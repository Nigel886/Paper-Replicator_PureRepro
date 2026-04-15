from fastapi import FastAPI, UploadFile, File, Form
import os
import shutil
from core.engine import PaperReplicator
from dotenv import load_dotenv

app = FastAPI(title="AI Paper Replicator API")

# Initialize environment variables and core engine
load_dotenv()
replicator = PaperReplicator(os.getenv("GEMINI_API_KEY"))

@app.post("/replicate")
async def replicate_paper(
    # Use File(...) to trigger the upload button in Swagger UI
    file: UploadFile = File(..., description="Upload paper image"),
    output_name: str = Form("model.py")
):
    # 1. Initialize temporary directory
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 2. Save the uploaded file to local storage
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Call the core engine (analyze_paper_set expects a list of paths)
    raw_response = replicator.analyze_paper_set([file_path])

    return {
        "status": "success",
        "analysis": raw_response,
        "suggested_filename": output_name
    }

if __name__ == "__main__":
    import uvicorn
    # Using 127.0.0.1 to avoid potential Windows firewall issues with 0.0.0.0
    uvicorn.run(app, host="127.0.0.1", port=8000)