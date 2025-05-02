# FastAPI wrapper for the chatbot
# This is the REST API interface to the laptop chatbot

import os
import sys
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json


# Add project root to the sys.path to import from other modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)


from Ross.STPrototype1 import LaptopRecommendationBot

# This initializes FastAPI app
app = FastAPI(
    title="Laptop Recommendation API",
    description="API for the laptop recommendation chatbot",
    version="1.6.0"
)

# Add CORS middleware to allow cross-origin requests 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This is used to specify allowed origins. NEEDS TO BE UPDATED FOR PRODUCTION
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define requests and response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class LaptopRecommendation(BaseModel):
    brand: str
    name: str
    specs: str

class ChatResponse(BaseModel):
    message: str
    recommendations: List[LaptopRecommendation] = []
    next_question: Optional[str] = None
    session_id: Optional[str] = None
    detected_use_case: Optional[str] = None  # Add detected use case information

class ResetRequest(BaseModel):
    session_id: Optional[str] = None

class ResetResponse(BaseModel):
    message: str
    success: bool

class DebugInfoResponse(BaseModel):
    message: str
    user_preferences: Dict = {}
    conversation_state: str
    session_id: str

# Store active chatbot instances 
active_chatbots = {}

# Set laptop limit for performance
LAPTOP_LIMIT = 100  # Can be adjusted based on server capacity

# API Endpoints
@app.get("/api/health")
async def health_check():
    # Health check endpoint to verify if the API is running
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # Process a chat message and returns recommendations
    session_id = request.session_id or "default"

    # Get or create a chatbot instance for this session
    if session_id not in active_chatbots:
        try:
            # Initialize with laptop limit for performance
            active_chatbots[session_id] = LaptopRecommendationBot()
            background_tasks.add_task(cleanup_inactive_sessions)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error initializing chatbot: {str(e)}")

    chatbot = active_chatbots[session_id]

    try:
        # Process the user's message
        response_data = chatbot.process_input(request.message)
        
        # Add session_id to the response
        response_data["session_id"] = session_id
        
        # Add detected use case if in the user preferences
        if hasattr(chatbot, 'user_preferences') and 'use_case' in chatbot.user_preferences:
            response_data["detected_use_case"] = chatbot.user_preferences['use_case']

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/api/reset", response_model=ResetResponse)
async def reset_conversation(request: ResetRequest):
    # Reset the conversation state
    session_id = request.session_id or "default"

    if session_id in active_chatbots:
        try:
            active_chatbots[session_id].reset_conversation()
            return {"message": "Conversation has been reset.", "success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error resetting conversation: {str(e)}")
    else:
        # If session doesn't exist, create a new one (it's already "reset")
        try:
            active_chatbots[session_id] = LaptopRecommendationBot()
            return {"message": "New conversation started", "success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating new conversation: {str(e)}")

@app.get("/api/debug/{session_id}")
async def get_debug_info(session_id: str):
    # Debug endpoint to get the current state of a chatbot session
    if session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    chatbot = active_chatbots[session_id]
    
    return {
        "message": "Debug information",
        "user_preferences": chatbot.user_preferences,
        "conversation_state": chatbot.conversation_state,
        "session_id": session_id
    }

def cleanup_inactive_sessions():
    # Session cleanup function
    if len(active_chatbots) > 100:  # Limit total number of active sessions
        # Just removes oldest sessions
        sessions_to_remove = list(active_chatbots.keys())[:-100]
        for session_id in sessions_to_remove:
            del active_chatbots[session_id]

if __name__ == "__main__":
    try:
        import uvicorn
        # Fix the module name to match the actual file name
        uvicorn.run("chatBotAPI:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("ERROR: uvicorn package is not installed. Please install it with:")
        print("pip install uvicorn fastapi")
        print("or")
        print("pip3 install uvicorn fastapi")