# This is the REST API interface to the laptop chatbot version 3

import os 
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Header 
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uuid 
import time
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../Sam/server_side/logs/server.log", rotation="60 MB", retention="35 days", compression="zip")
logger = logger.bind(user="API")

# Add project root to the sys.path to import from other modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import our chatbot model 3
from STPrototype3 import LaptopRecommendationBot

# This initializes the FASTAPI app
app = FastAPI(
    title = "Enhanced Laptop Recommendation API",
    description = "API for the improved laptop recommendation chatbot",
    version = "3.1.0" 
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials = True,
    allow_methods=["POST"],  # Allow GET for health check and POST for chat
    allow_headers=["*"],
)

# Define request and response models with improved fields 
class ChatRequest(BaseModel):
    message: str 
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class LaptopFeature(BaseModel):
    name: str
    value: Union[str, bool, int, float]

# Keeping this class as similar as possible to the original per request
class LaptopRecommendation(BaseModel):
    brand: str
    name: str
    specs: str
    price: Optional[str] = None
    similarity_score: Optional[float] = None
    features: Optional[List[LaptopFeature]] = None
    # Added key_specs from STPrototype3 but making it optional to maintain compatibility
    key_specs: Optional[Dict[str, str]] = None

class ChatResponse(BaseModel):
    message: str
    recommendations: List[LaptopRecommendation] = []  # Fixed field name to match STPrototype3
    next_question: Optional[str] = None
    session_id: str
    detected_use_case: Optional[str] = None
    detected_preferences: Optional[Dict[str, Any]] = None
    conversation_state: Optional[str] = None

class ResetRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ResetResponse(BaseModel):
    message: str
    success: bool
    session_id: str

class DebugInfoResponse(BaseModel):
    message: str
    user_preferences: Dict = {}
    conversation_state: str
    session_id: str
    last_activity: Optional[str] = None
    total_recommendations: int = 0

class HealthResponse(BaseModel):
    status: str
    version: str
    active_sessions: int
    uptime: str

# Session tracking
class SessionInfo:
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Initialize chatbot
        try:
            self.chatbot = LaptopRecommendationBot()
            if hasattr(self.chatbot, 'laptops'):
                logger.info(f"Created chatbot instance with {len(self.chatbot.laptops)} laptops for session {session_id}")
            else:
                logger.warning(f"Created chatbot instance but no laptops found for session {session_id}")
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            # Initialize with empty laptops as fallback
            self.chatbot = LaptopRecommendationBot([])
            logger.info(f"Initialized fallback chatbot with empty laptop list for session {session_id}")
            
        self.total_recommendations = 0

    def update_activity(self):
        self.last_activity = datetime.now()
        logger.info(f"Updating activity to: {self.last_activity}")

    def track_recommendations(self, count: int):
        self.total_recommendations += count
        logger.info(f"Adding a new total recommendations count: {self.total_recommendations}")

    def get_age_minutes(self) -> float:
        age_minutes = (datetime.now() - self.created_at).total_seconds() / 60
        logger.info(f"Age of session: {age_minutes} minutes")
        return age_minutes

# Store active chatbot sessions
active_sessions = {}

# API startup time for uptime calculations
start_time = datetime.now()
logger.info(f"Start time of the API - session: {start_time}")

# Set laptop limit for performance 
LAPTOP_LIMIT = 10000  # Maximum number of laptops to load
SESSION_TIMEOUT_MINUTES = 20  # Timeout for inactive sessions

# Helper functions
def generate_session_id() -> str:
    # Generate a unique session ID
    new_id = str(uuid.uuid4())
    logger.info(f"Initializing session id: {new_id}")
    return new_id

def get_or_create_session(session_id: Optional[str] = None, user_id: Optional[str] = None) -> SessionInfo:
    # Get an existing session or create a new one
    if session_id and session_id in active_sessions:
        session = active_sessions[session_id]
        session.update_activity()
        logger.info(f"Using existing session: {session_id}, for user: {user_id}")
        return session

    logger.warning(f"No session found for user: {user_id}")
    # Create new session 
    new_session_id = session_id or generate_session_id()
    active_sessions[new_session_id] = SessionInfo(new_session_id, user_id)
    logger.info(f"Created new session: {new_session_id} for user: {user_id}")
    return active_sessions[new_session_id]

def cleanup_inactive_sessions():
    # Remove sessions that have been inactive for too long
    current_time = datetime.now()   
    sessions_to_remove = []

    for session_id, session in active_sessions.items():
        inactive_time = (current_time - session.last_activity).total_seconds() / 60
        if inactive_time > SESSION_TIMEOUT_MINUTES:
            sessions_to_remove.append(session_id)
            
    for session_id in sessions_to_remove:
        del active_sessions[session_id]

    logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions. {len(active_sessions)} sessions remaining.")

def convert_to_recommendation_model(recommendations):
    """Convert the recommendation data from STPrototype3 format to API response format"""
    result = []
    for rec in recommendations:
        # Create a base recommendation object
        recommendation = {
            "brand": rec["brand"],
            "name": rec["name"],
            "specs": rec["specs"],
            "price": rec.get("price"),
            "similarity_score": rec.get("similarity_score")
        }
        
        # Add key_specs if available
        if "key_specs" in rec:
            recommendation["key_specs"] = rec["key_specs"]
            
            # Also convert key_specs to features format for backward compatibility
            if "features" not in rec:
                features = []
                for name, value in rec["key_specs"].items():
                    features.append({"name": name, "value": value})
                recommendation["features"] = features
                
        result.append(recommendation)
    return result

# API Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    # Health check endpoint to verify if the API is running and provide system stats
    uptime = datetime.now() - start_time 
    uptime_str = str(uptime).split('.')[0]  # Format without microseconds

    return {
        "status": "ok",
        "version": "3.1.0", 
        "active_sessions": len(active_sessions),
        "uptime": uptime_str
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # Process a chat message and return recommendations
    try:
        logger.info(f"Processing chat message for session: {request.session_id}")
        # Get or create a session
        session = get_or_create_session(request.session_id, request.user_id)
        background_tasks.add_task(cleanup_inactive_sessions)

        # Process the user's message
        chatbot = session.chatbot
        response_data = chatbot.process_input(request.message)

        # Update tracking information
        if 'recommendations' in response_data and response_data['recommendations']:
            session.track_recommendations(len(response_data['recommendations']))
            
            # Convert recommendations to the API response format
            response_data['recommendations'] = convert_to_recommendation_model(response_data['recommendations'])

        # Add session and conversation state info to the response
        response_data["session_id"] = session.session_id
        response_data["conversation_state"] = chatbot.conversation_state 

        # Add detected use case if in the user preferences
        if hasattr(chatbot, 'user_preferences') and 'use_case' in chatbot.user_preferences:
            response_data["detected_use_case"] = chatbot.user_preferences['use_case']

        return response_data

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/api/reset", response_model=ResetResponse)
async def reset_conversation(request: ResetRequest):
    # Reset the conversation state or create a new session
    session_id = request.session_id
    user_id = request.user_id

    if session_id and session_id in active_sessions:
        try: 
            # Reset existing session
            logger.info(f"Attempting to reset existing session: {session_id}")
            session = active_sessions[session_id]
            session.chatbot.reset_conversation()
            session.update_activity()

            return {
                "message": "Conversation has been reset.",
                "success": True,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Could not reset the session: {e}")
            raise HTTPException(status_code=500, detail=f"Error resetting conversation: {str(e)}")
    else:
        # Create a new session
        try:
            logger.info(f"Creating a new session for user: {user_id}")
            new_session = get_or_create_session(user_id=user_id)

            return {
                "message": "New conversation started",
                "success": True,
                "session_id": new_session.session_id
            }
        except Exception as e:
            logger.error(f"Error creating a new session for user: {user_id} - {e}")
            raise HTTPException(status_code=500, detail=f"Error creating new conversation: {str(e)}")

@app.get("/api/debug/{session_id}", response_model=DebugInfoResponse)
async def get_debug_info(session_id: str):
    # Debug endpoint to get the current state of a chatbot session
    if session_id not in active_sessions:
        logger.warning(f"Session: {session_id} was not found")
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session = active_sessions[session_id]
    chatbot = session.chatbot

    return {
        "message": "Debug information",
        "user_preferences": chatbot.user_preferences,
        "conversation_state": chatbot.conversation_state,
        "session_id": session_id,
        "last_activity": session.last_activity.isoformat(),
        "total_recommendations": session.total_recommendations
    }

@app.get("/api/admin/sessions", response_model=List[Dict])
async def list_sessions(admin_key: Optional[str] = Header(None)):
    """Admin endpoint to list all active sessions"""
    # Simple admin key check - should be improved for production
    if not admin_key or admin_key != "admin-secret-key":
        logger.warning(f"Admin key was incorrect: {admin_key}")
        raise HTTPException(status_code=403, detail="Not authorized")
    
    sessions_info = []
    for session_id, session in active_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "age_minutes": session.get_age_minutes(),
            "conversation_state": session.chatbot.conversation_state,
            "total_recommendations": session.total_recommendations
        })
    
    return sessions_info

@app.get("/api/database-status")
async def database_status():
    """Check the database connection status"""
    try:
        # Create a temporary chatbot to test database connection
        test_bot = LaptopRecommendationBot()
        laptop_count = len(test_bot.laptops) if hasattr(test_bot, 'laptops') else 0
        
        db_status = {
            "status": "ok" if laptop_count > 0 else "no_data",
            "laptop_count": laptop_count,
            "data_source": "database" if hasattr(test_bot, '_db_source') and test_bot._db_source == "database" else "json_fallback"
        }
        return db_status
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    try:
        import uvicorn
        
        # Find an available port if 8000 is already in use
        import socket
        port = 8000
        max_port = 8100  # Don't try forever
        
        while port < max_port:
            try:
                # Try to create a socket on the port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                # If we get here, the port is available
                break
            except socket.error:
                logger.warning(f"Port {port} is already in use, trying {port+1}")
                port += 1
                
        if port >= max_port:
            logger.error(f"Could not find an available port between 8000 and {max_port-1}")
            sys.exit(1)
            
        # Run with auto-reload for development
        logger.info(f"Starting server on 0.0.0.0:{port}")
        uvicorn.run("chatBotAPI3:app", host="0.0.0.0", port=port, reload=True)
    except ImportError:
        logger.error("ERROR: uvicorn package is not installed. Please install it with:")
        logger.warning("pip install uvicorn fastapi")
        logger.info("or")
        logger.warning("pip3 install uvicorn fastapi")