from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/invoke")
async def proxy_invoke(request: Request):
    
    print("✋ invoke hit")

    payload = await request.json()
    print(payload["user_prompt"], payload["model_name"], payload["temperature"])

    auth_header = request.headers.get("Authorization")
    headers = {
        "Content-Type": "application/json",
        "X-Function-Name": request.headers.get("x-function-name", "frontend-proxy"),
        "X-Platform-ID": request.headers.get("x-platform-id", "123"),
    }

    if auth_header:
        headers["Authorization"] = auth_header

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://dev-nlp.telligentbiz.com/llm/sandbox/invoke",
                json=payload,
                headers=headers
            )
            return r.json()
    except Exception as e:
        print("❌ ERROR inside /invoke:", str(e))
        return {"error": str(e)}
