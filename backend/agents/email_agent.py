import os
from typing import Any, Dict

from agno.agent import Agent
from agno.tools.email import EmailTools

# =============================================================================
#  Environment-driven configuration
# =============================================================================

RECEIVER_EMAIL = os.getenv("EMAIL_RECEIVER", "")
SENDER_EMAIL = os.getenv("EMAIL_SENDER", "")
SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "Finance Chatbot Agent")
SENDER_PASSKEY = os.getenv("EMAIL_SENDER_PASSKEY", "")

if not SENDER_EMAIL:
    print("[EmailAgent] WARNING: EMAIL_SENDER is not set in the environment.")
if not SENDER_PASSKEY:
    print("[EmailAgent] WARNING: EMAIL_SENDER_PASSKEY is not set in the environment.")

# =============================================================================
#  Email tool + Agent (NO enable_auto_execute here)
# =============================================================================

email_tools = EmailTools(
    receiver_email=RECEIVER_EMAIL or SENDER_EMAIL,  # fall back to sender if needed
    sender_email=SENDER_EMAIL,
    sender_name=SENDER_NAME,
    sender_passkey=SENDER_PASSKEY,
)

email_agent = Agent(
    # name and instructions are optional but helpful
    name="email_agent",
    instructions=(
        "You are an assistant that drafts and sends concise, polite emails. "
        "When asked to send an email, you should use the EmailTools tool."
    ),
    tools=[email_tools],  # ✅ ONLY supported argument here; no enable_auto_execute
)


# =============================================================================
#  Helper used by Flask endpoint
# =============================================================================

def send_email_via_agent(subject: str, body: str, to: str | None = None) -> Dict[str, Any]:
    """
    Ask the Agno email agent to send an email.

    Parameters
    ----------
    subject : str
        Email subject.
    body : str
        Main body text.
    to : str | None
        Optional override for receiver email.

    Returns
    -------
    dict
        Minimal status + raw agent output (for logging / debugging).
    """
    # Override receiver if needed
    if to:
        email_tools.receiver_email = to

    prompt = (
        "Compose and send the following email.\n\n"
        f"Subject: {subject}\n\n"
        f"Body:\n{body}\n\n"
        "Use the email tool to actually send the message."
    )

    # Depending on Agno version this is typically `.run()` or `.chat()`.
    # If you see an AttributeError, we can swap to `.chat()`.
    result = email_agent.run(prompt)

    return {
        "status": "sent",
        "receiver": email_tools.receiver_email,
        "subject": subject,
        "raw_result": str(result),
    }
