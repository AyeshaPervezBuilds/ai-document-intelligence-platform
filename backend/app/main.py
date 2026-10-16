from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, documents, query

app = FastAPI(title="Document Intelligence Platform")

# CORS — allow the Next.js frontend (running on a different origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; lock down in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health")
def health_check():
    return {"status": "ok"} 