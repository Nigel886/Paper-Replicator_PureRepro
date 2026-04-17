from typing import List
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks 
from fastapi.openapi.utils import get_openapi
import os
import shutil
from core.engine import PaperReplicator
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Initialize App
app = FastAPI(title="PureRepro Paper Replicator V3-Final")

# Mount static files to serve frontend
# Ensure the 'static' directory exists in your root
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    """Route to serve the main frontend page."""
    return FileResponse('static/index.html')

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
    framework: str = Form("PyTorch")
):
    # 1. Setup workspace
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_paths = []
    # 2. Save incoming files
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_paths.append(file_path)
    
    # 3. Trigger Engine Analysis
    # The engine now returns structured Markdown with ## headers
    raw_response = replicator.analyze_paper_set(temp_paths, framework=framework)

    # 4. Schedule Cleanup
    background_tasks.add_task(cleanup_temp_files, temp_paths)

    return {
        "status": "success",
        "analysis": raw_response,
        "suggested_filename": output_name
    }

from pydantic import BaseModel
from typing import List, Optional

class ArxivRequest(BaseModel):
    arxiv_id: str
    framework: Optional[str] = "PyTorch"

@app.post("/replicate_arxiv")
async def replicate_arxiv(request: ArxivRequest):
    """
    Endpoint to trigger the full ArXiv replication flow.
    """
    from mcp_server import replicate_from_arxiv
    
    print(f"[API] Triggering ArXiv Replication for ID: {request.arxiv_id} with {request.framework}")
    result = replicate_from_arxiv(request.arxiv_id, framework=request.framework)
    
    return {
        "status": "success",
        "analysis": result
    }

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