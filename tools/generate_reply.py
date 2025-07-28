from protocol import EmailReply
from typing import List, Optional
from datetime import datetime
import pytz

def format_time_human_readable(iso_time: str, target_timezone: str = "UTC") -> str:
    """
    Convert ISO time to human-readable format
    
    Args:
        iso_time: ISO format time string
        target_timezone: Target timezone for display
        
    Returns:
        Human-readable time string
    """
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        
        # Convert to target timezone if specified
        if target_timezone != "UTC":
            target_tz = pytz.timezone(target_timezone)
            dt = dt.astimezone(target_tz)
        
        # Format as human-readable
        return dt.strftime("%A, %B %d at %I:%M %p %Z")
    except Exception as e:
        print(f"Error formatting time '{iso_time}': {e}")
        return iso_time

def extract_name_from_email(email: str) -> str:
    """
    Extract a name from an email address
    
    Args:
        email: Email address
        
    Returns:
        Extracted name or generic greeting
    """
    if not email or "@" not in email:
        return "there"
    
    try:
        username = email.split("@")[0]
        # Handle common email patterns
        name_parts = username.replace(".", " ").replace("_", " ").replace("-", " ")
        words = name_parts.split()
        
        # Capitalize each word
        capitalized_words = [word.capitalize() for word in words if word.isalpha()]
        
        if capitalized_words:
            return " ".join(capitalized_words)
        else:
            return "there"
    except Exception:
        return "there"

def generate_reply_based_on_intent(
    intent: str,
    candidate_name: str,
    proposed_times: List[str],
    timezone: str
) -> str:
    """
    Generate reply message based on detected intent
    
    Args:
        intent: Detected intent from email parsing
        candidate_name: Name of the candidate
        proposed_times: Available meeting times
        timezone: Target timezone for formatting
        
    Returns:
        Generated message text
    """
    if intent == "cancel":
        return f"""Hi {candidate_name},

Thank you for letting us know. We understand that schedules can change.

If you'd like to reschedule for a future date, please let us know your availability and we'll be happy to accommodate.

Best regards,
Schedule Helper"""

    elif intent == "reschedule":
        if proposed_times:
            time_lines = "\n".join([f"• {format_time_human_readable(t, timezone)}" for t in proposed_times])
            return f"""Hi {candidate_name},

No problem! We can definitely reschedule.

Would any of these alternative times work for you?

{time_lines}

Please let us know which option works best.

Best regards,
Schedule Helper"""
        else:
            return f"""Hi {candidate_name},

We'd be happy to reschedule. Could you please share your preferred times and we'll check our availability?

Best regards,
Schedule Helper"""

    elif intent == "confirm":
        return f"""Hi {candidate_name},

Perfect! We have you confirmed for the meeting.

We look forward to speaking with you then. You'll receive a calendar invitation shortly with all the details.

Best regards,
Schedule Helper"""

    elif intent == "available" or intent == "available_no_times":
        if proposed_times:
            time_lines = "\n".join([f"• {format_time_human_readable(t, timezone)}" for t in proposed_times])
            return f"""Hi {candidate_name},

Thank you for sharing your availability!

We'd like to schedule the meeting for one of these times:

{time_lines}

Please confirm which time works best for you, and we'll send over a calendar invitation.

Best regards,
Schedule Helper"""
        else:
            return f"""Hi {candidate_name},

Thank you for your message! To help us find the best time for our meeting, could you please share a few specific times that work for you?

For example:
• Day of the week and time (e.g., "Tuesday at 2pm")
• Multiple options if possible
• Your timezone

We'll do our best to accommodate your schedule.

Best regards,
Schedule Helper"""

    else:  # unknown or other intents
        return f"""Hi {candidate_name},

Thank you for your message. To help us schedule our meeting, could you please let us know:

• Your preferred days and times
• Your timezone
• Any dates that definitely won't work

We'll get back to you promptly with available options.

Best regards,
Schedule Helper"""

def generate_reply(
    candidate_name: Optional[str] = None,
    proposed_times: Optional[List[str]] = None,
    timezone: str = "UTC",
    from_email: str = "",
    intent: str = "available"
) -> EmailReply:
    """
    Generates a human-like reply message proposing meeting times.

    Args:
        candidate_name (Optional[str]): Name of the candidate if known.
        proposed_times (Optional[List[str]]): ISO-format time strings.
        timezone (str): Target timezone for formatting.
        from_email (str): Email address for name extraction if candidate_name not provided.
        intent (str): Detected intent from email parsing.

    Returns:
        EmailReply: A structured reply message.
    """
    
    # Determine candidate name
    if candidate_name:
        name = candidate_name
    elif from_email:
        name = extract_name_from_email(from_email)
    else:
        name = "there"
    
    # Ensure proposed_times is a list
    if proposed_times is None:
        proposed_times = []
    
    # Generate message based on intent and available times
    message = generate_reply_based_on_intent(
        intent=intent,
        candidate_name=name,
        proposed_times=proposed_times,
        timezone=timezone
    )
    
    return EmailReply(
        type="email_reply",
        message=message,
        language="en",
        proposed_time=proposed_times[0] if proposed_times else None
    )