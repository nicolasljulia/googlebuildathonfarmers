from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.analysis.agronomic import analyze_agronomic_recommendations
from app.analysis.irrigation import analyze_irrigation
from app.analysis.plant_health import analyze_plant_health

app = FastAPI(title="OpenFarm Messaging — Data Layer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PointRequest(BaseModel):
    lat: float
    lon: float
    crop_type: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze/plant-health")
def plant_health(req: PointRequest):
    return analyze_plant_health(req.lat, req.lon, req.crop_type)


@app.post("/analyze/irrigation")
def irrigation(req: PointRequest):
    return analyze_irrigation(req.lat, req.lon, req.crop_type)


@app.post("/analyze/agronomic-recommendations")
def agronomic_recommendations(req: PointRequest):
    return analyze_agronomic_recommendations(req.lat, req.lon, req.crop_type)
