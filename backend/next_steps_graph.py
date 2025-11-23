# backend/next_steps_graph.py
"""
Lightweight 'next steps' helper with **no LangGraph / LangChain / LLM calls**.

This keeps the same public function:
    run_next_steps_graph(user_question, answer_text, key_points=None)

and returns:
    {
        "suggestions": [ { "label": ..., "category": ..., "reason": ... }, ... ],
        "error": None or str
    }

So any existing Flask route that imports and calls run_next_steps_graph
will continue to work, but will now be **instant** and cannot time out
due to an LLM call.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional


def _basic_suggestions(
    user_question: str,
    answer_text: str,
    key_points: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Very simple heuristic next-step generator.

    No external API calls. You can tweak these rules as you like.
    """
    key_points = key_points or []
    suggestions: List[Dict[str, Any]] = []

    # 1️⃣ Generic follow-up question
    suggestions.append(
        {
            "label": "Provide follow-up question",
            "category": "followup",
            "reason": "You can get deeper insights by asking a follow-up question about any part of the answer.",
        }
    )

    # 2️⃣ If the answer is long, offer a shorter summary
    if len(answer_text) > 700 or len(key_points) > 4:
        suggestions.append(
            {
                "label": "Request a shorter summary",
                "category": "clarification",
                "reason": "The answer is fairly detailed. A shorter summary may help you review the key ideas quickly.",
            }
        )

    # 3️⃣ If there are key points, offer a deep-dive
    if key_points:
        suggestions.append(
            {
                "label": "Deep dive into one key point",
                "category": "deep_dive",
                "reason": "You can focus on one of the key topics to understand it in greater detail.",
            }
        )

    # 4️⃣ If the question mentions 'requirements', 'plan', or 'steps', offer an action-oriented suggestion
    q_lower = (user_question or "").lower()
    if any(word in q_lower for word in ["requirement", "requirements", "plan", "steps"]):
        suggestions.append(
            {
                "label": "Create an action plan",
                "category": "action",
                "reason": "You might want to convert these details into a concrete checklist or plan.",
            }
        )

    # 5️⃣ Fallback: ensure at least one suggestion
    if not suggestions:
        suggestions.append(
            {
                "label": "Ask for more clarification",
                "category": "clarification",
                "reason": "If anything in the answer is unclear, you can request further clarification.",
            }
        )

    # Limit to a maximum of 5 suggestions
    return suggestions[:5]


def run_next_steps_graph(
    user_question: str,
    answer_text: str,
    key_points: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Public function used by Flask.

    Previously this called a LangGraph + LLM pipeline. Now it is a fast,
    local function that returns heuristic suggestions and **never** calls
    Ollama or Gemini.

    Example return:
        {
            "suggestions": [
                {"label": "...", "category": "followup", "reason": "..."},
                ...
            ],
            "error": None
        }
    """
    try:
        suggestions = _basic_suggestions(
            user_question=user_question,
            answer_text=answer_text,
            key_points=key_points or [],
        )
        return {
            "suggestions": suggestions,
            "error": None,
        }
    except Exception as e:
        # Extremely unlikely, but we keep the shape for safety
        return {
            "suggestions": [],
            "error": str(e),
        }
