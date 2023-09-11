from fastapi import FastAPI
from app.routes.file_ops import router as file_ops_router

app = FastAPI()

'''
Function that receives a 
'''
@app.get('/')
async def root():
    return 'Funciona!'


app.include_router(file_ops_router, prefix="/files", tags=["Files"])