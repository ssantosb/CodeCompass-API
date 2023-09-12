from fastapi import FastAPI
from app.routes.router import router as router

app = FastAPI()

'''
Function that receives a 
'''
@app.get('/')
async def root():
    return 'Funciona!'


app.include_router(router, prefix="/compass", tags=["Files"])