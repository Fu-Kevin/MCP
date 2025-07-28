# mcp/tools/real_check_calendar.py

import os
from datetime import datetime, timedelta
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from protocol import AvailableSlots

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarClient:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Check if we have saved credentials
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    # Delete invalid token and re-authenticate
                    if os.path.exists(self.token_file):
                        os.remove(self.token_file)
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar authenticated successfully!")
    
    def get_busy_times(self, 
                      calendar_id: str = 'primary',
                      days_ahead: int = 14) -> List[dict]:
        """Get busy periods from Google Calendar"""
        
        time_min = datetime.now()
        time_max = time_min + timedelta(days=days_ahead)
        
        body = {
            "timeMin": time_min.isoformat() + 'Z',
            "timeMax": time_max.isoformat() + 'Z',
            "items": [{"id": calendar_id}]
        }
        
        try:
            result = self.service.freebusy().query(body=body).execute()
            busy_times = result['calendars'][calendar_id].get('busy', [])
            print(f"📅 Found {len(busy_times)} busy periods in next {days_ahead} days")
            return busy_times
        except Exception as e:
            print(f"❌ Error getting busy times: {e}")
            return []
    
    def generate_available_slots(self,
                               duration_minutes: int = 60,
                               business_start: int = 9,
                               business_end: int = 17,
                               days_ahead: int = 14) -> List[str]:
        """Generate available time slots"""
        
        busy_times = self.get_busy_times(days_ahead=days_ahead)
        
        # Convert busy times to datetime objects
        busy_periods = []
        for busy in busy_times:
            start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
            busy_periods.append((start, end))
        
        available_slots = []
        current = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Skip to next hour if we're past the start of current hour
        if datetime.now().minute > 0:
            current += timedelta(hours=1)
        
        end_time = current + timedelta(days=days_ahead)
        
        while current < end_time and len(available_slots) < 20:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                current = current.replace(hour=business_start)
                continue
            
            # Skip outside business hours
            if current.hour < business_start or current.hour >= business_end:
                if current.hour >= business_end:
                    # Move to next day
                    current += timedelta(days=1)
                    current = current.replace(hour=business_start)
                else:
                    # Move to business start
                    current = current.replace(hour=business_start)
                continue
            
            # Check if this slot is available
            slot_end = current + timedelta(minutes=duration_minutes)
            is_available = True
            
            for busy_start, busy_end in busy_periods:
                # Check for overlap
                if current < busy_end and slot_end > busy_start:
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(current.isoformat() + 'Z')
            
            # Move to next hour
            current += timedelta(hours=1)
        
        print(f"✅ Generated {len(available_slots)} available slots")
        return available_slots
    
    def create_event(self,
                    summary: str,
                    start_time: str,
                    duration_minutes: int = 60,
                    attendee_emails: List[str] = None,
                    description: str = None) -> dict:
        """Create a calendar event"""
        
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if attendee_emails:
            event['attendees'] = [{'email': email} for email in attendee_emails]
        
        try:
            result = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Send invites to attendees
            ).execute()
            
            print(f"📅 Created calendar event: {result.get('htmlLink')}")
            return result
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return {}

# Global calendar client
_calendar_client = None

def get_calendar_client():
    """Get or create calendar client"""
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
    return _calendar_client

def check_real_calendar(candidate_times: List[str]) -> AvailableSlots:
    """
    Check real Google Calendar for availability
    
    Args:
        candidate_times: List of ISO format times from candidate
        
    Returns:
        AvailableSlots with real calendar data
    """
    try:
        calendar_client = get_calendar_client()
        
        # Get real available slots
        interviewer_times = calendar_client.generate_available_slots(
            duration_minutes=60,
            business_start=9,
            business_end=17,
            days_ahead=14
        )
        
        # Find matches between candidate and interviewer times
        proposed_times = []
        
        for candidate_time in candidate_times:
            try:
                candidate_dt = datetime.fromisoformat(candidate_time.replace('Z', '+00:00'))
                
                # Look for exact hour matches or close matches
                for interviewer_time in interviewer_times:
                    interviewer_dt = datetime.fromisoformat(interviewer_time.replace('Z', '+00:00'))
                    
                    # Check if times are within 2 hours
                    time_diff = abs((candidate_dt - interviewer_dt).total_seconds())
                    if time_diff <= 7200:  # Within 2 hours
                        proposed_times.append(interviewer_time)
                        break
                        
            except Exception as e:
                print(f"Error processing candidate time {candidate_time}: {e}")
                continue
        
        # If no matches, suggest first few available slots
        if not proposed_times:
            proposed_times = interviewer_times[:3]
        
        print(f"🎯 Found {len(proposed_times)} proposed meeting times")
        
        return AvailableSlots(
            type="available_slots",
            candidate_times=candidate_times,
            interviewer_times=interviewer_times,
            proposed_meeting_times=proposed_times[:5]  # Limit to 5 suggestions
        )
        
    except Exception as e:
        print(f"❌ Error with Google Calendar: {e}")
        print("🔄 Falling back to mock calendar...")
        
        # Fallback to original mock function
        from tools.check_calendar import check_calendar
        return check_calendar(candidate_times)

def create_meeting_event(
    candidate_email: str,
    meeting_time: str,
    candidate_name: str = None
) -> dict:
    """
    Create a calendar event for the scheduled meeting
    
    Args:
        candidate_email: Email of the candidate
        meeting_time: ISO format time for the meeting
        candidate_name: Name of the candidate
        
    Returns:
        Dict with event details
    """
    try:
        calendar_client = get_calendar_client()
        
        summary = f"Interview - {candidate_name or candidate_email.split('@')[0]}"
        description = f"Interview scheduled with {candidate_email}"
        
        result = calendar_client.create_event(
            summary=summary,
            start_time=meeting_time,
            duration_minutes=60,
            attendee_emails=[candidate_email],
            description=description
        )
        
        return {
            "success": True,
            "event_id": result.get('id'),
            "event_link": result.get('htmlLink'),
            "message": f"Calendar event created successfully"
        }
        
    except Exception as e:
        print(f"Error creating meeting event: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create calendar event"
        }