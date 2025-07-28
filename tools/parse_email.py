from protocol import ParsedAvailability
import re
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

def convert_natural_to_iso(natural_time: str, base_timezone: str = "UTC") -> Optional[str]:
    """Convert natural language time to proper ISO format"""
    try:
        # Get current date as reference
        if base_timezone == "UTC":
            now = datetime.now(pytz.UTC)
        else:
            tz = pytz.timezone(base_timezone)
            now = datetime.now(tz)
        
        # Day patterns
        if "tomorrow" in natural_time.lower():
            target_date = now + timedelta(days=1)
        elif "today" in natural_time.lower():
            target_date = now
        else:
            # Handle weekday names
            weekdays = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            for day_name, day_num in weekdays.items():
                if day_name in natural_time.lower():
                    days_ahead = day_num - now.weekday()
                    if days_ahead <= 0:  # Target day has passed this week
                        days_ahead += 7
                    target_date = now + timedelta(days=days_ahead)
                    break
            else:
                # If no specific day found, assume next week
                target_date = now + timedelta(days=7)
        
        # Time patterns
        time_match = re.search(r'(\d{1,2})(:\d{2})?\s*(am|pm)', natural_time.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)[1:]) if time_match.group(2) else 0
            am_pm = time_match.group(3)
            
            # Convert to 24-hour format
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
                
            # Create the datetime in the specified timezone
            result_dt = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Convert to UTC and return with Z suffix (proper ISO format)
            if base_timezone != "UTC":
                result_dt = result_dt.astimezone(pytz.UTC)
            
            return result_dt.isoformat().replace('+00:00', 'Z')
            
    except Exception as e:
        print(f"Error converting '{natural_time}': {e}")
        return None

def enhanced_extract_times(text: str, timezone: str = "UTC") -> List[str]:
    """
    Enhanced time extraction that returns ISO format times
    
    Args:
        text: Email body text to parse
        timezone: Base timezone for conversion
        
    Returns:
        List of ISO format time strings
    """
    # Comprehensive patterns for time extraction
    patterns = [
        # Day + time patterns
        r"(tomorrow|today)\s+at\s+\d{1,2}(:\d{2})?\s*(am|pm)",
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+\d{1,2}(:\d{2})?\s*(am|pm)",
        r"\d{1,2}(:\d{2})?\s*(am|pm)\s+on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        
        # Date + time patterns
        r"\d{1,2}/\d{1,2}(/\d{4})?\s+at\s+\d{1,2}(:\d{2})?\s*(am|pm)",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?\s+at\s+\d{1,2}(:\d{2})?\s*(am|pm)",
        
        # Flexible patterns
        r"available\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+\d{1,2}(:\d{2})?\s*(am|pm)",
        r"free\s+(tomorrow|today)\s+at\s+\d{1,2}(:\d{2})?\s*(am|pm)",
    ]
    
    matches = []
    text_lower = text.lower()
    
    for pattern in patterns:
        found = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in found:
            time_str = match.group(0)
            iso_time = convert_natural_to_iso(time_str, timezone)
            if iso_time and iso_time not in matches:  # Avoid duplicates
                matches.append(iso_time)
    
    return matches

def detect_intent(email_body: str) -> str:
    """
    Detect the intent of the email
    
    Args:
        email_body: The email content
        
    Returns:
        Intent string: available, reschedule, cancel, confirm, etc.
    """
    text_lower = email_body.lower()
    
    # Intent keywords
    reschedule_keywords = ['reschedule', 'change', 'move', 'different time', 'another time']
    cancel_keywords = ['cancel', 'cannot make it', "can't make it", 'not available', 'unavailable']
    confirm_keywords = ['confirm', 'sounds good', 'works for me', 'see you then']
    available_keywords = ['available', 'free', 'open', 'can do', 'works']
    
    # Check for specific intents
    if any(keyword in text_lower for keyword in cancel_keywords):
        return "cancel"
    elif any(keyword in text_lower for keyword in reschedule_keywords):
        return "reschedule"
    elif any(keyword in text_lower for keyword in confirm_keywords):
        return "confirm"
    elif any(keyword in text_lower for keyword in available_keywords):
        return "available"
    else:
        return "unknown"

def parse_email(
    email_body: str, 
    from_email: str = "", 
    timezone: str = "UTC"
) -> ParsedAvailability:
    """
    Extracts availability info from email text.

    Args:
        email_body (str): Raw email text from candidate.
        from_email (str): Sender's email (optional).
        timezone (str): Default assumed timezone.

    Returns:
        ParsedAvailability: Structured result for downstream tools.
    """
    # Extract times using enhanced parsing
    times = enhanced_extract_times(email_body, timezone)
    
    # Detect intent
    intent = detect_intent(email_body)
    
    # If no times found but intent suggests availability, mark as such
    if not times and intent == "available":
        intent = "available_no_times"
    
    return ParsedAvailability(
        type="parsed_availability",
        extracted_times=times,
        intent=intent,
        raw_context=email_body[:1000]  # Keep context for downstream processing
    )