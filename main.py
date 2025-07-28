from http_server import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Launching FastAPI Schedule Helper Server from main.py...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
