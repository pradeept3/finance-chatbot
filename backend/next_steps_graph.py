"""
backend/next_steps_graph.py

Simple rule-based "next steps" suggester for the finance chatbot.
No LangChain / LangGraph dependencies – fast and robust.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional


def _normalize(text: str) -> str:
    """Lowercase + strip helper."""
    return (text or "").lower().strip()


def _build_generic_suggestions(
    user_q: str,
    answer: str,
    key_points: List[str],
) -> List[Dict[str, Any]]:
    """
    Return 3–5 generic but useful next-step suggestions.

    Each suggestion has:
      - label: button text
      - category: followup | clarification | deep_dive | action
      - reason: why this is a good next step
    """
    suggestions: List[Dict[str, Any]] = []

    suggestions.append(
        {
            "label": "Ask for a simpler explanation",
            "category": "clarification",
            "reason": (
                "Use this if any part of the answer feels complex and you want a "
                "more intuitive or beginner-friendly explanation."
            ),
        }
    )

    if user_q:
        suggestions.append(
            {
                "label": "Apply this to my situation",
                "category": "deep_dive",
                "reason": (
                    "Ask the assistant to adapt the answer to your specific context, "
                    "project, or dataset."
                ),
            }
        )

    if key_points:
        suggestions.append(
            {
                "label": "Explain each key point with an example",
                "category": "deep_dive",
                "reason": (
                    "Walk through concrete examples for the key takeaways so they are "
                    "easier to understand and remember."
                ),
            }
        )

    suggestions.append(
        {
            "label": "List risks or limitations",
            "category": "followup",
            "reason": (
                "Use this to uncover caveats, edge cases, or limitations related to "
                "the answer."
            ),
        }
    )

    suggestions.append(
        {
            "label": "Suggest related topics to explore next",
            "category": "action",
            "reason": (
                "Ask for a short list of related topics you could investigate to go "
                "deeper in this area."
            ),
        }
    )

    # Deduplicate by label and limit to 5
    unique: Dict[str, Dict[str, Any]] = {}
    for s in suggestions:
        if s["label"] not in unique:
            unique[s["label"]] = s

    return list(unique.values())[:5]


def run_next_steps_graph(
    user_question: str,
    answer_text: str,
    key_points: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Public entry point used by Flask /api/next-steps.

    Returns:
        {
          "suggestions": [ { "label", "category", "reason" }, ... ],
          "error": None | str
        }
    """
    try:
        user_q_norm = _normalize(user_question)
        answer_norm = _normalize(answer_text)
        kp_list = key_points or []

        suggestions = _build_generic_suggestions(user_q_norm, answer_norm, kp_list)

        return {
            "suggestions": suggestions,
            "error": None,
        }
    except Exception as e:
        return {
            "suggestions": [],
            "error": str(e),
        }
