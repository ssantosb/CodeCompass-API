from fastapi import FastAPI

app = FastAPI()

'''
Function that receives a 
'''
@app.get('/')
async def root():
    return 'Funciona!'