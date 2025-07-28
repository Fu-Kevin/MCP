# mcp/main.py - Complete with both calendar tools

from mcp.server.fastmcp import FastMCP

# Import all your tools
from tools.parse_email import parse_email
from tools.generate_reply import generate_reply
from tools.timezone_ult import convert_timezone

# Import both calendar versions
from tools.check_calendar import check_calendar  # Original mock version
from tools.check_real_calendar import check_real_calendar  # Real Google Calendar

def create_server():
    mcp = FastMCP("Schedule Helper MCP - Complete Edition")

    # Register all tools
    mcp.add_tool(parse_email)
    mcp.add_tool(generate_reply)
    mcp.add_tool(convert_timezone)
    
    # Both calendar tools available
    mcp.add_tool(check_calendar)        # Mock calendar (for testing/demo)
    mcp.add_tool(check_real_calendar)   # Real Google Calendar

    print("Schedule Helper MCP Server Started!")
    print("Available tools:")
    print("   - parse_email - Extract times from email text")
    print("   - generate_reply - Create professional responses")
    print("   - convert_timezone - Handle timezone conversions")
    print("   - check_calendar - Mock calendar (testing)")
    print("   - check_real_calendar - Real Google Calendar")
    print("")
    print("Real Google Calendar integration ready!")
    print("Mock calendar available for testing")
    
    return mcp

def main():
    print("Starting Schedule Helper MCP Server...")
    mcp = create_server()
    mcp.run("stdio")

if __name__ == "__main__":
    main()