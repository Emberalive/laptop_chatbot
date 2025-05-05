# FastAPI wrapper for the improved chatbot version 2 
# This is the REST API interface to the laptop chatbot version 2

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


logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../Sam/server_side/logs/server.log", rotation="60 MB", retention="35 days", compression="zip")
logger = logger.bind(user="API")
# Add project root tot eh sys.path to import from other modules

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)


# Import or improved chatbot model
# Update import path to mathc your project structure 
from STPrototype2 import LaptopRecommendationBot

# This initlializes the FASTAPI app

app = FastAPI(
    title = "Enhanced Laptop Recommendation API",
    description = "API for the improved laptop recommendation chatbot",
    version = "3.0.0"
)

# Add CORS middleware to allow cross-origin requests

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # NEEDS TO UPDATED FOR PRODUCTION. It's used to speicfy the allowed origin/s 
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and respons emodels with improved fields 

class ChatRequest(BaseModel):
    message: str 
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class LaptopFeature(BaseModel):
    name: str
    value: Union[str, bool, int, float]

class LaptopRecommendation(BaseModel):
    brand: str
    name: str
    specs: str
    price: Optional[str] = None
    similarity_score: Optional[float] = None
    features: Optional[List[LaptopFeature]] = None

class ChatResponse(BaseModel):
    message: str
    _get_recommendations: List[LaptopRecommendation] = []
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
    def __init__(self, session_id:str, user_id: Optional[str]= None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_activty = datetime.now()
        self.chatbot = LaptopRecommendationBot()
        self.total_recommendations = 0

    def update_activity(self):
        self.last_activty = datetime.now()
        logger.info(f"updating activity to: {self.last_activty}")

    def track_recommendations(self, count: int):
        self.total_recommendations += count
        logger.info(f"adding a new total recommendations count: {self.total_recommendations} ")

    def get_age_minutes(self) -> float:
        logger.info(f"Age of session: {(datetime.now() - self.created_at).total_seconds() /60} minutes")
        return(datetime.now() - self.created_at).total_seconds() /60


# Store activate cahtbot sessions

active_sessions = {}

# API startup time for uptime calculations
start_time = datetime.now()
logger.info(f"start time of the api - session: {start_time}")

# Set laptop limit for performance 

LAPTOP_LIMIT = 10000 # Despite the amount of laptops being 2k they are 
SESSION_TIMEOUT_MINUTES = 20 # Timeout for inactive sessions

# Helper fucntions
def generate_session_id() -> str:
    # Generate a unique session ID
    logger.info(f"initialising session id: {str(uuid.uuid4)}")
    return str(uuid.uuid4())

def get_or_create_session(session_id: Optional[str]=None, user_id: Optional[str]=None)-> SessionInfo:
    # Get an existing session or create a new one

    if session_id and session_id in active_sessions:
        session = active_sessions[session_id]
        session.update_activity()
        logger.info(f"Grabbing the active session: {session_id}, for user: {user_id}")
        return session

    logger.warning(f"no session found for user: {user_id}")
    # Create new session 
    new_session_id = session_id or generate_session_id()
    active_sessions[new_session_id] = SessionInfo(new_session_id, user_id)
    logger.info(f"")
    return active_sessions[new_session_id]

def cleanup_inactive_sessions():
    # Remove session that have been inactive for too long
    current_time = datetime.now()   
    sessions_to_remove=[]

    for session_id, session in active_sessions.items():
        inactive_time = (current_time - session.last_activity).total_seconds()/60
        if inactive_time > SESSION_TIMEOUT_MINUTES:
            sessions_to_remove.append(session_id)
            
    for session_id in sessions_to_remove:
        del active_sessions[session_id]

    logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions. {len(active_sessions)} sessions remaining.")


# API Endpoints

@app.get("/api/health", response_model = HealthResponse)
async def health_check():
    # Health check endpoint to verfiy if the api is running a provide system stats
    uptime = datetime.now() - start_time 
    uptime_str = str(uptime).split('.')[0] # Format without microseconds

    return {
        "status": "ok",
        "version": "3.0.0",
        "active_sessions": len(active_sessions),
        "uptime": uptime_str
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    #Process a chat message and return recommendations
    try:
        logger.info("processing a chat message")
        # Get or create a session
        session = get_or_create_session(request.session_id, request.user_id)
        background_tasks.add_task(cleanup_inactive_sessions)

        # Process the user's message
        chatbot = session.chatbot
        response_data = chatbot.process_input(request.message)

        # Update tracking information
        if 'recommendations' in response_data and response_data['recommendations']:
            session.track_recommendations(len(response_data['recommendations']))

        logger.info(f"processing users response dasta")
        # Add session and conversation state info to the repsonse
        repsonse_data["session_id"] = session.session_id
        response_data["conversation_state"] = chatbot.conversation_state 

        #Add detected use case if in the user preferences 

        if hasattr(chatbot, 'user_preferences') and 'use_case' in chatbot.user_preferences:
            response_data["detected_use_case"] = chatbot.user_preferences['use_case']

        return response_data

    except Exception as e:
        logger.error(f"error in processing chat message and returning the results Error: {e}")
        raise HTTPException(status_code=500, detail=f"Eror processing message: {str(e)}")


@app.post("/api/reset", response_model=ResetRequest)
async def reset_conversation(request: ResetRequest):
    #Reset the conversation state or creat  a new session
    session_id = request.session_id
    user_id = request.user_id

    if session_id and session_id in active_sessions:
        try: 
            # Reset existing session
            logger.info(f"attempting to reset existing session:{session_id}")
            session = active_sessions[session_id]
            session.chatbot.reset_conversation()
            session.update_activity()

            return {
                "message": "Conversation has been reset.",
                "Success": True,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"could not reset the session Error: {e}")
            raise HTTPException(status_code=500, detail = f"Error resettign covnersaton: {str(e)}")
        
    else:
        # Create a new session
        try:
            logger.info(f"creating a new session for user: {user_id}")
            new_session = get_or_create_session(user_id=user_id)

            return{
                "message":"New conversation started",
                "success": True,
                "session_id": new_session.session_id
            }
            logger.info(f"New session was created successfully session_id: {new_session.session_id}")

        except Exception as e:
            logger.error(f"Error in making a new session for user: {user_id} Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating new conversation: {str(e)}")

@app.get("/api/debug/{session_id}", response_model = DebugInfoResponse)

async def get_debug_info(session_id: str):
    # Debuf endpoint to get the current state of a chatbot session

    if session_id not in active_sessions:
        logger.warning(f"Session: {session_id} was not available")
        raise HTTPException(status_code=404, detail =f"Session {session_id} not found")

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
        logger.warning(f"admin key was incorrect!! {admin_key}")
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

if __name__ == "__main__":
    try:
        import uvicorn
        # Run with auto-reload for development
        uvicorn.run("chatBotAPI:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        logger.error("ERROR: uvicorn package is not installed. Please install it with:")
        logger.warning("pip install uvicorn fastapi")
        logger.info("or")
        logger.warning("pip3 install uvicorn fastapi")
