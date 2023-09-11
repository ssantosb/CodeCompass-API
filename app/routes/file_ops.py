import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, UploadFile
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def test():
    return "Testing"


@router.post("/upload")
async def upload_directory(directory: UploadFile):
    try:
        # Create temp dir to store the uploaded zip file containing the directory
        temp_dir = Path("temp_project_directory")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file to the temp dir
        zip_file_path = temp_dir / directory.filename
        with zip_file_path.open("wb") as buffer:
            shutil.copyfileobj(directory.file, buffer)

        # Extract directory content
        target_directory = Path("target_directory")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(target_directory)

        # Upload project structure to azure storage service

        return JSONResponse(content={"message": "Directory uploaded successfully"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"messge": "Error uploading directory " + str(e)}, status_code=500)
