from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse 
import uvicorn, json
import asyncio
from asyncio import sleep


app = FastAPI(title="mce-api")

@app.get("/")  # Home Page
def home():
    return {"ok": True, "service": "mce-api"}  # JSON (JavaScript Object Notation) response

@app.get("/healthz")  # K8s-style health endpoint
def health():
    return {"status": "healthy"}

@app.get("/favicon.ico")
def favicon():
    return {}

# 👉 HERE: Define your async generator function that will yield SSE-formatted strings.
#    - Each yield should look like: f"data: {json.dumps({'token': token})}\n\n"
#    - Add a final yield with event: done.
#    - Consider including heartbeats (": keep-alive\n\n") if connection may stay idle.
async def sse_token_generator():
    for token in range(10):
        yield f"data: {json.dumps({'token': token})}\n\n"
        await asyncio.sleep(1)

    yield "event: done\ndata: {}\n\n"


async def main():
    # loop over async generator with async for loop
    async for item in sse_token_generator():
        print(item)

@app.get("/get-tokens")
async def root():
    return StreamingResponse(sse_token_generator(), media_type="text/event-stream")


# 👉 HERE: Add a new route, e.g., @app.get("/chat")
#    - Return a StreamingResponse using the generator above.
#    - Be sure to set headers:
#        Content-Type: text/event-stream
#        Cache-Control: no-cache
#        Connection: keep-alive
#    - Optionally add X-Accel-Buffering: no if behind Nginx.

def run():
    uvicorn.run("mce_api.main:app", host="0.0.0.0", port=8000, reload=True)
