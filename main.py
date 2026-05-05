"""TelcoConnect API — Telecom Carrier Data"""
import os, logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from data_pipeline import CARRIERS, search_carriers, get_carrier, identify_carrier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telcoconnect")

app = FastAPI(title="TelcoConnect API", version="1.0.0", description="200+ global telecom carriers with phone prefixes, coverage maps, and carrier identification")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

API_KEYS = {os.environ.get("INTERNAL_API_KEY", "demo-key")}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    key = request.headers.get("x-api-key", "")
    if key not in API_KEYS:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
    return await call_next(request)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "TelcoConnect", "carriers": len(CARRIERS)}

@app.get("/v1/carriers")
async def list_carriers():
    return {"carriers": [{"id": c["id"], "name": c["name"], "country": c["country"]} for c in CARRIERS]}

@app.get("/v1/carriers/search")
async def search(q: str = Query(""), country: Optional[str] = Query(None), limit: int = Query(20, le=100)):
    results = search_carriers(q, country, limit)
    return {"total": len(results), "results": results}

@app.get("/v1/carriers/{carrier_id}")
async def carrier_detail(carrier_id: str):
    c = get_carrier(carrier_id)
    if not c: raise HTTPException(404, f"Carrier {carrier_id} not found")
    return c

@app.get("/v1/identify")
async def identify(phone: str = Query(..., description="Phone number with country code")):
    result = identify_carrier(phone)
    if "error" in result: raise HTTPException(404, result["error"])
    return result

@app.get("/v1/billing")
async def billing(account_id: str = Query(""), period: str = Query("current")):
    return {"account_id": account_id, "period": period, "status": "mock", "message": "Billing integration requires carrier API keys"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
