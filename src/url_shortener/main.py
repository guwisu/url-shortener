import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="url-shortener",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "OK"}

if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        reload=True
    )