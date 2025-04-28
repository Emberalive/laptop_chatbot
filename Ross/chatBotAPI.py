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
    title ="Laptop Recommendation API",
    description="APi for the laptop recommendation chatbot",
    version="1.0.0"
)

# Add CORS() middleware to allow cross-origin requests 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # THis is used to specify allowed origins. NEEDS TO BE ADDED
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define requests and response models

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class LaptopRecommendation(BaseModel):
    brand:  str
    name: str
    specs: str

class ChatResponse(BaseModel):
    message: str
    recommendations: List[LaptopRecommendation] = []
    next_question: Optional[str] = None
    session_id: Optional[str] = None

class ResetRequest(BaseModel):
    session_id: Optional[str] = None

class ResetResponse(BaseModel):
    message: str
    success: bool

# Store active chatbot instances 

active_chatbots = {}


# API Endpoints


@app.get("/api/health")
async def health_check():
    # Health check endpoint ot verfiy if the API is runnign
    return {"status":"ok"}


@app.post("/api/chat", response_model = ChatResponse)
async def chat(request: ChatRequest, Background_tasks: BackgroundTasks):

    # This processes a chat message and returns recommendations
    session_id = request.session_id or "default"

    # Get or create a chatbot instance for this session
    if session_id not in active_chatbots:
        try:
            active_chatbots[session_id] = LaptopRecommendationBot()
            Background_tasks.add_task(cleanup_inactive_sessions)
        except Exception as e:
            raise HTTPException(status_code=500, detail = f"Error intialising chatbot: {str(e)}")

    chatbot = active_chatbots[session_id]

    try:
        # process the users message

        response = chatbot.process_input(request.message)

        # Addd sessions_id to the response
        response["session_id"] = session_id

        return response

    except Exception as e :
        raise HTTPException(staus_code=500, detail=f"Erorr processing message: {str(e)}")

@app.post("/api/reset", response_model=ResetResponse)
async def reset_conversation(request: ResetRequest):
    # Reset the converstion state

    sessions_id = request.session_id or "default"

    if sessions_id in active_chatbots:
        try: 
        
            active_chatbots[sessions_id].reset_conversation()
            return {"message": "Conversation has been reset.", "succes": True}

        except Exception as e:
            raise HTTPException(status_code=500, detail = f"Error resetting conversation: {str(e)}")

    else:
        # If sessions doesnt exist, create a new one(its' already "reset")

        try:
            active_chatbots[sessions_id] = LaptopRecommendationBot()

            return {"message": "New conversation started", "success": True}

        except Exception as e:
            raise HTTPException(status_code=500, detail = f"Error creating new conversation: {str(e)}")


def cleanup_inactive_sessions():

    # Session cleanup function
    if len(active_chatbots) > 100: # Limit total number of active sessions

        # Just removes oldest session 

        session_to_remove = list(active_chatbots.keys())[:-100]
        for session_id in session_to_remove: 
            del active_chatbots[session_id]



if __name__ == "__name__":
    import uvicorn 

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

