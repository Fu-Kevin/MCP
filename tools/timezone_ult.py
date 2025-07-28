from protocol import ConvertTimezoneOutput
from datetime import datetime
import pytz
from dateutil import parser
from typing import Dict

# Common timezone abbreviation mappings
TIMEZONE_MAPPINGS: Dict[str, str] = {
    # US Timezones
    'PST': 'America/Los_Angeles',
    'PDT': 'America/Los_Angeles',
    'MST': 'America/Denver',
    'MDT': 'America/Denver',
    'CST': 'America/Chicago',
    'CDT': 'America/Chicago',
    'EST': 'America/New_York',
    'EDT': 'America/New_York',
    
    # Other common abbreviations
    'GMT': 'GMT',
    'BST': 'Europe/London',
    'CET': 'Europe/Paris',
    'JST': 'Asia/Tokyo',
    'IST': 'Asia/Kolkata',
    'AEST': 'Australia/Sydney',
    
    # Keep UTC as is
    'UTC': 'UTC',
    'Z': 'UTC',
}

def normalize_timezone(tz_str: str) -> str:
    """
    Normalize timezone string to a standard format
    
    Args:
        tz_str: Timezone string (could be abbreviation or full name)
        
    Returns:
        Normalized timezone string
    """
    tz_upper = tz_str.upper().strip()
    return TIMEZONE_MAPPINGS.get(tz_upper, tz_str)

def validate_timezone(tz_str: str) -> bool:
    """
    Validate if a timezone string is valid
    
    Args:
        tz_str: Timezone string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        pytz.timezone(tz_str)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False

def parse_time_string(time_str: str) -> datetime:
    """
    Parse various time string formats into datetime object
    
    Args:
        time_str: Time string to parse
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If time string cannot be parsed
    """
    # Remove common suffixes and normalize
    time_str = time_str.strip()
    
    # Handle 'Z' suffix (UTC indicator)
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
    
    # Try different parsing approaches
    try:
        # First try dateutil parser (most flexible)
        return parser.isoparse(time_str)
    except (ValueError, parser.ParserError):
        try:
            # Try standard ISO format
            return datetime.fromisoformat(time_str)
        except ValueError:
            try:
                # Try with microseconds stripped
                if '.' in time_str:
                    time_str = time_str.split('.')[0]
                return datetime.fromisoformat(time_str)
            except ValueError:
                raise ValueError(f"Unable to parse time string: {time_str}")

def convert_timezone(
    time_str: str,
    from_tz: str,
    to_tz: str
) -> ConvertTimezoneOutput:
    """
    Converts a given ISO time string from one timezone to another.

    Args:
        time_str (str): Time string (e.g., '2025-06-20T14:00:00', '2025-06-20T14:00:00Z')
        from_tz (str): Source timezone (e.g., 'PST', 'America/Los_Angeles', 'UTC')
        to_tz (str): Target timezone (e.g., 'UTC', 'EST', 'Europe/London')

    Returns:
        ConvertTimezoneOutput: Result with converted time or None if error
    """
    try:
        # Normalize timezone names
        from_tz_normalized = normalize_timezone(from_tz)
        to_tz_normalized = normalize_timezone(to_tz)
        
        # Validate timezones
        if not validate_timezone(from_tz_normalized):
            raise ValueError(f"Invalid source timezone: {from_tz}")
        
        if not validate_timezone(to_tz_normalized):
            raise ValueError(f"Invalid target timezone: {to_tz}")
        
        # Create timezone objects
        from_zone = pytz.timezone(from_tz_normalized)
        to_zone = pytz.timezone(to_tz_normalized)
        
        # Parse the time string
        dt = parse_time_string(time_str)
        
        # Handle timezone-aware vs naive datetimes
        if dt.tzinfo is None:
            # Naive datetime - localize to source timezone
            dt_localized = from_zone.localize(dt)
        else:
            # Already timezone-aware - convert to source timezone first if needed
            dt_localized = dt.astimezone(from_zone)
        
        # Convert to target timezone
        dt_converted = dt_localized.astimezone(to_zone)
        
        # Format output (ISO format with timezone info)
        result = dt_converted.isoformat()
        
        return ConvertTimezoneOutput(result=result)
        
    except Exception as e:
        error_msg = f"Timezone conversion error: {str(e)}"
        print(f"[timezone_ult] {error_msg}")
        return ConvertTimezoneOutput(result=None)

def get_timezone_info(tz_str: str) -> dict:
    """
    Get information about a timezone
    
    Args:
        tz_str: Timezone string
        
    Returns:
        Dictionary with timezone information
    """
    try:
        tz_normalized = normalize_timezone(tz_str)
        tz = pytz.timezone(tz_normalized)
        now = datetime.now(tz)
        
        return {
            "timezone": tz_normalized,
            "abbreviation": now.strftime('%Z'),
            "utc_offset": now.strftime('%z'),
            "is_dst": bool(now.dst()),
            "current_time": now.isoformat()
        }
    except Exception as e:
        return {
            "error": f"Unable to get timezone info: {str(e)}"
        }

# Utility function for testing
def test_conversion():
    """Test function to verify timezone conversion works correctly"""
    test_cases = [
        ("2025-07-15T14:00:00", "PST", "UTC"),
        ("2025-07-15T14:00:00Z", "UTC", "EST"),
        ("2025-07-15T14:00:00", "America/Los_Angeles", "Europe/London"),
    ]
    
    for time_str, from_tz, to_tz in test_cases:
        result = convert_timezone(time_str, from_tz, to_tz)
        print(f"{time_str} {from_tz} -> {to_tz}: {result.result}")

if __name__ == "__main__":
    test_conversion()