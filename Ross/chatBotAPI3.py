# This is the enhanced REST API interface to the laptop chatbot version 3.5

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
    description = "API for the improved laptop recommendation chatbot with detailed features",
    version = "3.5.0" 
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials = True,
    allow_methods=["GET", "POST"],  # Allow GET and POST methods
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

# Enhanced LaptopRecommendation model with more detailed information
class LaptopRecommendation(BaseModel):
    brand: str
    name: str
    specs: str
    price: Optional[str] = None
    similarity_score: Optional[float] = None
    features: Optional[List[LaptopFeature]] = None
    key_specs: Optional[Dict[str, str]] = None
    # Extended information fields
    image: Optional[str] = None
    has_touchscreen: Optional[bool] = None
    cpu: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    screen_size: Optional[str] = None
    screen_resolution: Optional[str] = None
    refresh_rate: Optional[str] = None
    graphics: Optional[str] = None
    operating_system: Optional[str] = None
    battery_life: Optional[str] = None
    weight: Optional[str] = None
    # Ports
    has_usb_c: Optional[bool] = None
    has_hdmi: Optional[bool] = None
    has_ethernet: Optional[bool] = None
    has_thunderbolt: Optional[bool] = None
    has_display_port: Optional[bool] = None
    # Additional features
    has_backlit_keyboard: Optional[bool] = None
    has_numeric_keyboard: Optional[bool] = None
    has_bluetooth: Optional[bool] = None
    # Performance category
    performance_level: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    recommendations: List[LaptopRecommendation] = []  # Using the enhanced model
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

# This fix focuses on properly extracting RAM information from multiple sources in the data structure

def extract_detailed_laptop_info(laptop_data: Dict) -> Dict:
    """
    Extract detailed information from the laptop data object
    to provide rich information to the frontend
    """
    detailed_info = {
        "has_touchscreen": False,
        "has_usb_c": False,
        "has_hdmi": False,
        "has_ethernet": False,
        "has_thunderbolt": False,
        "has_display_port": False,
        "has_backlit_keyboard": False,
        "has_numeric_keyboard": False,
        "has_bluetooth": False,
        "cpu": None,
        "ram": None,
        "storage": None,
        "screen_size": None,
        "screen_resolution": None,
        "refresh_rate": None,
        "graphics": None,
        "operating_system": None,
        "battery_life": None,
        "weight": None,
        "image": None,
        "performance_level": None
    }
    
    # Extract information from the nested table structure
    for table in laptop_data.get('tables', []):
        title = table.get('title', '')
        data = table.get('data', {})
        
        # Product Details
        if title == 'Product Details':
            if isinstance(data, dict):
                detailed_info['weight'] = data.get('Weight')
                # Get image URL if available
                detailed_info['image'] = data.get('image')
        
        # Misc Data
        elif title == 'Misc':
            if isinstance(data, dict):
                # Save RAM from Memory Installed if it exists
                if data.get('Memory Installed'):
                    detailed_info['ram'] = data.get('Memory Installed')
                detailed_info['operating_system'] = data.get('Operating System')
                detailed_info['battery_life'] = data.get('Battery Life')
        
        # Specs
        elif title == 'Specs':
            if isinstance(data, dict):
                processor_brand = data.get('Processor Brand', '')
                processor_name = data.get('Processor Name', '')
                if processor_brand and processor_name:
                    detailed_info['cpu'] = f"{processor_brand} {processor_name}"
                
                detailed_info['graphics'] = data.get('Graphics Card')
                detailed_info['storage'] = data.get('Storage')
                
                # Some laptops might have RAM info in the specs table instead
                if data.get('RAM') and not detailed_info['ram']:
                    detailed_info['ram'] = data.get('RAM')
                    
                # Infer performance level from specs
                if processor_name and ('i7' in processor_name or 'i9' in processor_name or 
                                     'Ryzen 7' in processor_name or 'Ryzen 9' in processor_name):
                    detailed_info['performance_level'] = 'high'
                elif processor_name and ('i5' in processor_name or 'Ryzen 5' in processor_name):
                    detailed_info['performance_level'] = 'medium'
                elif processor_name:
                    detailed_info['performance_level'] = 'basic'
        
        # Screen
        elif title == 'Screen':
            if isinstance(data, dict):
                detailed_info['screen_size'] = data.get('Size')
                detailed_info['screen_resolution'] = data.get('Resolution')
                detailed_info['refresh_rate'] = data.get('Refresh Rate')
                detailed_info['has_touchscreen'] = bool(data.get('Touchscreen'))
        
        # Features
        elif title == 'Features':
            if isinstance(data, dict):
                detailed_info['has_backlit_keyboard'] = bool(data.get('Backlit Keyboard'))
                detailed_info['has_numeric_keyboard'] = bool(data.get('Numeric Keyboard'))
                detailed_info['has_bluetooth'] = bool(data.get('Bluetooth'))
        
        # Ports
        elif title == 'Ports':
            if isinstance(data, dict):
                detailed_info['has_ethernet'] = bool(data.get('Ethernet (RJ45)'))
                detailed_info['has_hdmi'] = bool(data.get('HDMI'))
                detailed_info['has_usb_c'] = bool(data.get('USB Type-C'))
                detailed_info['has_thunderbolt'] = bool(data.get('Thunderbolt'))
                detailed_info['has_display_port'] = bool(data.get('Display Port'))
    
    return detailed_info

def convert_to_recommendation_model(recommendations, raw_laptops=None):
    """
    Convert the recommendation data from STPrototype3 format to API response format
    with enhanced information
    """
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
            
            # Extract RAM information from key_specs if available
            if "RAM" in rec["key_specs"] and (recommendation.get("ram") is None):
                recommendation["ram"] = rec["key_specs"]["RAM"]
        
        # Find the raw laptop data if provided to extract more details
        if raw_laptops:
            # Find matching laptop in raw data
            for laptop in raw_laptops:
                laptop_brand = ""
                laptop_name = ""
                
                for table in laptop.get('tables', []):
                    if table.get('title') == 'Product Details' and 'data' in table:
                        laptop_brand = table['data'].get('Brand', '')
                        laptop_name = table['data'].get('Name', '')
                        break
                
                # Check if this is the same laptop
                if laptop_brand.lower() == rec["brand"].lower() and laptop_name.lower() == rec["name"].lower():
                    # Extract detailed information
                    detailed_info = extract_detailed_laptop_info(laptop)
                    # Update recommendation with detailed info
                    recommendation.update(detailed_info)
                    break
        
        # Additional check: try to extract RAM from specs string if it's still not available
        if not recommendation.get("ram") and "specs" in recommendation:
            specs = recommendation["specs"]
            ram_match = re.search(r"(\d+\s*GB\s*RAM)", specs, re.IGNORECASE)
            if ram_match:
                recommendation["ram"] = ram_match.group(1)
        
        # Final fallback: Check if RAM is mentioned in the laptop description
        if not recommendation.get("ram") and "specs" in recommendation:
            specs = recommendation["specs"]
            # Look for patterns like "8GB RAM", "16 GB RAM", etc.
            ram_patterns = [
                r"(\d+\s*GB)\s+RAM",
                r"RAM\s+(\d+\s*GB)",
                r"Memory\s+(\d+\s*GB)",
                r"(\d+\s*GB)\s+Memory"
            ]
            
            for pattern in ram_patterns:
                ram_match = re.search(pattern, specs, re.IGNORECASE)
                if ram_match:
                    recommendation["ram"] = ram_match.group(1)
                    break
        
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
        "version": "3.5.0", 
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
            
            # Get filtered laptops to find raw data for detailed information
            filtered_laptops = None
            try:
                filters = {}
                for key, value in chatbot.user_preferences.items():
                    if key != 'use_case' and value:
                        filters[key] = value
                
                filtered_laptops = chatbot._filter_laptops(filters)
                logger.info(f"Found {len(filtered_laptops)} filtered laptops to extract detailed information")
            except Exception as e:
                logger.error(f"Error getting filtered laptops: {e}")
            
            # Convert recommendations to the API response format with enhanced information
            response_data['recommendations'] = convert_to_recommendation_model(
                response_data['recommendations'], 
                filtered_laptops
            )

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
        # Safely access chatbot attributes
        conversation_state = "unknown"
        if session.chatbot:
            conversation_state = session.chatbot.conversation_state
            
        sessions_info.append({
            "session_id": session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "age_minutes": session.get_age_minutes(),
            "conversation_state": conversation_state,
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

# New endpoint to get full laptop details
@app.get("/api/laptop/{brand}/{name}")
async def get_laptop_details(brand: str, name: str):
    """Get detailed information about a specific laptop by brand and name"""
    try:
        # Create a chatbot to access laptop data
        chatbot = LaptopRecommendationBot()
        
        # Search for the laptop
        found_laptop = None
        for laptop in chatbot.laptops:
            laptop_brand = ""
            laptop_name = ""
            
            for table in laptop.get('tables', []):
                if table.get('title') == 'Product Details' and 'data' in table:
                    laptop_brand = table['data'].get('Brand', '')
                    laptop_name = table['data'].get('Name', '')
                    break
            
            if laptop_brand.lower() == brand.lower() and laptop_name.lower() == name.lower():
                found_laptop = laptop
                break
                
        if not found_laptop:
            raise HTTPException(status_code=404, detail=f"Laptop {brand} {name} not found")
            
        # Extract detailed information
        detailed_info = extract_detailed_laptop_info(found_laptop)
        
        # Add basic info
        detailed_info["brand"] = brand
        detailed_info["name"] = name
        detailed_info["specs"] = chatbot._format_laptop_description(found_laptop)
        
        # Add price
        price_value, price_string = chatbot._extract_price_range(found_laptop)
        detailed_info["price"] = price_string if price_string else "Price not available"
        
        # Add key specs
        detailed_info["key_specs"] = chatbot._get_key_specs(found_laptop)
        
        return detailed_info
        
    except Exception as e:
        logger.error(f"Error getting laptop details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting laptop details: {str(e)}")

@app.get("/api/features")
async def get_available_features():
    """Get a list of all available laptop features in the database"""
    try:
        # Create a chatbot to access laptop data
        chatbot = LaptopRecommendationBot()
        
        # Collect all unique features
        features = {
            "brands": set(),
            "screen_sizes": set(),
            "processors": set(),
            "graphics_cards": set(),
            "ram_options": set(),
            "storage_options": set(),
            "operating_systems": set(),
            "special_features": ["touchscreen", "backlit_keyboard", "numeric_keyboard", "bluetooth"],
            "ports": ["usb_c", "hdmi", "ethernet", "thunderbolt", "display_port"]
        }
        
        # Go through all laptops to collect unique features
        for laptop in chatbot.laptops:
            for table in laptop.get('tables', []):
                title = table.get('title', '')
                data = table.get('data', {})
                
                if title == 'Product Details' and isinstance(data, dict):
                    brand = data.get('Brand')
                    if brand:
                        features["brands"].add(brand)
                
                elif title == 'Screen' and isinstance(data, dict):
                    size = data.get('Size')
                    if size:
                        features["screen_sizes"].add(size)
                
                elif title == 'Specs' and isinstance(data, dict):
                    processor = data.get('Processor Name')
                    if processor:
                        features["processors"].add(processor)
                    
                    graphics = data.get('Graphics Card')
                    if graphics:
                        features["graphics_cards"].add(graphics)
                
                elif title == 'Misc' and isinstance(data, dict):
                    ram = data.get('Memory Installed')
                    if ram:
                        features["ram_options"].add(ram)
                    
                    os = data.get('Operating System')
                    if os:
                        features["operating_systems"].add(os)
        
        # Convert sets to lists for JSON serialization
        for key in features:
            if isinstance(features[key], set):
                features[key] = sorted(list(features[key]))
        
        return features
        
    except Exception as e:
        logger.error(f"Error getting available features: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting available features: {str(e)}")

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