from app.data_sources.crops import ALL_CROPS, crop_slug, is_known_crop
from app.conversation.features import FEATURES_BY_ID
from app.conversation.session import (
    STAGE_CONTINUE,
    STAGE_CROP,
    STAGE_DONE,
    STAGE_FEATURE_CHOICE,
    STAGE_LOCATION,
    STAGE_ON_FIELD,
    create_session,
    get_session,
)

MENU_PAGE_SIZE = 2

YES_VALUES = {"yes", "y", "true", "1"}
NO_VALUES = {"no", "n", "false", "0"}


class FlowError(Exception):
    pass


def _crop_prompt(session):
    return {
        "session_id": session.id,
        "stage": session.stage,
        "message": "Which crop are you growing?",
        "input_type": "select",
        "options": [{"id": c, "label": c} for c in ALL_CROPS],
    }


def _on_field_prompt(session):
    return {
        "session_id": session.id,
        "stage": session.stage,
        "message": "Are you on your field right now?",
        "input_type": "yes_no",
        "options": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}],
    }


def _location_prompt(session):
    if session.location_variant == "gps":
        message = "Please share your current location."
    else:
        message = "Drop a pin on the map, or type your coordinates as \"lat, lon\"."
    return {
        "session_id": session.id,
        "stage": session.stage,
        "message": message,
        "input_type": "location",
    }


def _feature_menu_prompt(session):
    ordered = [FEATURES_BY_ID[fid] for fid in session.feature_order]
    page = ordered[session.menu_offset: session.menu_offset + MENU_PAGE_SIZE]
    remaining = len(ordered) - (session.menu_offset + MENU_PAGE_SIZE)
    options = [{"id": f["id"], "label": f["label"]} for f in page]
    if remaining > 0:
        options.append({"id": "more", "label": "Something else"})
    return {
        "session_id": session.id,
        "stage": session.stage,
        "message": "What would you like to check?",
        "input_type": "select",
        "options": options,
    }


def _done_prompt(session, message):
    return {
        "session_id": session.id,
        "stage": session.stage,
        "message": message,
        "done": True,
    }


def start_session():
    session = create_session()
    return _crop_prompt(session)


def _parse_yes_no(value):
    v = str(value).strip().lower()
    if v in YES_VALUES:
        return True
    if v in NO_VALUES:
        return False
    raise FlowError("Please answer yes or no.")


def _parse_location(value):
    if isinstance(value, dict):
        lat, lon = value.get("lat"), value.get("lon")
    elif isinstance(value, str) and "," in value:
        parts = value.split(",")
        lat, lon = parts[0].strip(), parts[1].strip()
    else:
        raise FlowError("Please share a location as {lat, lon} or \"lat, lon\".")
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise FlowError("Latitude/longitude must be numbers.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise FlowError("Latitude must be -90..90 and longitude -180..180.")
    return lat, lon


def submit(session_id, value):
    session = get_session(session_id)
    if session is None:
        raise FlowError("Session not found — start a new one.")

    if session.stage == STAGE_CROP:
        if not is_known_crop(str(value)):
            return _crop_prompt(session)
        matched = next(c for c in ALL_CROPS if crop_slug(c) == crop_slug(str(value)))
        session.crop = matched
        session.stage = STAGE_ON_FIELD
        return _on_field_prompt(session)

    if session.stage == STAGE_ON_FIELD:
        on_field = _parse_yes_no(value)
        session.location_variant = "gps" if on_field else "manual"
        session.stage = STAGE_LOCATION
        return _location_prompt(session)

    if session.stage == STAGE_LOCATION:
        lat, lon = _parse_location(value)
        session.lat, session.lon = lat, lon
        session.stage = STAGE_FEATURE_CHOICE
        session.menu_offset = 0
        return _feature_menu_prompt(session)

    if session.stage == STAGE_FEATURE_CHOICE:
        choice = str(value)
        if choice == "more":
            session.menu_offset += MENU_PAGE_SIZE
            return _feature_menu_prompt(session)

        feature = FEATURES_BY_ID.get(choice)
        if feature is None:
            return _feature_menu_prompt(session)

        result = feature["run"](session.lat, session.lon, session.crop)
        session.last_result = result
        session.bump_feature_to_end(choice)
        session.stage = STAGE_CONTINUE

        reply_text = feature["format"](result)
        return {
            "session_id": session.id,
            "stage": session.stage,
            "message": f"{reply_text}\n\nWould you like to check anything else?",
            "input_type": "yes_no",
            "options": [{"id": "yes", "label": "Yes"}, {"id": "no", "label": "No"}],
            "result": result,
        }

    if session.stage == STAGE_CONTINUE:
        again = _parse_yes_no(value)
        if not again:
            session.stage = STAGE_DONE
            return _done_prompt(session, "Thanks! Reach out anytime you need another check.")
        session.stage = STAGE_FEATURE_CHOICE
        session.menu_offset = 0
        return _feature_menu_prompt(session)

    if session.stage == STAGE_DONE:
        return _done_prompt(session, "This session has ended — start a new one to run another check.")

    raise FlowError(f"Unknown stage: {session.stage}")
