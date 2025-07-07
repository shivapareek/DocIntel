from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

from routers import upload, qa, challenge

app = FastAPI(title="GenAI Document Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("store", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])
app.include_router(challenge.router, prefix="/api", tags=["challenge"])


@app.get("/")
async def root():
    return {"message": "GenAI Document Assistant API is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    