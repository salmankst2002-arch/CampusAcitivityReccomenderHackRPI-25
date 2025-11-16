# app/agents/swipe_tool.py

from typing import Dict, Any

from app.extensions import db
from app.models import User, Club, Swipe
from app.recommendation.linucb import update_global_linucb_from_swipe


def record_swipe_with_linucb(user_id: int, club_id: int, liked: bool) -> Dict[str, Any]:
    """
    Record a swipe in the database and update the global LinUCB model.

    This function is used by both:
      - the REST /api/swipe endpoint
      - the Gemini function tool `submit_swipe`
    """
    user = User.query.get(user_id)
    club = Club.query.get(club_id)

    if user is None or club is None:
        return {
            "ok": False,
            "error": "User or Club not found",
            "user_exists": user is not None,
            "club_exists": club is not None,
        }

    # Create a new swipe record (swipe history).
    swipe = Swipe(user_id=user_id, club_id=club_id, liked=liked)
    db.session.add(swipe)
    db.session.commit()

    # Update LinUCB and save its state.
    update_global_linucb_from_swipe(user, club, liked)

    print(
        f"[SwipeTool] Swipe stored and LinUCB updated: "
        f"user_id={user_id}, club_id={club_id}, liked={liked}, swipe_id={swipe.id}"
    )

    return {
        "ok": True,
        "swipe_id": swipe.id,
        "user_id": user_id,
        "club_id": club_id,
        "liked": liked,
        "club_name": club.name,
    }
