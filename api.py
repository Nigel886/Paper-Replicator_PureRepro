import os
import shutil
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks 
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from core.engine import PaperReplicator
from dotenv import load_dotenv
from utils.progress_manager import ProgressTracker, progress_tracker

# Initialize App
app = FastAPI(title="PureRepro Paper Replicator V3-Final")
# progress_tracker is already instantiated in ProgressTracker module as a global instance
# but if you need to access the class or the instance:
# progress_tracker = ProgressTracker() # This would create a new instance, we should use the shared one
from utils.progress_manager import progress_tracker 

# Mount static files to serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    """Route to serve the main frontend page."""
    return FileResponse('static/index.html')

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    SSE endpoint to push progress updates to the frontend.
    """
    async def event_generator():
        queue = progress_tracker.get_queue(task_id)
        while True:
            try:
                # Wait for progress message
                data = await queue.get()
                import json
                yield f"data: {json.dumps(data)}\n\n"
                
                # Check for completion
                if data.get("message") == "COMPLETED" or data.get("message") == "FAILED":
                    break
            except asyncio.CancelledError:
                break
        # Cleanup
        progress_tracker.remove_task(task_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

load_dotenv()
replicator = PaperReplicator(os.getenv("GEMINI_API_KEY"))

def cleanup_temp_files(file_paths: List[str]):
    """Background task to wipe temporary images after processing."""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[Cleanup] Removed: {path}")
        except Exception as e:
            print(f"[Cleanup Error] {path}: {e}")

@app.post("/replicate")
async def replicate_paper(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Upload multiple paper screenshots"),
    output_name: str = Form("model.py"),
    framework: str = Form("PyTorch"),
    task_id: str = Form(None)
):
    if not task_id:
        task_id = str(uuid.uuid4())
    
    progress_tracker.get_queue(task_id)

    async def run_upload_replication():
        temp_paths = []
        try:
            progress_tracker.update_progress(task_id, "Initializing workspace...", 1, 5)
            # 1. Setup workspace
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 2. Save incoming files
            progress_tracker.update_progress(task_id, f"Saving {len(files)} uploaded files...", 2, 5)
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                temp_paths.append(file_path)
            
            # 3. Trigger Engine Analysis
            progress_tracker.update_progress(task_id, "Analyzing paper images with Gemini...", 3, 5)
            raw_response = await asyncio.to_thread(
                replicator.analyze_paper_set, 
                temp_paths, 
                framework=framework
            )

            task_results[task_id] = raw_response
            progress_tracker.update_progress(task_id, "COMPLETED", 5, 5)
        except Exception as e:
            task_results[task_id] = f"Error: {str(e)}"
            progress_tracker.update_progress(task_id, f"FAILED: {str(e)}", 5, 5)
        finally:
            # 5. Cleanup
            cleanup_temp_files(temp_paths)

    background_tasks.add_task(run_upload_replication)

    return {
        "status": "pending",
        "task_id": task_id
    }

from pydantic import BaseModel

class ArxivRequest(BaseModel):
    arxiv_id: str
    framework: Optional[str] = "PyTorch"
    task_id: Optional[str] = None

# 全局存储任务结果，防止连接断开后丢失
task_results = {}

@app.post("/replicate_arxiv")
async def replicate_arxiv(request: ArxivRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the full ArXiv replication flow.
    """
    from mcp_server import replicate_from_arxiv
    
    task_id = request.task_id or str(uuid.uuid4())
    progress_tracker.get_queue(task_id)
    
    async def run_replication():
        try:
            progress_tracker.update_progress(task_id, f"Retrieving ArXiv ID: {request.arxiv_id}", 1, 10)
            print(f"[API] Background task started for ID: {request.arxiv_id}")
            
            # 在独立线程运行，不阻塞事件循环
            result = await asyncio.to_thread(
                replicate_from_arxiv, 
                request.arxiv_id, 
                framework=request.framework, 
                task_id=task_id
            )
            
            task_results[task_id] = result
            progress_tracker.update_progress(task_id, "COMPLETED", 10, 10)
        except Exception as e:
            error_msg = f"Task failed: {str(e)}"
            task_results[task_id] = error_msg
            progress_tracker.update_progress(task_id, f"FAILED: {str(e)}", 10, 10)

    # 使用 BackgroundTasks 运行，这样即使 HTTP 连接断开，任务也会继续
    background_tasks.add_task(run_replication)
    
    return {
        "status": "pending",
        "message": "Replication started in background",
        "task_id": task_id
    }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """获取任务最终生成的报告内容"""
    if task_id in task_results:
        return {"status": "success", "analysis": task_results[task_id]}
    return {"status": "processing"}

@app.post("/stop")
async def stop_engine():
    """紧急停止所有正在运行的 AI 引擎任务"""
    progress_tracker.stop_all()
    print("[API] SHUTDOWN signal received. Stopping all background engines...")
    return {"status": "success", "message": "Shutdown signal sent to all engines."}

@app.post("/reset")
async def reset_engine():
    """重置停机标志，允许开始新任务"""
    progress_tracker.reset_shutdown()
    return {"status": "success", "message": "Engine reset and ready for new tasks."}

def custom_openapi():
    """Injects 'format: binary' into OpenAPI schema to fix Swagger UI file buttons."""
    if app.openapi_schema:
        return app.openapi_schema
    
    schema = get_openapi(
        title=app.title,
        version="3.0.0",
        description="Internationalized API for Paper Replication",
        routes=app.routes,
    )
    
    try:
        # Targeting the multipart body schema
        props = schema["components"]["schemas"]["Body_replicate_paper_replicate_post"]["properties"]
        if "files" in props:
            props["files"]["items"] = {"type": "string", "format": "binary"}
    except KeyError:
        pass
        
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# http://127.0.0.1:8000
if __name__ == "__main__":
    import uvicorn
    # Ready for action!
    uvicorn.run(app, host="127.0.0.1", port=8000)