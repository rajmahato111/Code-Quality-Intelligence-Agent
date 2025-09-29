#!/usr/bin/env python3
"""
FastAPI Web Server for Code Quality Intelligence Agent

This module provides the web server implementation for the bonus web UI feature.
It serves the React frontend and provides API endpoints for analysis and chat.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Import our analysis components
try:
    from ..orchestrator import AnalysisOrchestrator
    from ..models import AnalysisOptions
    from ..llm.qa_engine import QAEngine
except ImportError:
    # Fallback for development
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from orchestrator import AnalysisOrchestrator
    from models import AnalysisOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Code Quality Intelligence Agent",
    description="AI-powered code analysis with web interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for active connections and analyses
active_connections: Dict[str, WebSocket] = {}
active_analyses: Dict[str, dict] = {}

# Initialize components
orchestrator = AnalysisOrchestrator()
qa_engine = None  # Will be initialized when needed

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# API Routes
@app.get("/")
async def serve_frontend():
    """Serve the React frontend."""
    frontend_path = Path(__file__).parent / "frontend" / "build" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    else:
        # Development fallback
        return {"message": "Frontend not built. Run 'npm run build' in the frontend directory."}

@app.post("/api/analyze")
async def start_analysis(request: dict):
    """Start a new code analysis."""
    try:
        path = request.get("path")
        options = request.get("options", {})
        
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        
        # Generate analysis ID
        analysis_id = f"analysis_{len(active_analyses) + 1}_{hash(path) % 10000}"
        
        # Store analysis info
        active_analyses[analysis_id] = {
            "id": analysis_id,
            "path": path,
            "status": "started",
            "progress": 0
        }
        
        # Start analysis in background
        asyncio.create_task(run_analysis(analysis_id, path, options))
        
        return {"analysis_id": analysis_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis results."""
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return active_analyses[analysis_id]

@app.post("/api/chat")
async def chat_query(request: dict):
    """Handle chat queries about code analysis."""
    try:
        message = request.get("message")
        analysis_id = request.get("analysis_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Mock response for now - in production this would use the QA engine
        response = generate_mock_chat_response(message, analysis_id)
        
        return {"response": response, "timestamp": "2024-01-01T12:00:00Z"}
        
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "start_analysis":
                # Handle analysis start via WebSocket
                path = message.get("path")
                options = message.get("options", {})
                
                analysis_id = f"ws_analysis_{len(active_analyses) + 1}"
                active_analyses[analysis_id] = {
                    "id": analysis_id,
                    "path": path,
                    "status": "started",
                    "progress": 0
                }
                
                # Start analysis and send updates via WebSocket
                asyncio.create_task(run_analysis_with_websocket(analysis_id, path, options, websocket))
                
            elif message.get("type") == "chat_message":
                # Handle chat message via WebSocket
                chat_message = message.get("message")
                analysis_id = message.get("analysis_id")
                
                response = generate_mock_chat_response(chat_message, analysis_id)
                
                await manager.send_personal_message(
                    json.dumps({
                        "type": "chat_response",
                        "response": response,
                        "timestamp": "2024-01-01T12:00:00Z"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_analysis(analysis_id: str, path: str, options: dict):
    """Run analysis in background."""
    try:
        # Update status
        active_analyses[analysis_id]["status"] = "running"
        
        # Simulate analysis progress
        for progress in range(0, 101, 10):
            active_analyses[analysis_id]["progress"] = progress
            await asyncio.sleep(0.5)  # Simulate work
        
        # Generate mock results
        results = generate_mock_analysis_results(path)
        active_analyses[analysis_id].update({
            "status": "completed",
            "progress": 100,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in analysis {analysis_id}: {e}")
        active_analyses[analysis_id]["status"] = "error"
        active_analyses[analysis_id]["error"] = str(e)

async def run_analysis_with_websocket(analysis_id: str, path: str, options: dict, websocket: WebSocket):
    """Run analysis with WebSocket updates."""
    try:
        # Send start notification
        await manager.send_personal_message(
            json.dumps({
                "type": "analysis_started",
                "analysis_id": analysis_id,
                "path": path
            }),
            websocket
        )
        
        # Simulate analysis with progress updates
        stages = [
            "File Discovery",
            "Code Parsing", 
            "Security Analysis",
            "Performance Analysis",
            "Complexity Analysis",
            "Documentation Check",
            "Report Generation"
        ]
        
        for i, stage in enumerate(stages):
            progress = int((i + 1) / len(stages) * 100)
            
            await manager.send_personal_message(
                json.dumps({
                    "type": "analysis_progress",
                    "progress": progress,
                    "stage": stage,
                    "message": f"Processing {stage.lower()}..."
                }),
                websocket
            )
            
            await asyncio.sleep(1)  # Simulate work
        
        # Generate and send results
        results = generate_mock_analysis_results(path)
        
        await manager.send_personal_message(
            json.dumps({
                "type": "analysis_complete",
                "analysis_id": analysis_id,
                "results": results
            }),
            websocket
        )
        
    except Exception as e:
        logger.error(f"Error in WebSocket analysis {analysis_id}: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "analysis_error",
                "analysis_id": analysis_id,
                "error": str(e)
            }),
            websocket
        )

def generate_mock_analysis_results(path: str) -> dict:
    """Generate mock analysis results for demonstration."""
    return {
        "id": f"analysis_{hash(path) % 10000}",
        "path": path,
        "timestamp": "2024-01-01T12:00:00Z",
        "metrics": {
            "overall_score": 75,
            "maintainability_index": 68.5,
            "technical_debt_ratio": 15.2
        },
        "issues": [
            {
                "id": "issue_1",
                "title": "Hardcoded Password",
                "description": "Found hardcoded password in source code. This poses a security risk.",
                "category": "SECURITY",
                "severity": "HIGH",
                "location": {
                    "file_path": f"{path}/app.py",
                    "line_start": 15,
                    "line_end": 15
                },
                "suggestion": "Move password to environment variables or secure configuration.",
                "confidence": 0.9
            },
            {
                "id": "issue_2", 
                "title": "High Cyclomatic Complexity",
                "description": "Function has high cyclomatic complexity (15), making it hard to test and maintain.",
                "category": "COMPLEXITY",
                "severity": "MEDIUM",
                "location": {
                    "file_path": f"{path}/utils.py",
                    "line_start": 42,
                    "line_end": 68
                },
                "suggestion": "Break down the function into smaller, more focused functions.",
                "confidence": 0.8
            },
            {
                "id": "issue_3",
                "title": "Missing Docstring",
                "description": "Function is missing documentation.",
                "category": "DOCUMENTATION", 
                "severity": "LOW",
                "location": {
                    "file_path": f"{path}/helpers.py",
                    "line_start": 8,
                    "line_end": 8
                },
                "suggestion": "Add docstring to explain function purpose and parameters.",
                "confidence": 0.7
            }
        ]
    }

def generate_mock_chat_response(message: str, analysis_id: Optional[str] = None) -> str:
    """Generate mock chat responses for demonstration."""
    message_lower = message.lower()
    
    if "security" in message_lower:
        return """I found 1 security issue in your codebase:

🔴 **Hardcoded Password** (HIGH)
📁 File: app.py:15
💡 Fix: Move password to environment variables

This is a critical security vulnerability that should be fixed immediately. Hardcoded credentials can be exposed if your code is shared or stored in version control."""
    
    elif "performance" in message_lower:
        return """I found several performance issues:

🟡 **High Complexity Function** (MEDIUM)  
📁 File: utils.py:42-68
💡 Fix: Break down into smaller functions

This function has cyclomatic complexity of 15, which makes it hard to test and maintain. Consider refactoring it into smaller, more focused functions."""
    
    elif "complexity" in message_lower:
        return """Here are the complexity issues I found:

🟠 **High Cyclomatic Complexity** (MEDIUM)
📁 File: utils.py:42-68  
📊 Complexity Score: 15 (threshold: 10)
💡 Suggestion: Use early returns and extract helper functions

Complex code is harder to understand, test, and maintain. Breaking it down will improve code quality."""
    
    elif "documentation" in message_lower or "doc" in message_lower:
        return """Documentation issues found:

🔵 **Missing Docstring** (LOW)
📁 File: helpers.py:8
💡 Fix: Add function documentation

Good documentation helps other developers understand your code. Consider adding docstrings that explain:
- What the function does
- Parameters and their types  
- Return value and type
- Usage examples"""
    
    elif "fix" in message_lower or "how" in message_lower:
        return """Here's how to fix the main issues:

**Priority 1 - Security Issues:**
```python
# Instead of:
PASSWORD = "hardcoded123"

# Use:
import os
PASSWORD = os.getenv('DATABASE_PASSWORD')
```

**Priority 2 - Complexity Issues:**
- Break large functions into smaller ones
- Use early returns to reduce nesting
- Extract complex logic into helper functions

**Priority 3 - Documentation:**
- Add docstrings to all functions
- Include type hints
- Add inline comments for complex logic"""
    
    else:
        return f"""I can help you understand your code quality analysis! 

Based on your question "{message}", here are some insights:

📊 **Overall Quality Score: 75/100**
- 1 High priority issue (Security)
- 1 Medium priority issue (Complexity)  
- 1 Low priority issue (Documentation)

💡 **Quick Actions:**
- Fix the hardcoded password immediately
- Refactor complex functions
- Add missing documentation

Ask me more specific questions like:
- "What are the security issues?"
- "How can I improve performance?"
- "Show me the most complex functions"
"""

# Serve static files (React build)
frontend_build_path = Path(__file__).parent / "frontend" / "build"
if frontend_build_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_build_path / "static"), name="static")

def create_app():
    """Factory function to create the FastAPI app."""
    return app

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )