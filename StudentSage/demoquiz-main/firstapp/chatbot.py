from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from llm import *

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str

@app.post("/chat/")
async def chat(message: Message):
    # return {"response": greeting()}
    response =await chat_with_me(message.text)
    return {"response": response}


if __name__=='__main__':
    uvicorn.run(app,host='localhost',port=8001)