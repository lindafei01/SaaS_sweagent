
#!/usr/bin/env python3
import re
import subprocess
import shlex
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# Define the request and response models
class MonitorRequest(BaseModel):
    filter_flags: Optional[str] = Field(None, description="Flags to filter and sort processes, matching the flags of the 'ps' command")
    command_regex: str = Field(..., description="The regular expression of the commands to search for on the server")

class ProcessInfo(BaseModel):
    processId: int = Field(..., description="The ID of the process")
    processString: str = Field(..., description="The complete string of the process")

class ErrorResponse(BaseModel):
    code: int = Field(..., description="Numeric error code")
    message: str = Field(..., description="Human-readable error message")

# Create the FastAPI application
app = FastAPI(
    title="Monitor Service",
    description="A service that accepts a filter criterion and returns a list of matching process IDs.",
    version="1.0.0"
)

@app.post("/monitor/commands", response_model=List[ProcessInfo])
async def get_processes(request: MonitorRequest):
    """
    Retrieve a list of running processes whose command string matches a given regular expression.
    """
    try:
        # Prepare the ps command with the provided flags or default to 'aux'
        flags = request.filter_flags if request.filter_flags else "aux"
        
        # Validate the flags to prevent command injection
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', flags):
            raise HTTPException(status_code=400, detail={
                "code": 400,
                "message": "Invalid filter flags format"
            })
        
        # Validate the regex pattern
        try:
            regex_pattern = re.compile(request.command_regex)
        except re.error:
            raise HTTPException(status_code=400, detail={
                "code": 400,
                "message": "Invalid regular expression pattern"
            })
        
        # Execute the ps command
        cmd = f"ps {flags}"
        process = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            check=False
        )
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail={
                "code": 500,
                "message": f"Failed to execute ps command: {process.stderr}"
            })
        
        # Parse the output and filter by regex
        output_lines = process.stdout.strip().split('\n')
        
        # Skip the header line
        if len(output_lines) > 1:
            output_lines = output_lines[1:]
        
        matching_processes = []
        for line in output_lines:
            if regex_pattern.search(line):
                # Extract the PID - for 'ps aux' it's in the second column (index 1)
                # For other formats, we'll try to find the first numeric value that could be a PID
                parts = line.split()
                if len(parts) > 0:
                    try:
                        # First try the standard position for 'ps aux'
                        if len(parts) > 1 and parts[1].isdigit():
                            pid = int(parts[1])
                        else:
                            # Otherwise, find the first numeric column
                            for part in parts:
                                if part.isdigit():
                                    pid = int(part)
                                    break
                            else:
                                # No numeric column found
                                continue
                                
                        matching_processes.append(ProcessInfo(
                            processId=pid,
                            processString=line
                        ))
                    except (ValueError, IndexError):
                        # Skip lines that don't have a valid PID
                        continue
        
        return matching_processes
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail={
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        })

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)