# app/agents/event_pipeline.py

import os
import json
from typing import List, Dict, Any

from google import genai
from google.genai import types
from sqlalchemy import or_, func

from app.extensions import db
from app.models import User, Event
from app.recommendation.linucb import rank_events_with_linucb

# Gemini client used only for this event recommendation pipeline.
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _strip_json_markdown(raw: str) -> str:
    """
    Helper to strip Markdown code fences (``` or ```json) from model output.

    Many LLMs tend to wrap JSON in:
      ```json
      { ... }
      ```

    This function removes the first and last fence lines if present and
    returns the inner text, which should be valid JSON.
    """
    if not raw:
        return ""

    text = raw.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()

    # Drop the first line (``` or ```json)
    if lines:
        lines = lines[1:]

    # Drop the last line if it is a closing fence
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()


def extract_event_search_query(user_message: str) -> Dict[str, Any]:
    """
    Step 1: Use Gemini to convert a natural language message into a simple
    search query for events.

    Expected JSON output format:
    {
      "keywords": ["robotics", "ai"],
      "time_pref": "weekday_evening",
      "club_tags": ["academic_stem_tech"]
    }

    Semantics:
      - keywords: list of 1-5 important keywords for event search (lowercase strings)
      - time_pref: one of
          "any", "weekday_evening", "weekend", "morning", "afternoon", "evening"
      - club_tags: subset of the coarse tag vocabulary used in the app
          e.g. ["academic_stem_tech", "sports", "creative_arts", ...]
    """
    system_text = (
        "You are a STRICT JSON API that converts natural language requests about "
        "campus events into a structured search query.\n\n"
        "Your ONLY job is to return a SINGLE valid JSON object with the EXACT schema:\n"
        "{\n"
        '  "keywords": string[],   // 1-5 important keywords for event search (lowercase)\n'
        '  "time_pref": string,    // one of: "any", "weekday_evening", "weekend", "morning", "afternoon", "evening"\n'
        '  "club_tags": string[]   // subset of the tag vocabulary used in this app\n'
        "}\n\n"
        "Rules:\n"
        "- Output MUST be valid JSON. Do NOT include comments in the actual JSON.\n"
        "- Do NOT wrap the JSON in Markdown code fences.\n"
        '- Do NOT include any extra keys besides "keywords", "time_pref", "club_tags".\n'
        "- If you are not sure about the time preference, use \"any\".\n"
        "- Extract 1-5 meaningful keywords from the user message, in lowercase.\n"
        "- Use simple, short words for keywords, like [\"robotics\", \"ai\", \"cs\"]\n"
        "- If the user mentions weekday evenings, map that to \"weekday_evening\".\n"
        "- Respond with JSON ONLY. No explanations, no surrounding text.\n"
    )

    prompt = (
        f"{system_text}\n\n"
        "User message:\n"
        f"{user_message}\n\n"
        "JSON output:"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )
        ],
    )

    raw_text = response.text or ""
    # Strip possible ```json ... ``` wrappers
    raw_text = _strip_json_markdown(raw_text)

    try:
        query = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: naive keyword extraction from whitespace-separated tokens.
        print(
            "[EventPipeline] Failed to parse JSON in extract_event_search_query; "
            "falling back to naive keyword split."
        )
        query = {
            "keywords": [
                w.strip().lower()
                for w in user_message.split()
                if w.strip()
            ],
            "time_pref": "any",
            "club_tags": [],
        }

    # Ensure required keys exist with default values.
    query.setdefault("keywords", [])
    query.setdefault("time_pref", "any")
    query.setdefault("club_tags", [])

    print(f"[EventPipeline] Extracted search query: {query}")
    return query


def search_events_in_db(search_query: Dict[str, Any], limit: int = 5) -> List[Event]:
    """
    Step 2: Search the Event table using the extracted keywords and (optionally)
    time preferences.

    For now:
      - We search title and description with simple LIKE conditions.
      - We ignore club_tags because the Event model does not have a 'tags' column.
      - time_pref is kept as a placeholder for future filters (weekday/weekend/evening).
    """
    keywords: List[str] = [
        k.strip().lower()
        for k in search_query.get("keywords", [])
        if k and k.strip()
    ]
    time_pref: str = (search_query.get("time_pref") or "any").lower()

    query = Event.query

    # Keyword filters over title and description (OR across all fields and keywords).
    if keywords:
        conditions = []
        for kw in keywords:
            like = f"%{kw}%"
            conditions.append(func.lower(Event.title).like(like))
            conditions.append(func.lower(Event.description).like(like))
        query = query.filter(or_(*conditions))

    # Very simple time-based filter placeholder.
    # You can implement real weekday/weekend logic using Event.start_time here.
    if time_pref == "weekday_evening":
        # Example placeholder: keep all events for now.
        pass
    elif time_pref == "weekend":
        # Example placeholder: keep all events for now.
        pass

    events = (
        query.order_by(Event.start_time.asc())
        .limit(limit)
        .all()
    )

    print(f"[EventPipeline] DB search found {len(events)} event(s)")
    return events


def select_top_events_with_llm(
    user_message: str,
    candidates: List[Event],
    final_k: int = 3,
) -> List[Event]:
    """
    Step 3: Given up to `len(candidates) <= 5` events from the DB, ask Gemini
    to choose the `final_k` most relevant events for the user's request.

    The model must return JSON:
      {"selected_event_ids": [<id1>, <id2>, ...]}

    If anything goes wrong (parsing failure or no valid ids), we fall back
    to taking the first `final_k` candidates in DB order.
    """
    if len(candidates) <= final_k:
        # Nothing to filter; just return them as-is.
        print(
            "[EventPipeline] Number of candidates <= final_k; "
            "skipping LLM selection step."
        )
        return candidates

    events_payload = [
        {
            "id": ev.id,
            "title": ev.title,
            "description": (ev.description or "")[:200],
            "start_time": ev.start_time.isoformat() if ev.start_time else None,
            "location": ev.location,
        }
        for ev in candidates
    ]

    system_text = (
        "You are a STRICT JSON API that selects the best campus events for a student.\n\n"
        "Your ONLY job is to return a SINGLE valid JSON object with the EXACT schema:\n"
        "{\n"
        '  "selected_event_ids": [int, int, ...]  // up to K event ids, in order\n'
        "}\n\n"
        "Rules:\n"
        "- Use the user message and the candidate events to judge relevance.\n"
        "- Prefer events that match the requested topic (e.g. robotics, AI).\n"
        "- Prefer events whose time is compatible with the user's request (e.g. weekday evenings).\n"
        "- Always return between 1 and K event ids, where K is given in the prompt.\n"
        "- Event ids MUST be taken from the provided candidate list.\n"
        "- Output MUST be valid JSON. Do NOT wrap the JSON in Markdown code fences.\n"
        "- Do NOT include any extra keys or text outside the JSON.\n"
    )

    payload = {
        "user_message": user_message,
        "max_k": final_k,
        "candidates": events_payload,
    }

    prompt = (
        f"{system_text}\n\n"
        "INPUT (as JSON):\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "JSON output:"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )
        ],
    )

    raw_text = response.text or ""
    # Strip possible ```json ... ``` wrappers
    raw_text = _strip_json_markdown(raw_text)

    try:
        data = json.loads(raw_text)
        ids = data.get("selected_event_ids", [])
    except json.JSONDecodeError:
        print(
            "[EventPipeline] Failed to parse JSON in select_top_events_with_llm; "
            "falling back to first K candidates."
        )
        return candidates[:final_k]

    try:
        selected_ids = [int(i) for i in ids]
    except (TypeError, ValueError):
        print(
            "[EventPipeline] select_top_events_with_llm received non-integer ids; "
            "falling back to first K candidates."
        )
        return candidates[:final_k]

    id_to_event = {ev.id: ev for ev in candidates}
    selected_events: List[Event] = []

    for eid in selected_ids:
        if eid in id_to_event:
            selected_events.append(id_to_event[eid])
        if len(selected_events) >= final_k:
            break

    if not selected_events:
        print(
            "[EventPipeline] LLM selection produced no valid ids; "
            "falling back to first K candidates."
        )
        return candidates[:final_k]

    print(f"[EventPipeline] LLM selected event ids: {selected_ids}")
    return selected_events


def recommend_events_via_pipeline(
    user_id: int,
    user_message: str,
    max_candidates: int = 5,
    final_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Full pipeline for event recommendation:

      1) Use LLM to extract search keywords and time preferences
         from the user's natural language request.
      2) Query the Event table to get up to `max_candidates` events.
      3) Use LLM again to down-select those events to `final_k` candidates.
      4) Use the global LinUCB model to rank those `final_k` events
         according to the user's preference profile.
      5) Return a JSON-serializable list of events with LinUCB scores
         in descending order.

    If the Event table has no matching rows, an empty list is returned.
    """
    user = User.query.get(user_id)
    if user is None:
        print(f"[EventPipeline] No such user_id={user_id}")
        return []

    # Step 1: keyword extraction via LLM
    search_query = extract_event_search_query(user_message)

    # Step 2: DB search for up to `max_candidates` events
    candidates = search_events_in_db(search_query, limit=max_candidates)
    if not candidates:
        # No events found in the DB; return an empty list.
        return []

    # Step 3: LLM-based down-selection from up to 5 candidates to `final_k` events
    selected_events = select_top_events_with_llm(
        user_message=user_message,
        candidates=candidates,
        final_k=final_k,
    )

    # Step 4: Rank the selected events with LinUCB
    ranked_pairs = rank_events_with_linucb(user, selected_events)

    # Step 5: Format the results for JSON
    results: List[Dict[str, Any]] = []
    for ev, score in ranked_pairs:
        results.append(
            {
                "event_id": ev.id,
                "title": ev.title,
                "description": ev.description,
                "start_time": ev.start_time.isoformat() if ev.start_time else None,
                "location": ev.location,
                "linucb_score": float(score),
            }
        )

    print(
        "[EventPipeline] Final ranked events: "
        f"{[{'id': r['event_id'], 'score': r['linucb_score']} for r in results]}"
    )
    return results
