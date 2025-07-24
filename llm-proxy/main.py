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
    print(payload["user_prompt"], payload["model_name"])

    auth_header = request.headers.get("Authorization")
    print("Received Authorization header from frontend:", auth_header)
    headers = {
        "Content-Type": "application/json",
        "X-Function-Name": request.headers.get("x-function-name", "frontend-proxy"),
        "X-Platform-ID": request.headers.get("x-platform-id", "123"),
        # "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjQxNDkwODJGOTFCOUY0RDNERjkwN0YzNDA4NDhDRENBNTNFOTAzOUIiLCJ4NXQiOiJRVWtJTDVHNTlOUGZrSDgwQ0VqTnlsUHBBNXMiLCJ0eXAiOiJhdCtqd3QifQ.eyJzdWIiOiJjbGllbnQtY3JlZGVudGlhbCIsIm5hbWUiOiJNMk0iLCJyb2xlIjoiU3VwZXJBZG1pbmlzdHJhdG9yIiwib2lfcHJzdCI6ImNsaWVudC1jcmVkZW50aWFsIiwiY2xpZW50X2lkIjoiY2xpZW50LWNyZWRlbnRpYWwiLCJvaV90a25faWQiOiIwOGRkY2E1MC1mNTQwLTQ3ZWYtOGIxYS1iOGFjNDExYjRlNDkiLCJzY29wZSI6ImludGVybmFsIiwianRpIjoiZWNiMjQ2ZTYtY2M5ZS00NzhmLTgyMTYtZmQwYjk0MThiYTk2IiwiZXhwIjoxNzUzMzIzOTIxLCJpc3MiOiJodHRwczovL2Rldi50ZWxsaWdlbnRiaXouY29tL29hdXRoMmFwaS8iLCJpYXQiOjE3NTMzMjAzMjF9.tqbnRue_y_HrwXux2yy5hqJ5kiiqOxCRuX28ui13NUP8zWG1MGQOBiksavsjgkRYG9hqrGjf7pBi1-4KKqKSyQr-Uan-Ji3qu5ASUmZ_ddIZ7Rz0GvxfNzV72Q6i7sXki0WgqPPADt2D-SXGCNfTjogMTwMXFU8VUD3hzb7n3qfEamObbwzZlBbuO8do1JDMmJy1_XbcCfsWEmGNp8dp3G_bO05OfuAB64KGsM2vtrDXv08cJZ_onqFMRU6CYc-3seyFsmlm84QPUkW6OXhJH6b_hb9N1uInME6JcsZWFQHtYAQKcAPwKdyIeaTcW8Vovx7QYfuQR_iG8rwIYOdz3Q"
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
            print("LLM Response:", r)
            return r.json()
    except Exception as e:
        print("❌ ERROR inside /invoke:", str(e))
        return {"error": str(e)}