import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.analysis.agronomic import analyze_agronomic_recommendations
from app.analysis.irrigation import analyze_irrigation
from app.analysis.plant_health import analyze_plant_health
from app.config import FIELD_RADIUS_M
from app.conversation.flow import FlowError, start_session, submit
from app.data_sources.crops import ALL_CROPS

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


class ReplyRequest(BaseModel):
    value: Any


@app.post("/chat/start")
def chat_start():
    return start_session()


@app.post("/chat/{session_id}/reply")
def chat_reply(session_id: str, req: ReplyRequest):
    try:
        return submit(session_id, req.value)
    except FlowError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/crops")
def crops():
    return {"crops": ALL_CROPS}


@app.get("/config")
def config():
    return {"field_radius_m": FIELD_RADIUS_M}


@app.get("/field-locator")
def field_locator():
    return FileResponse(os.path.join(os.path.dirname(__file__), "field-locator.html"))
