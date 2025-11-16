# app/api/routes.py
from flask import Blueprint, jsonify, request, current_app
from flask_cors import CORS

from ..extensions import db
from ..models import User, Club, Swipe, Event
from ..agents.gemini_agent import chat_with_linucb  # NEW: import the Gemini chat helper
from ..recommendation.linucb import update_global_linucb_from_swipe  # 追加
from ..agents.swipe_tool import record_swipe_with_linucb  # NEW import

api_bp = Blueprint("api", __name__)
CORS(app=api_bp) # allow requests of all origin

@api_bp.route("/ping")
def ping():
    return jsonify({"message": "pong"})


@api_bp.route("/recommend", methods=["GET"])
def recommend_clubs():
    """
    Recommend a list of clubs for a given user.

    Primary behavior:
      - Return clubs that the user has NOT swiped yet, ordered by id desc.
    Fallback:
      - If the user has already swiped all clubs, fall back to returning
        all clubs (up to `limit`) so that the UI always has something to show.
    """
    user_id = request.args.get("user_id", type=int)
    limit = request.args.get("limit", default=10, type=int)

    if user_id is None:
        return jsonify({"error": "user_id query parameter is required"}), 400

    # Ensure the user exists
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"User with id {user_id} does not exist"}), 404

    # Subquery: all club_ids that this user has already swiped
    swiped_club_ids_subq = (
        db.session.query(Swipe.club_id)
        .filter(Swipe.user_id == user_id)
        .subquery()
    )

    # First, try: clubs that are not in the swiped list
    clubs_query = (
        Club.query
        .filter(~Club.id.in_(swiped_club_ids_subq))
        .order_by(Club.id.desc())
        .limit(limit)
    )
    clubs = clubs_query.all()

    # Fallback: if user has swiped every club, still return some clubs
    if not clubs:
        current_app.logger.info(
            "[API/recommend] No unswiped clubs for user_id=%s, "
            "falling back to ALL clubs.",
            user_id,
        )
        clubs = (
            Club.query
            .order_by(Club.id.desc())
            .limit(limit)
            .all()
        )

    result = []
    for club in clubs:
        result.append(
            {
                "club_id": club.id,
                "name": club.name,
                "description": club.description,
                "tags": club.tags,
                "meeting_time": club.meeting_time,
                "location": club.location,
            }
        )

    return jsonify(result)

@api_bp.route("/matches", methods=["GET"])
def get_user_matches():
    """
    Return clubs that the user has liked, along with their events.

    Response format:
    [
      {
        "club_id": 1,
        "club_name": "...",
        "club_tags": ["academic_stem_tech"],
        "events": [
          {
            "event_id": 1,
            "title": "...",
            "description": "...",
            "start_time": "...",
            "location": "...",
          },
          ...
        ],
      },
      ...
    ]
    """
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"error": "user_id query parameter is required"}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"User with id {user_id} does not exist"}), 404

    # 1) Find liked swipes for this user
    liked_swipes = Swipe.query.filter_by(user_id=user_id, liked=True).all()
    club_ids = [s.club_id for s in liked_swipes]

    if not club_ids:
        return jsonify([])

    # 2) Load clubs
    clubs = Club.query.filter(Club.id.in_(club_ids)).all()
    clubs_by_id = {c.id: c for c in clubs}

    # 3) Load events for those clubs (future events only if you want)
    events = (
        Event.query
        .filter(Event.club_id.in_(club_ids))
        .order_by(Event.start_time.asc())
        .all()
    )

    events_by_club = {}
    for ev in events:
        events_by_club.setdefault(ev.club_id, []).append(ev)

    # 4) Format response
    results = []
    for cid in club_ids:
        club = clubs_by_id.get(cid)
        if club is None:
            continue

        tags_list = []
        if club.tags:
            tags_list = [t.strip() for t in club.tags.split(",") if t.strip()]

        ev_list = []
        for ev in events_by_club.get(cid, []):
            ev_list.append(
                {
                    "event_id": ev.id,
                    "title": ev.title,
                    "description": ev.description,
                    "start_time": ev.start_time.isoformat() if ev.start_time else None,
                    "location": ev.location,
                }
            )

        results.append(
            {
                "club_id": club.id,
                "club_name": club.name,
                "club_tags": tags_list,
                "events": ev_list,
            }
        )

    return jsonify(results)


@api_bp.route("/swipe", methods=["POST"])
def swipe_club():
    """
    Save a swipe action from a user for a given club.
    Expected JSON body:
    {
        "user_id": 1,
        "club_id": 3,
        "liked": true
    }
    """
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    club_id = data.get("club_id")
    liked = data.get("liked")

    # Basic validation
    if user_id is None or club_id is None or liked is None:
        return (
            jsonify(
                {
                    "error": "user_id, club_id, and liked are required fields in JSON body"
                }
            ),
            400,
        )

    # Ensure types are correct
    try:
        user_id = int(user_id)
        club_id = int(club_id)
    except (TypeError, ValueError):
        return jsonify({"error": "user_id and club_id must be integers"}), 400

    if not isinstance(liked, bool):
        # Allow 1/0 as well
        if liked in (0, 1):
            liked = bool(liked)
        else:
            return (
                jsonify({"error": "liked must be a boolean (true/false) or 0/1"}),
                400,
            )

    # Use the shared helper to handle DB + LinUCB update.
    result = record_swipe_with_linucb(user_id=user_id, club_id=club_id, liked=liked)
    if not result.get("ok"):
        return jsonify(result), 404

    current_app.logger.info(
        "Swipe recorded via /api/swipe: user_id=%s club_id=%s liked=%s",
        user_id,
        club_id,
        liked,
    )

    return jsonify({"status": "ok", "swipe_id": result["swipe_id"]})


@api_bp.route("/chat", methods=["POST"])
def chat():
    """
    Chat endpoint that connects the frontend to the Gemini + LinUCB agent.

    Expected JSON body:
    {
        "user_id": 1,
        "message": "I want to find a robotics club that meets on weekday evenings.",
        "history": [
            {"role": "user", "text": "Previous user message"},
            {"role": "assistant", "text": "Previous assistant reply"}
        ]
    }

    Returns:
    {
        "reply": "<assistant message text>"
    }
    """
    data = request.get_json(silent=True) or {}

    user_id_raw = data.get("user_id")
    message = data.get("message", "")
    history = data.get("history", [])

    # Basic validation
    if user_id_raw is None or message.strip() == "":
        return jsonify({"error": "user_id and message are required"}), 400

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "user_id must be an integer"}), 400

    # Call the Gemini-based chat helper, which will:
    #   1. Decide whether to call the LinUCB tool.
    #   2. Fetch recommendations via LinUCB if needed.
    #   3. Produce a natural-language reply in English or Japanese.
    reply_text = chat_with_linucb(
        user_id=user_id,
        user_message=message,
        history=history,
    )

    return jsonify({"reply": reply_text})

from ..agents.event_pipeline import recommend_events_via_pipeline  # NEW import
@api_bp.route("/events/chat_recommend", methods=["POST"])
def chat_recommend_events():
    """
    Recommend events for a user in a conversational context.

    Expected JSON body:
    {
        "user_id": 1,
        "message": "I want a robotics or AI-related event on weekday evenings."
    }

    Returns:
    [
        {
            "event_id": ...,
            "title": "...",
            "description": "...",
            "tags": "...",
            "start_time": "...",
            "location": "...",
            "linucb_score": 3.14
        },
        ...
    ]
    """
    data = request.get_json(silent=True) or {}
    user_id_raw = data.get("user_id")
    message = data.get("message", "")

    if user_id_raw is None or message.strip() == "":
        return jsonify({"error": "user_id and message are required"}), 400

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "user_id must be an integer"}), 400

    results = recommend_events_via_pipeline(
        user_id=user_id,
        user_message=message,
        max_candidates=5,
        final_k=3,
    )

    return jsonify(results)