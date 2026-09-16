import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.conversation.features import FEATURE_REGISTRY

STAGE_CROP = "AWAITING_CROP"
STAGE_ON_FIELD = "AWAITING_ON_FIELD"
STAGE_LOCATION = "AWAITING_LOCATION"
STAGE_FEATURE_CHOICE = "AWAITING_FEATURE_CHOICE"
STAGE_CONTINUE = "AWAITING_CONTINUE"
STAGE_DONE = "DONE"


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    stage: str = STAGE_CROP
    crop: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    location_variant: Optional[str] = None
    menu_offset: int = 0
    last_result: Optional[dict] = None
    feature_order: list = field(default_factory=lambda: [f["id"] for f in FEATURE_REGISTRY])

    def bump_feature_to_end(self, feature_id):
        self.feature_order.remove(feature_id)
        self.feature_order.append(feature_id)


_SESSIONS = {}


def create_session():
    session = Session()
    _SESSIONS[session.id] = session
    return session


def get_session(session_id):
    return _SESSIONS.get(session_id)
