import os
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, APIRouter, HTTPException
from azure.storage.blob import BlobServiceClient
from starlette.responses import JSONResponse
from app.Query import Query

router = APIRouter()
query = None
hierarchy = None

# TODO: Remove this and use an enviroment
storage_account_key = 'UFMBntGTy48V7R4MuJfNOhi3zEeSnsvjrQhUCmjT3/Kz+08B8J0B5ghzC5nKfqg/vmZd+djElT88+AStnj0nAA=='
storage_account_name = 'aiengineers'
connection_string = 'DefaultEndpointsProtocol=https;AccountName=aiengineers;AccountKey=UFMBntGTy48V7R4MuJfNOhi3zEeSnsvjrQhUCmjT3/Kz+08B8J0B5ghzC5nKfqg/vmZd+djElT88+AStnj0nAA==;EndpointSuffix=core.windows.net'
container_name = 'projects'


@router.get("/")
async def test():
    return "Testing"


@router.post("/upload-proj")
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
        original_proj_dir_path = temp_dir / "original"
        original_proj_dir_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(original_proj_dir_path)

        # Convert to txt
        convert_directory_to_txt(original_proj_dir_path, temp_dir)

        # Get project hierarchy
        global hierarchy
        hierarchy = get_project_hierarchy(temp_dir, max_files=15)

        # Upload project structure to azure storage service (recursive upload)
        project_id_container = str(uuid.uuid4())
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        recursive_project_upload(temp_dir, blob_service_client, project_id_container)

        # TODO: Start embeding processing routine

        return JSONResponse(content={
            "message": "Directory uploaded successfully",
            "project_id": project_id_container
        },
            status_code=200)
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


@router.get("/list-projects")
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


def get_project_hierarchy(project_directory, level=0, max_files=15):
    if not os.path.exists(project_directory):
        return "El directorio no existe"

    if not os.path.isdir(project_directory):
        return "La ruta proporcionada no es un directorio"

    resultado = ""

    print("Im here")

    for item in os.listdir(project_directory):
        item_ruta = os.path.join(project_directory, item)
        indent = "  " * level

        if os.path.isfile(item_ruta):
            resultado += f"{indent}- {item}\n"
        elif os.path.isdir(item_ruta):
            resultado += f"{indent}+ {item}/\n"
            if level < max_files:
                resultado += get_project_hierarchy(item_ruta, level=level + 1, max_files=max_files)

    return resultado


def convert_directory_to_txt(input_path, output_path):
    # Walk through the input directory
    for root, dirs, files in os.walk(input_path):
        # Create corresponding subdirectories in the output directory
        relative_path = os.path.relpath(root, input_path)
        output_subdir = os.path.join(output_path, relative_path)
        os.makedirs(output_subdir, exist_ok=True)

        # Convert and copy files
        for file in files:
            input_file_path = os.path.join(root, file)
            output_file_path = os.path.join(output_subdir, file + '.txt')  # Add .txt extension
            try:
                with open(input_file_path, 'r', encoding='utf-8') as input_file:
                    with open(output_file_path, 'w', encoding='utf-8') as output_file:
                        shutil.copyfileobj(input_file, output_file)
            except Exception as e:
                print(f"Error processing {input_file_path}: {str(e)}")


def print_file_structure(directory_path):
    for root, directories, files in os.walk(directory_path):
        # Print the current directory
        print(f"Directory: {root}")

        # Print all subdirectories in the current directory
        for directory in directories:
            print(f"  Subdirectory: {os.path.join(root, directory)}")

        # Print all files in the current directory
        for file in files:
            print(f"  File: {os.path.join(root, file)}")


@router.post("/ask/")
def ask_compass(project_name: str):
    global query
    if query is None:
        # download_blob(project_id)d
        temp_dir = Path("temp_project_directory")
        path = temp_dir / project_name
        hier = get_project_hierarchy(path)
        query = Query(directory=path, hierarchy=hier)
        query.make_db()

        question = "Could you describe what the project does?"
        answ = query.make_query(question)
        print(answ)
        print(answ['answer'])


def download_blob(project_id):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Create temp dir to store the uploaded zip file containing the directory
    proj_dir = Path("documents")
    proj_dir.mkdir(parents=True, exist_ok=True)

    blobs = container_client.list_blobs(name_starts_with="")

    for blob in blobs:
        curr_project_name = blob.name.split('/')[0]
        if curr_project_name == project_id:
            index = blob.name.find('/') + 1
            folder_name = blob.name[index:]
            proj_path = proj_dir / folder_name
            proj_path.mkdir(parents=True, exist_ok=True)

            blob_client = container_client.get_blob_client(blob.name)
            with open(proj_path, "wb") as local_file:
                local_file.write(blob_client.download_blob().readall())
