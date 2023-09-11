import os
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, APIRouter, HTTPException
from azure.storage.blob import BlobServiceClient
from starlette.responses import JSONResponse

router = APIRouter()

# TODO: Remove this and use an enviroment
storage_account_key = 'UFMBntGTy48V7R4MuJfNOhi3zEeSnsvjrQhUCmjT3/Kz+08B8J0B5ghzC5nKfqg/vmZd+djElT88+AStnj0nAA=='
storage_account_name = 'aiengineers'
connection_string = 'DefaultEndpointsProtocol=https;AccountName=aiengineers;AccountKey=UFMBntGTy48V7R4MuJfNOhi3zEeSnsvjrQhUCmjT3/Kz+08B8J0B5ghzC5nKfqg/vmZd+djElT88+AStnj0nAA==;EndpointSuffix=core.windows.net'
container_name = 'projects'


@router.get("/")
async def test():
    return "Testing"


@router.post("/upload")
async def upload_project_directory(directory: UploadFile):
    try:
        # Create temp dir to store the uploaded zip file containing the directory
        temp_dir = Path("temp_project_directory")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file to the temp dir
        zip_file_path = temp_dir / directory.filename
        with zip_file_path.open("wb") as buffer:
            shutil.copyfileobj(directory.file, buffer)

        # Extract directory content
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Upload project structure to azure storage service (recursive upload)
        project_id_container = str(uuid.uuid4())
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        recursive_project_upload(temp_dir, blob_service_client, project_id_container)

        #TODO: Start embeding processing routine

        # Clean up: Remove the uploaded ZIP file
        os.remove(zip_file_path)

        return JSONResponse(content={"message": "Directory uploaded successfully"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"messge": "Error uploading directory " + str(e)}, status_code=500)


def recursive_project_upload(project_directory_path, blob_service_client, project_id, base_dir=""):
    for item in project_directory_path.iterdir():
        if item.is_dir():
            # Recursively upload subdirectories
            new_base_directory = os.path.join(base_dir, item.name)
            recursive_project_upload(item, blob_service_client, project_id, new_base_directory)
        elif item.is_file():
            # Upload files to Azure Blob Storage while preserving directory structure
            blob_name = ""
            if base_dir != "":
                blob_name = f"{project_id}/{base_dir}/{item.relative_to(project_directory_path)}"
            else:
                blob_name = f"{project_id}/{item.relative_to(project_directory_path)}"
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=str(blob_name))
            with open(item, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)


@router.get("/projects")
def show_all_projects():
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Set the base directory path you want to list folders under
    base_directory = ""  # Replace with the desired path

    # List blobs with the specified prefix
    blobs = container_client.list_blobs(name_starts_with=base_directory)

    # Extract and print unique folder names
    folder_set = set()
    for blob in blobs:
        # Extract the folder name
        folder_name = blob.name.split('/')[0] + "/" + blob.name.split('/')[1]
        second_level = blob.name.split('/')[1]

        if "." not in second_level:
            folder_set.add(folder_name)

    # Print the unique folder names
    for folder in folder_set:
        print(folder)