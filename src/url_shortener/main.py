import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from url_shortener.api.routers.health import router as health_router
from url_shortener.api.v1 import redirect_router, v1_router

app = FastAPI(
    title="url-shortener",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

app.include_router(health_router)
app.include_router(v1_router, prefix="/api")
app.include_router(redirect_router)

if __name__ == "__main__":
    uvicorn.run(app="url_shortener.main:app", reload=True)
