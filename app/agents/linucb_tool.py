# app/agents/linucb_tool.py

from typing import List, Dict, Any

from app.models import User, Club
from app.recommendation.linucb import (
    rank_clubs_with_linucb,
)


def recommend_clubs_with_linucb(user_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Recommend clubs for a given user using the global LinUCB agent
    dedicated to clubs.

    This function:
      1. Loads the User from the database.
      2. Fetches candidate clubs (currently: all clubs).
      3. Calls `rank_clubs_with_linucb(user, candidate_clubs, top_k)`.
      4. Converts the result into a JSON-serializable list of dicts.

    The returned data is designed to be easy for the LLM (Gemini) to consume.
    """
    print(f"[LinUCB] recommend_clubs_with_linucb called with user_id={user_id}, top_k={top_k}")

    # 1) Load the user
    user = User.query.get(user_id)
    if user is None:
        print(f"[LinUCB] No user found with id={user_id}")
        return []

    # 2) Fetch candidate clubs (all clubs for now)
    candidate_clubs: List[Club] = Club.query.all()
    print(f"[LinUCB] Number of candidate clubs fetched from DB: {len(candidate_clubs)}")

    if not candidate_clubs:
        print("[LinUCB] No candidate clubs available")
        return []

    # 3) Use the club-level LinUCB ranking helper
    ranked = rank_clubs_with_linucb(user, candidate_clubs, top_k=top_k)
    print(f"[LinUCB] rank_clubs_with_linucb returned {len(ranked)} items")

    # 4) Convert to JSON-serializable structure
    results: List[Dict[str, Any]] = []
    for club, score in ranked:
        # Club.tags is stored as a comma-separated string.
        tags_list: List[str] = []
        if club.tags:
            tags_list = [t.strip() for t in club.tags.split(",") if t.strip()]

        results.append(
            {
                "club_id": club.id,
                "name": club.name,
                "tags": tags_list,
                "score": float(score),
            }
        )

    # Print a compact preview of the results for debugging
    preview = [
        {"club_id": r["club_id"], "name": r["name"], "score": r["score"]}
        for r in results
    ]
    print(f"[LinUCB] Recommendation result preview: {preview}")

    return results
