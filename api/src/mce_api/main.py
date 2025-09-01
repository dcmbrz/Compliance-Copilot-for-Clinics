from fastapi import FastAPI
import uvicorn

app = FastAPI(title="mce-api")

@app.get("/") # Home Page
def home():
    return {"ok": True, "service": "mce-api"} # JSON (JavaScript Object Notation) response

@app.get("/healthz") # K8s-style health endpoint
def health():
    return {"status": "healthy"}

@app.get("/favicon.ico")
def favicon():
    return {}

def run():
    uvicorn.run("mce_api.main:app", host="0.0.0.0", port=8000, reload=True)

