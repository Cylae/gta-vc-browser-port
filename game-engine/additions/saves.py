import os
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()

SAVES_DIR = "saves"
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

def sanitize_token(token: str) -> str:
    """Sanitize token to prevent path traversal."""
    # Only allow alphanumeric characters, hyphens, and underscores
    clean_token = re.sub(r'[^a-zA-Z0-9_-]', '', token)
    if not clean_token:
        clean_token = "default"
    return clean_token

@router.get("/token/get")
async def get_token(id: str):
    # Always return success for any token
    clean_id = sanitize_token(id)
    return {"token": clean_id, "premium": True, "email": "local@user"}

@router.post("/saves/upload")
async def upload_save(
    token: str = Form(...),
    fileName: str = Form(...),
    file: UploadFile = File(...)
):
    clean_token = sanitize_token(token)
    safe_filename = os.path.basename(fileName)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    save_path = os.path.join(SAVES_DIR, f"{clean_token}_{safe_filename}")
    
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"success": True}

@router.get("/saves/download/{token}/{fileName}")
async def download_save(token: str, fileName: str):
    clean_token = sanitize_token(token)
    safe_filename = os.path.basename(fileName)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    save_path = os.path.join(SAVES_DIR, f"{clean_token}_{safe_filename}")
    
    if not os.path.exists(save_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
        
    return FileResponse(save_path)
