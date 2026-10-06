from fastapi import FastAPI

app = FastAPI(title="Document Intelligence Platform API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
    