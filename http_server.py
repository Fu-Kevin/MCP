# mcp/http_server.py - HTTP wrapper for your MCP tools

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json

# Import your existing MCP tools
from tools.parse_email import parse_email
from tools.check_calendar import check_calendar
from tools.check_real_calendar import check_real_calendar, create_meeting_event
from tools.generate_reply import generate_reply
from tools.timezone_ult import convert_timezone

app = FastAPI(title="Schedule Helper HTTP API", version="1.0.0")

# Add CORS middleware for N8N
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models for HTTP endpoints
class ParseEmailRequest(BaseModel):
    email_body: str
    from_email: str = ""
    timezone: str = "UTC"

class CheckCalendarRequest(BaseModel):
    candidate_times: List[str]

class GenerateReplyRequest(BaseModel):
    candidate_name: Optional[str] = None
    proposed_times: Optional[List[str]] = None
    timezone: str = "UTC"
    from_email: str = ""
    intent: str = "available"

class ConvertTimezoneRequest(BaseModel):
    time_str: str
    from_tz: str
    to_tz: str

class CreateEventRequest(BaseModel):
    candidate_email: str
    meeting_time: str
    candidate_name: Optional[str] = None

# Complete workflow request
class ScheduleWorkflowRequest(BaseModel):
    email_body: str
    from_email: str = ""
    timezone: str = "UTC"
    create_event: bool = False

# HTTP endpoints that wrap your MCP tools
@app.post("/parse_email")
async def http_parse_email(request: ParseEmailRequest):
    """Extract availability from email text"""
    try:
        result = parse_email(
            email_body=request.email_body,
            from_email=request.from_email,
            timezone=request.timezone
        )
        # Convert Pydantic model to dict
        return result.dict() if hasattr(result, 'dict') else result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/check_calendar")
async def http_check_calendar(request: CheckCalendarRequest):
    """Check mock calendar availability"""
    try:
        result = check_calendar(candidate_times=request.candidate_times)
        return result.dict() if hasattr(result, 'dict') else result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/check_real_calendar")
async def http_check_real_calendar(request: CheckCalendarRequest):
    """Check real Google Calendar availability"""
    try:
        result = check_real_calendar(candidate_times=request.candidate_times)
        return result.dict() if hasattr(result, 'dict') else result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate_reply")
async def http_generate_reply(request: GenerateReplyRequest):
    """Generate professional email reply"""
    try:
        result = generate_reply(
            candidate_name=request.candidate_name,
            proposed_times=request.proposed_times,
            timezone=request.timezone,
            from_email=request.from_email,
            intent=request.intent
        )
        return result.dict() if hasattr(result, 'dict') else result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/convert_timezone")
async def http_convert_timezone(request: ConvertTimezoneRequest):
    """Convert time between timezones"""
    try:
        result = convert_timezone(
            time_str=request.time_str,
            from_tz=request.from_tz,
            to_tz=request.to_tz
        )
        return result.dict() if hasattr(result, 'dict') else result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/create_event")
async def http_create_event(request: CreateEventRequest):
    """Create calendar event"""
    try:
        result = create_meeting_event(
            candidate_email=request.candidate_email,
            meeting_time=request.meeting_time,
            candidate_name=request.candidate_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Complete scheduling workflow endpoint
@app.post("/schedule_workflow")
async def schedule_workflow(request: ScheduleWorkflowRequest):
    """Complete scheduling workflow in one call"""
    try:
        # Step 1: Parse email
        print(f"📧 Parsing email from {request.from_email}")
        parsed = parse_email(
            email_body=request.email_body,
            from_email=request.from_email,
            timezone=request.timezone
        )
        
        # Step 2: Check calendar
        print(f"📅 Checking calendar for {len(parsed.extracted_times)} times")
        calendar_result = check_real_calendar(parsed.extracted_times)
        
        # Step 3: Generate reply
        print(f"✉️ Generating reply for {parsed.intent}")
        candidate_name = request.from_email.split('@')[0] if request.from_email else None
        reply = generate_reply(
            candidate_name=candidate_name,
            proposed_times=calendar_result.proposed_meeting_times,
            timezone=request.timezone,
            from_email=request.from_email,
            intent=parsed.intent
        )
        
        # Step 4: Optionally create calendar event
        event_result = None
        if request.create_event and calendar_result.proposed_meeting_times:
            print(f"📅 Creating calendar event")
            event_result = create_meeting_event(
                candidate_email=request.from_email,
                meeting_time=calendar_result.proposed_meeting_times[0],
                candidate_name=candidate_name
            )
        
        return {
            "success": True,
            "parsed": parsed.dict() if hasattr(parsed, 'dict') else parsed,
            "calendar": calendar_result.dict() if hasattr(calendar_result, 'dict') else calendar_result,
            "reply": reply.dict() if hasattr(reply, 'dict') else reply,
            "event": event_result,
            "message": "Scheduling workflow completed successfully"
        }
        
    except Exception as e:
        print(f"❌ Error in scheduling workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Schedule Helper HTTP API is running"}

# List available endpoints
@app.get("/endpoints")
async def list_endpoints():
    """List all available endpoints"""
    return {
        "endpoints": [
            {"path": "/parse_email", "method": "POST", "description": "Extract times from email"},
            {"path": "/check_calendar", "method": "POST", "description": "Check mock calendar"},
            {"path": "/check_real_calendar", "method": "POST", "description": "Check real Google Calendar"},
            {"path": "/generate_reply", "method": "POST", "description": "Generate email reply"},
            {"path": "/convert_timezone", "method": "POST", "description": "Convert timezone"},
            {"path": "/create_event", "method": "POST", "description": "Create calendar event"},
            {"path": "/schedule_workflow", "method": "POST", "description": "Complete scheduling workflow"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/endpoints", "method": "GET", "description": "List endpoints"}
        ]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Schedule Helper HTTP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": "/endpoints"
    }

if __name__ == "__main__":
    print("🚀 Starting Schedule Helper HTTP Server...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    print("🛠️ Endpoints List: http://localhost:8000/endpoints")
    print("🔄 This server wraps your MCP tools for N8N integration")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)