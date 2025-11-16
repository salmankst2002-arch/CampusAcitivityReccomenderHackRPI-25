# app/agents/gemini_agent.py

import os
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types

from app.agents.linucb_tool import recommend_clubs_with_linucb

# app/agents/gemini_agent.py

from collections import defaultdict

# In-memory conversation history store:
#   key: user_id (int)
#   value: list of {"role": "user" | "assistant", "text": "..."}
conversation_history: dict[int, list[dict[str, str]]] = defaultdict(list)

# Create a Gemini client using the API key from environment variables.
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# 1) Function declaration for Gemini: "recommend_clubs"
recommend_clubs_declaration: Dict[str, Any] = {
    "name": "recommend_clubs",
    "description": (
        "Recommend campus clubs for the current student using the LinUCB bandit model. "
        "Use this tool when the user wants suggestions for clubs or events."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": (
                    "Internal user id for the current student. "
                    "The backend will override this with the actual id."
                ),
            },
            "top_k": {
                "type": "integer",
                "description": "How many clubs to recommend (1–20).",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
            },
        },
        "required": ["user_id"],
    },
}

# app/agents/gemini_agent.py

from app.agents.swipe_tool import record_swipe_with_linucb


submit_swipe_declaration: Dict[str, Any] = {
    "name": "submit_swipe",
    "description": (
        "Record a swipe (like or dislike) for a specific club on behalf of the user "
        "and immediately update the LinUCB bandit model. "
        "Use this tool whenever the user explicitly says they like or dislike a club "
        "that you have mentioned by name."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": (
                    "Internal user id for the current student. "
                    "The backend will override this with the actual id."
                ),
            },
            "club_id": {
                "type": "integer",
                "description": "The numeric id of the club the user is reacting to.",
            },
            "liked": {
                "type": "boolean",
                "description": "True if the user likes the club, False otherwise.",
            },
        },
        "required": ["user_id", "club_id", "liked"],
    },
}


# Wrap the declaration in a Tool object.
tool = types.Tool(
    function_declarations=[
        recommend_clubs_declaration,
        submit_swipe_declaration,
    ]
)

config = types.GenerateContentConfig(
    tools=[tool],
    system_instruction=(
        "You are a campus activity assistant for university students.\n"
        "- You speak in English by default.\n"
        "- When the user wants club recommendations, you SHOULD call the "
        "`recommend_clubs` tool to get personalized candidates.\n"
        "- When the user explicitly likes or dislikes a specific club (including in "
        "natural language, such as 'I like the AI & Robotics Lab Club' or "
        "'I am not interested in the Campus Jazz Band'), you MUST call the "
        "`submit_swipe` tool for that club with liked=true or liked=false.\n"
        "- Prefer to show a small number of clubs at a time (e.g., 3–5), and then "
        "ask the user for their reactions, updating their preferences via "
        "submit_swipe before suggesting more clubs.\n"
    ),
    temperature=0.4,
)



def _build_contents(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> List[types.Content]:
    """
    Convert our own conversation history structure into Gemini Contents.

    history is expected to be a list of dicts:
      {"role": "user" | "assistant", "text": "..."}
    """
    contents: List[types.Content] = []

    # Past conversation turns (if any).
    if history:
        for turn in history:
            role = "user" if turn.get("role") == "user" else "assistant"
            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        # NOTE: Use direct Part(text=...) instead of Part.from_text(...)
                        types.Part(text=turn.get("text", "")),
                    ],
                )
            )

    # Current user message.
    contents.append(
        types.Content(
            role="user",
            parts=[
                # NOTE: Same here: direct constructor
                types.Part(text=user_message),
            ],
        )
    )

    return contents


# app/agents/gemini_agent.py

def chat_with_linucb(
    user_id: int,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    High-level entry point for the chat endpoint.

    1. Build conversation contents from either:
         - explicit history passed from the frontend, or
         - the server-side in-memory history for this user.
    2. Send the user message and function declarations to Gemini.
    3. If Gemini calls the `recommend_clubs` tool, run LinUCB in Python.
    4. Send the tool result back to Gemini for a natural-language reply.
    5. Append the turn to the in-memory history and return the reply text.
    """
    print(f"[Gemini] chat_with_linucb called for user_id={user_id}")
    print(f"[Gemini] User message: {user_message}")

    # Decide which history to use:
    #  - If the caller provided a history, trust it and overwrite the server-side store.
    #  - Otherwise, fall back to the server-side history for this user.
    if history is not None and len(history) > 0:
        conversation_history[user_id] = history
        effective_history = history
    else:
        effective_history = conversation_history.get(user_id, [])

    contents = _build_contents(user_message=user_message, history=effective_history)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=config,
    )

    tool_call = None
    for part in response.candidates[0].content.parts:
        if getattr(part, "function_call", None):
            tool_call = part.function_call
            break

    if tool_call is None:
        print("[Gemini] No function call detected, returning plain text response")
        reply_text = response.text
        conversation_history[user_id].append({"role": "user", "text": user_message})
        conversation_history[user_id].append({"role": "assistant", "text": reply_text})
        return reply_text

    print(f"[Gemini] Function call detected: name={tool_call.name}, args={dict(tool_call.args)}")

    # --- Branch on tool name ---
    if tool_call.name == "recommend_clubs":
        args = dict(tool_call.args)
        top_k = int(args.get("top_k", 5))
        print(f"[Gemini] Calling recommend_clubs_with_linucb(user_id={user_id}, top_k={top_k})")
        clubs = recommend_clubs_with_linucb(user_id=user_id, top_k=top_k)

        function_response_payload = {"clubs": clubs}

    elif tool_call.name == "submit_swipe":
        args = dict(tool_call.args)
        # Ignore args["user_id"] and trust our backend user_id.
        club_id_raw = args.get("club_id")
        liked_raw = args.get("liked")

        try:
            club_id = int(club_id_raw)
        except (TypeError, ValueError):
            print(f"[Gemini] submit_swipe tool called with invalid club_id={club_id_raw}")
            reply_text = "I could not record your preference because the club id was invalid."
            conversation_history[user_id].append({"role": "user", "text": user_message})
            conversation_history[user_id].append({"role": "assistant", "text": reply_text})
            return reply_text

        liked = bool(liked_raw)
        print(f"[Gemini] Calling record_swipe_with_linucb(user_id={user_id}, club_id={club_id}, liked={liked})")
        swipe_result = record_swipe_with_linucb(user_id=user_id, club_id=club_id, liked=liked)

        function_response_payload = {"swipe": swipe_result}

    else:
        print(f"[Gemini] Unknown tool name: {tool_call.name}")
        reply_text = "Sorry, I am not configured to use this tool yet."
        conversation_history[user_id].append({"role": "user", "text": user_message})
        conversation_history[user_id].append({"role": "assistant", "text": reply_text})
        return reply_text

    # --- Send tool result back to Gemini for natural-language reply ---
    function_response_part = types.Part.from_function_response(
        name=tool_call.name,
        response=function_response_payload,
    )

    final_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[function_response_part],
            )
        ],
        config=config,
    )

    reply_text = final_response.text
    print("[Gemini] Final response generated")

    # Update server-side history with this turn.
    conversation_history[user_id].append({"role": "user", "text": user_message})
    conversation_history[user_id].append({"role": "assistant", "text": reply_text})

    return reply_text

