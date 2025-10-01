from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Reuse the embedded telemetry from the existing module to avoid duplication
try:
    # When running as a package (preferred)
    from .latency import TELEMETRY_DATA
except Exception:
    try:
        # Absolute import fallback
        from api.latency import TELEMETRY_DATA  # type: ignore
    except Exception:
        # Local module fallback
        from latency import TELEMETRY_DATA  # type: ignore

app = FastAPI()

# Enable permissive CORS for POST (and preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


def calculate_percentile(values, percentile):
    """Calculate percentile without numpy (inclusive linear interpolation)."""
    if not values:
        return 0.0
    data = sorted(values)
    n = len(data)
    if n == 1:
        return float(data[0])
    rank = (percentile / 100.0) * (n - 1)
    lower_index = int(rank)
    if rank.is_integer():
        return float(data[lower_index])
    upper_index = lower_index + 1
    fraction = rank - lower_index
    return float(data[lower_index] + fraction * (data[upper_index] - data[lower_index]))


@app.post("/")
async def compute_metrics(request: Request):
    payload = await request.json()
    regions = payload.get("regions", [])
    threshold_ms = float(payload.get("threshold_ms", 0))

    response = {"regions": []}

    for region in regions:
        region_rows = [row for row in TELEMETRY_DATA if row.get("region") == region]
        if not region_rows:
            # Skip unknown regions (alternatively could include with zeros)
            continue

        latencies = [float(row["latency_ms"]) for row in region_rows]
        uptimes = [float(row["uptime_pct"]) for row in region_rows]

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = calculate_percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        breaches = sum(1 for v in latencies if v > threshold_ms)

        response["regions"].append({
            "region": region,
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches)
        })

    return response


@app.get("/")
async def root_info():
    return {
        "message": "Latency Analytics API",
        "usage": {
            "POST /": {
                "body": {"regions": ["apac", "emea", "amer"], "threshold_ms": 200}
            },
            "GET /health": "returns {status: 'ok'}"
        }
    }


@app.options("/")
async def options_root():
    # Explicitly answer preflight in addition to CORS middleware
    return JSONResponse(
        content={},
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok"}

