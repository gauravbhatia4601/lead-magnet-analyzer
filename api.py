from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
import os
import time
from main import analyze_full_site, plot_results

API_KEY = os.environ.get("API_KEY", "secret")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

app = FastAPI()


def verify_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return key


@app.post("/analyze")
def analyze(url: str, key: str = Depends(verify_key)):
    total_score, breakdown, pages_scanned = analyze_full_site(url)
    os.makedirs("results", exist_ok=True)
    file_name = f"analysis_{int(time.time())}.png"
    file_path = os.path.join("results", file_name)
    plot_results(
        breakdown, total_score, pages_scanned, url, output_file=file_path, show=False
    )
    return {
        "total_score": total_score,
        "pages_scanned": pages_scanned,
        "score_breakdown": breakdown,
        "result_file": file_name,
    }


@app.get("/files/{file_name}")
def get_file(file_name: str, key: str = Depends(verify_key)):
    file_path = os.path.join("results", file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/png", filename=file_name)
