from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.openapi.utils import get_openapi
import os
import shutil
from core.engine import PaperReplicator
from dotenv import load_dotenv

# Initialize FastAPI app with a version-specific title to force UI refresh
app = FastAPI(title="Lumina Paper Replicator V3-TEST")

load_dotenv()
# Initialize the replication engine with your Gemini API Key
replicator = PaperReplicator(os.getenv("GEMINI_API_KEY"))

@app.post("/replicate")
async def replicate_paper(
    # List[UploadFile] allows multiple file uploads
    files: List[UploadFile] = File(..., description="Select multiple images"),
    output_name: str = Form("model.py")
):
    # 1. Ensure temporary directory exists
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_paths = []
    # 2. Save all uploaded files to the temp directory
    for file in files:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        temp_paths.append(file_path)
    
    # 3. Process the files through the core abstraction engine
    raw_response = replicator.analyze_paper_set(temp_paths)

    return {
        "status": "success",
        "analysis": raw_response,
        "suggested_filename": output_name
    }

# ==================== The "Magic Fix": Custom OpenAPI Schema ====================
def custom_openapi():
    """
    Override the default OpenAPI schema generation.
    Forces 'format: binary' for file uploads to fix Swagger UI display issues.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate the base schema using FastAPI's utility
    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="Standardized API for paper replication with multi-image support",
        routes=app.routes,
    )
    
    # Deep dive into the schema to force Swagger to render 'Choose File' buttons
    try:
        # Targeting the auto-generated Pydantic model for the request body
        properties = openapi_schema["components"]["schemas"]["Body_replicate_paper_replicate_post"]["properties"]
        if "files" in properties:
            # Replace the modern 'contentMediaType' with the classic 'format: binary'
            # This ensures maximum compatibility with all browsers and Swagger versions
            properties["files"]["items"] = {
                "type": "string",
                "format": "binary"
            }
    except KeyError:
        # Gracefully skip if the schema structure differs
        pass
        
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Inject the custom schema generator into the app
app.openapi = custom_openapi
# ===============================================================================

# http://127.0.0.1:8000/docs
if __name__ == "__main__":
    import uvicorn
    # Use 127.0.0.1 to avoid Windows-specific networking issues with 0.0.0.0
    uvicorn.run(app, host="127.0.0.1", port=8000)