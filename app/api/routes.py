# app/api/routes.py
from flask import Blueprint, jsonify, request, current_app

from ..extensions import db
from ..models import User, Club, Swipe

api_bp = Blueprint("api", __name__)


@api_bp.route("/ping")
def ping():
    return jsonify({"message": "pong"})


@api_bp.route("/recommend", methods=["GET"])
def recommend_clubs():
    """
    Recommend a list of clubs for a given user.
    For now: return clubs that the user has not swiped yet (random order).
    """
    user_id = request.args.get("user_id", type=int)
    limit = request.args.get("limit", default=10, type=int)

    if user_id is None:
        return (
            jsonify({"error": "user_id query parameter is required"}),
            400,
        )

    # Ensure the user exists (optional but helpful)
    user = User.query.get(user_id)
    if user is None:
        return (
            jsonify({"error": f"User with id {user_id} does not exist"}),
            404,
        )

    # Subquery: all club_ids that this user has already swiped
    swiped_club_ids_subq = (
        db.session.query(Swipe.club_id)
        .filter(Swipe.user_id == user_id)
        .subquery()
    )

    # Query clubs that are not in the swiped list
    # For now, order by id descending (or random if you want).
    clubs_query = (
        Club.query
        .filter(~Club.id.in_(swiped_club_ids_subq))
        .order_by(Club.id.desc())
        .limit(limit)
    )

    clubs = clubs_query.all()

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

    # Ensure types are correct (convert liked to bool)
    try:
        user_id = int(user_id)
        club_id = int(club_id)
    except (TypeError, ValueError):
        return (
            jsonify({"error": "user_id and club_id must be integers"}),
            400,
        )

    if not isinstance(liked, bool):
        # Allow 1/0 as well
        if liked in (0, 1):
            liked = bool(liked)
        else:
            return (
                jsonify({"error": "liked must be a boolean (true/false) or 0/1"}),
                400,
            )

    user = User.query.get(user_id)
    club = Club.query.get(club_id)

    if user is None or club is None:
        return (
            jsonify(
                {
                    "error": "User or Club not found",
                    "user_exists": user is not None,
                    "club_exists": club is not None,
                }
            ),
            404,
        )

    # Option 1: allow multiple swipes (history)
    swipe = Swipe(user_id=user_id, club_id=club_id, liked=liked)
    db.session.add(swipe)
    db.session.commit()

    # TODO: if liked and user has Google Calendar connected,
    #       call a helper to create an event in Google Calendar.

    current_app.logger.info(
        "Swipe recorded: user_id=%s club_id=%s liked=%s",
        user_id,
        club_id,
        liked,
    )

    return jsonify({"status": "ok", "swipe_id": swipe.id})
