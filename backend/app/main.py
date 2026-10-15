from fastapi import FastAPI

from app.routers import auth, documents, query

app = FastAPI(title="Document Intelligence Platform")

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health")
def health_check():
    return {"status": "ok"} 