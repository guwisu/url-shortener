import uvicorn

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "OK"}

if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        reload=True
    )