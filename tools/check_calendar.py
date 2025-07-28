from protocol import AvailableSlots
from typing import List
from datetime import datetime, timedelta
import pytz

# Mock interviewer's available slots - in production, this would come from a real calendar API
MOCK_INTERVIEWER_AVAILABILITY = [
    "2025-07-15T14:00:00Z",  # Tuesday 2pm UTC
    "2025-07-15T21:00:00Z",  # Tuesday 9pm UTC  
    "2025-07-16T10:00:00Z",  # Wednesday 10am UTC
    "2025-07-16T21:00:00Z",  # Wednesday 9pm UTC
    "2025-07-17T09:00:00Z",  # Thursday 9am UTC
    "2025-07-17T14:00:00Z",  # Thursday 2pm UTC
    "2025-07-18T15:00:00Z",  # Friday 3pm UTC
    "2025-07-18T20:00:00Z",  # Friday 8pm UTC
]

def normalize_time_to_hour_boundary(time_str: str) -> str:
    """
    Normalize time to the nearest hour boundary for easier matching
    
    Args:
        time_str: ISO format time string
        
    Returns:
        Normalized time string
    """
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # Round to nearest hour
        if dt.minute >= 30:
            dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            dt = dt.replace(minute=0, second=0, microsecond=0)
        return dt.isoformat().replace('+00:00', 'Z')
    except Exception as e:
        print(f"Error normalizing time '{time_str}': {e}")
        return time_str

def find_time_matches(candidate_times: List[str], interviewer_times: List[str]) -> List[str]:
    """
    Find overlapping times between candidate and interviewer availability
    
    Args:
        candidate_times: List of candidate's available times
        interviewer_times: List of interviewer's available times
        
    Returns:
        List of matching times
    """
    matches = []
    
    # Normalize all times for comparison
    normalized_candidate = [normalize_time_to_hour_boundary(t) for t in candidate_times]
    normalized_interviewer = [normalize_time_to_hour_boundary(t) for t in interviewer_times]
    
    # Find exact matches
    for cand_time in normalized_candidate:
        if cand_time in normalized_interviewer:
            matches.append(cand_time)
    
    # If no exact matches, find nearby times (within 2 hours)
    if not matches:
        matches = find_nearby_times(candidate_times, interviewer_times)
    
    return list(set(matches))  # Remove duplicates

def find_nearby_times(candidate_times: List[str], interviewer_times: List[str]) -> List[str]:
    """
    Find interviewer times that are within 2 hours of candidate times
    
    Args:
        candidate_times: Candidate's preferred times
        interviewer_times: Interviewer's available times
        
    Returns:
        List of nearby available times
    """
    nearby_matches = []
    
    for cand_str in candidate_times:
        try:
            cand_dt = datetime.fromisoformat(cand_str.replace('Z', '+00:00'))
            
            for int_str in interviewer_times:
                try:
                    int_dt = datetime.fromisoformat(int_str.replace('Z', '+00:00'))
                    
                    # Check if they're on the same day and within 2 hours
                    if (cand_dt.date() == int_dt.date() and 
                        abs((int_dt - cand_dt).total_seconds()) <= 7200):  # 2 hours = 7200 seconds
                        nearby_matches.append(int_str)
                        
                except Exception as e:
                    print(f"Error parsing interviewer time '{int_str}': {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing candidate time '{cand_str}': {e}")
            continue
    
    return nearby_matches

def generate_alternative_times(candidate_times: List[str]) -> List[str]:
    """
    Generate alternative meeting times if no matches found
    
    Args:
        candidate_times: Candidate's requested times
        
    Returns:
        List of alternative times from interviewer's availability
    """
    if not candidate_times:
        # Return next 3 available slots
        return MOCK_INTERVIEWER_AVAILABILITY[:3]
    
    # Try to find times on same days as candidate requested
    candidate_dates = set()
    for time_str in candidate_times:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            candidate_dates.add(dt.date())
        except Exception:
            continue
    
    alternatives = []
    for time_str in MOCK_INTERVIEWER_AVAILABILITY:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            if dt.date() in candidate_dates:
                alternatives.append(time_str)
        except Exception:
            continue
    
    # If no same-day alternatives, return next available slots
    if not alternatives:
        alternatives = MOCK_INTERVIEWER_AVAILABILITY[:3]
    
    return alternatives[:3]  # Limit to 3 alternatives

def check_calendar(candidate_times: List[str]) -> AvailableSlots:
    """
    Compare candidate's availability with interviewer's and return proposed times.

    Args:
        candidate_times (List[str]): Time strings (ISO 8601) extracted from email

    Returns:
        AvailableSlots: Proposed times for scheduling
    """
    
    # Validate input times
    valid_candidate_times = []
    for time_str in candidate_times:
        try:
            # Validate that it's a proper ISO format
            datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            valid_candidate_times.append(time_str)
        except Exception as e:
            print(f"Invalid time format '{time_str}': {e}")
            continue
    
    # Find matches between candidate and interviewer times
    proposed_times = find_time_matches(valid_candidate_times, MOCK_INTERVIEWER_AVAILABILITY)
    
    # If no matches found, suggest alternatives
    if not proposed_times:
        proposed_times = generate_alternative_times(valid_candidate_times)
    
    return AvailableSlots(
        type="available_slots",
        candidate_times=valid_candidate_times,
        interviewer_times=MOCK_INTERVIEWER_AVAILABILITY,
        proposed_meeting_times=proposed_times
    )