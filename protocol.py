from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# === MCP Request Types ===
class ScheduleRequest(BaseModel):
    """Request to handle a complete scheduling workflow"""
    type: Literal["schedule_request"]
    from_email: str
    email_body: str
    timezone: str = "UTC"  # e.g. "PST" or "America/Los_Angeles"
    timestamp: Optional[str] = None  # ISO format if provided

    class Config:
        json_schema_extra = {
            "example": {
                "type": "schedule_request",
                "from_email": "candidate@example.com",
                "email_body": "Hi! I'm available Tuesday at 2pm or Wednesday at 10am.",
                "timezone": "America/Los_Angeles"
            }
        }


# === Parsed Output ===
class ParsedAvailability(BaseModel):
    """Result of parsing availability information from email text"""
    type: Literal["parsed_availability"]
    extracted_times: List[str] = Field(description="ISO 8601 time strings extracted from email")
    intent: str = Field(description="Detected intent: available, reschedule, cancel, etc.")
    raw_context: Optional[str] = Field(default=None, description="Original email text for context")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "parsed_availability",
                "extracted_times": ["2025-07-15T14:00:00Z", "2025-07-16T10:00:00Z"],
                "intent": "available",
                "raw_context": "Hi! I'm available Tuesday at 2pm or Wednesday at 10am."
            }
        }


# === Calendar Check Output ===
class AvailableSlots(BaseModel):
    """Result of checking candidate availability against interviewer calendar"""
    type: Literal["available_slots"]
    candidate_times: List[str] = Field(description="Candidate's available time slots")
    interviewer_times: List[str] = Field(description="Interviewer's available time slots")
    proposed_meeting_times: List[str] = Field(description="Overlapping time slots for scheduling")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "available_slots",
                "candidate_times": ["2025-07-15T14:00:00Z", "2025-07-16T10:00:00Z"],
                "interviewer_times": ["2025-07-15T14:00:00Z", "2025-07-17T09:00:00Z"],
                "proposed_meeting_times": ["2025-07-15T14:00:00Z"]
            }
        }


# === Reply Format ===
class EmailReply(BaseModel):
    """Generated email response for scheduling"""
    type: Literal["email_reply"]
    message: str = Field(description="The generated email message text")
    language: str = Field(default="en", description="Language code for the message")
    proposed_time: Optional[str] = Field(default=None, description="Primary proposed meeting time")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "email_reply",
                "message": "Hi there,\n\nThanks for sharing your availability...",
                "language": "en",
                "proposed_time": "2025-07-15T14:00:00Z"
            }
        }


# === Timezone Conversion Output ===
class ConvertTimezoneOutput(BaseModel):
    """Result of timezone conversion operation"""
    result: Optional[str] = Field(description="Converted time in ISO format, or None if conversion failed")

    class Config:
        json_schema_extra = {
            "example": {
                "result": "2025-07-15T22:00:00Z"
            }
        }


# === Error or Status ===
class MCPError(BaseModel):
    """Error response for failed operations"""
    type: Literal["error"]
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
    tool: Optional[str] = Field(default=None, description="Tool that generated the error")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "error": "Invalid timezone format",
                "detail": "Timezone 'XYZ' is not recognized",
                "tool": "convert_timezone"
            }
        }


# === Utility Types ===
class TimeSlot(BaseModel):
    """Represents a time slot with metadata"""
    start_time: str = Field(description="ISO 8601 start time")
    end_time: Optional[str] = Field(default=None, description="ISO 8601 end time")
    timezone: str = Field(default="UTC", description="Timezone for the time slot")
    available: bool = Field(default=True, description="Whether this slot is available")

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "2025-07-15T14:00:00Z",
                "end_time": "2025-07-15T15:00:00Z",
                "timezone": "UTC",
                "available": True
            }
        }