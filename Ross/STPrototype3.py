# Enhanced Sentence Transformer Chatbot with Improved Database Integration

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional, Union
import json
import sys
import os
import re
import psycopg2
from collections import defaultdict
from loguru import logger
from dotenv import load_dotenv

# Setup logger
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/API.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="API")

# Add paths for imports - corrected based on file structure
current_dir = os.path.dirname(os.path.abspath(__file__))  # Ross directory
project_root = os.path.dirname(current_dir)  # Parent directory
server_side_path = os.path.join(project_root, "Sam", "server_side")  # Sam/server_side
dbaccess_path = os.path.join(server_side_path, "DBAccess")  # Sam/server_side/DBAccess

# Add paths to sys.path if they're not already there
for path in [project_root, server_side_path, dbaccess_path]:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)
        logger.info(f"Added path to sys.path: {path}")
    elif not os.path.exists(path):
        logger.warning(f"Path doesn't exist: {path}")

# Try to load the .env file first
try:
    load_dotenv(os.path.join(project_root, '.env'))
    logger.info("Loaded .env file")
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

# First try to import database module via DBAccess
HAS_DB_MODULE = False
try:
    # Import directly based on seen file structure
    from DBAccess.dbAccess import init_db_pool, get_db_connection, release_db_connection
    logger.info("Successfully imported database module")
    
    # Explicitly set DATABASE_NAME to "laptopchatbot_new"
    os.environ["DATABASE_NAME"] = "laptopchatbot_new"
    logger.info("Set DATABASE_NAME environment variable to laptopchatbot_new")
    
    # Initialize the database connection pool
    init_db_pool()
    logger.info("Database pool initialized")
    
    # Test if we can actually get a connection
    try:
        conn, cur = get_db_connection()
        if conn and cur:
            logger.info("Successfully connected to database pool")
            release_db_connection(conn, cur)
            HAS_DB_MODULE = True
        else:
            logger.error("Could not get a connection from the pool")
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
except ImportError as e:
    # Try alternative import path based on the image
    logger.error(f"Failed to import database modules using first method: {e}")
    try:
        sys.path.insert(0, dbaccess_path)  # Ensure this path is first in sys.path
        from dbAccess import init_db_pool, get_db_connection, release_db_connection
        
        # Explicitly set DATABASE_NAME to "laptopchatbot_new"
        os.environ["DATABASE_NAME"] = "laptopchatbot_new"
        logger.info("Set DATABASE_NAME environment variable to laptopchatbot_new (alternative path)")
        
        # Initialize the database connection pool
        init_db_pool()
        logger.info("Database pool initialized (alternative path)")
        
        # Test connection
        conn, cur = get_db_connection()
        if conn and cur:
            logger.info("Successfully connected to database pool using alternative path")
            release_db_connection(conn, cur)
            HAS_DB_MODULE = True
        else:
            logger.error("Could not get a connection from the pool (alternative path)")
    except Exception as alt_e:
        logger.error(f"Failed with alternative import method: {alt_e}")

# Direct database connection function as a fallback
def direct_db_connection():
    """Create a direct connection to the database, bypassing the connection pool"""
    try:
        logger.info("Attempting direct connection to the database")
        # Load potential environment variables first
        load_dotenv(os.path.join(project_root, '.env'))
        
        conn = psycopg2.connect(
            database="laptopchatbot_new",
            user=os.getenv("USER", "postgres"),
            host=os.getenv("DB_HOST", "localhost"),
            password=os.getenv("PASSWORD", "postgres"),
            port=5432
        )
        cur = conn.cursor()
        logger.info("Direct database connection successful")
        return conn, cur
    except Exception as e:
        logger.error(f"Direct database connection failed: {e}")
        return None, None

# Find and load JSON file with laptop data as a last resort
def find_and_load_laptops_json():
    """Search for and load laptop data from a JSON file as fallback"""
    logger.info("Searching for JSON file with laptop data")
    
    possible_paths = [
        # Add potential paths to JSON files based on the shown file structure
        os.path.join(server_side_path, 'scrapers', 'scraped_data', 'latest.json'),
        os.path.join(project_root, 'Sam', 'server_side', 'scrapers', 'scraped_data', 'latest.json'),
        os.path.join(project_root, 'Sam', 'scrapers', 'scraped_data', 'latest.json'),
        os.path.join(project_root, 'data', 'laptops.json'),
        os.path.join(current_dir, 'laptops.json')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                logger.info(f"Found JSON file at {path}")
                with open(path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Successfully loaded {len(data)} laptops from JSON file")
                    return data
            except Exception as e:
                logger.error(f"Error loading JSON file {path}: {e}")
    
    logger.error("No valid JSON file with laptop data found")
    return []

class LaptopRecommendationBot:
    def __init__(self, laptop_data: List[Dict] = None):
        """
        Initialize the chatbot with laptop data and load the sentence transformer model
        
        Args:
            laptop_data: List of dictionaries containing laptop information (optional)
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Try to load laptops either from provided data, database, or JSON file
        if laptop_data:
            self.laptops = laptop_data
            logger.info(f"Using provided laptop data with {len(self.laptops)} records")
        else:
            # First try database connection
            self.laptops = self.load_from_database()
            
            # If database loading failed, try loading from JSON
            if not self.laptops:
                logger.warning("Database loading failed. Attempting to load from JSON file")
                json_data = find_and_load_laptops_json()
                if json_data:
                    self.laptops = json_data
                    logger.info(f"Successfully loaded {len(self.laptops)} laptops from JSON file")
                else:
                    logger.error("Failed to load laptop data from any source")
                    self.laptops = []
        
        self.conversation_state = "initial"
        self.user_preferences = {}
        self.last_recommendations = []  # Store last recommendations for reference
        
        # Expanded predefined questions for gathering user preferences
        self.questions = {
            "initial": "What kind of laptop are you looking for? Please describe your needs in detail.",
            "budget": "What's your approximate budget range?",
            "purpose": "What will you primarily use the laptop for (e.g., gaming, work, studies, design)?",
            "size": "Do you have a preferred screen size (e.g., 13\", 14\", 15.6\", 16\", 17\")?",
            "brand": "Do you have any preferred brands?",
            "features": "Are there any specific features you need (e.g., touchscreen, backlit keyboard, long battery life)?",
            "performance": "How important is performance to you (e.g., high, medium, basic needs)?",
            "ports": "Do you need any specific ports (e.g., HDMI, Ethernet, USB-C, Thunderbolt)?",
            "storage": "What are your storage requirements (e.g., SSD size, additional storage)?",
            "graphics": "Do you need a dedicated graphics card? If so, for what purposes?"
        }
        
        # Create embeddings for predefined features and use cases
        self.feature_embeddings = self._create_feature_embeddings()

    def load_from_database(self, limit=10000) -> List[Dict]:
        """
        Load laptop data from PostgreSQL database using the connection pool or direct connection
        
        Args:
            limit: Maximum number of laptops to load (default: 10000)
        
        Returns:
            List of dictionaries containing laptop information in the same format as the JSON
        """
        conn = None
        cur = None
        
        # Try to use connection pool first if available
        if HAS_DB_MODULE:
            try:
                logger.info(f"Loading up to {limit} laptops from database using connection pool")
                conn, cur = get_db_connection()
                if not conn or not cur:
                    raise Exception("Failed to get database connection from pool")
                
                logger.info("Connection successful")
            except Exception as e:
                logger.error(f"Connection pool error: {e}")
                conn, cur = None, None
        
        # Try direct connection if pool connection failed
        if not conn or not cur:
            try:
                logger.info("Connection pool failed or not available. Trying direct connection")
                conn, cur = direct_db_connection()
                if not conn or not cur:
                    raise Exception("Failed to establish direct database connection")
            except Exception as e:
                logger.error(f"Direct connection error: {e}")
                return []  # Return empty list if all connection attempts failed
        
        try:
            # Get laptop models with limit
            logger.info("Querying laptop_models table")
            cur.execute(f"""
                SELECT model_id, brand, model_name, image_url
                FROM laptop_models
                LIMIT {limit}
            """)
            
            laptop_models = cur.fetchall()
            if not laptop_models:
                logger.error("No laptop models found in database")
                return []
            
            logger.info(f"Found {len(laptop_models)} laptop models")
            
            # Create a list to store all laptop data
            laptops = []
            
            # Process each laptop model
            for laptop_model in laptop_models:
                model_id = laptop_model[0]  # Access by index since not using RealDictCursor
                
                # Create a laptop entry
                laptop = {'tables': []}
                
                # Add product details
                product_details = {
                    'Brand': laptop_model[1],  # brand
                    'Name': laptop_model[2],   # model_name
                    'image': laptop_model[3]   # image_url
                }
                
                laptop['tables'].append({
                    'title': 'Product Details',
                    'data': product_details
                })
                
                # Get configuration details
                cur.execute("""
                    SELECT config_id, price, weight, battery_life, memory_installed, operating_system, 
                           processor, graphics_card
                    FROM laptop_configurations
                    WHERE model_id = %s
                """, (model_id,))
                
                configs = cur.fetchall()
                if not configs:
                    # Skip laptops without configurations
                    continue
                
                # Use the first configuration (most laptops will only have one)
                config = configs[0]
                config_id = config[0]  # config_id
                
                # Add weight to product details
                if config[2]:  # weight
                    product_details['Weight'] = config[2]
                
                # Add misc info
                misc_data = {}
                if config[4]:  # memory_installed
                    misc_data['Memory Installed'] = config[4]
                if config[5]:  # operating_system
                    misc_data['Operating System'] = config[5]
                if config[3]:  # battery_life
                    misc_data['Battery Life'] = config[3]
                
                if misc_data:
                    laptop['tables'].append({
                        'title': 'Misc',
                        'data': misc_data
                    })
                
                # Add price info
                if config[1]:  # price
                    price_data = [
                        {
                            'shop_url': '',  # No shop URL in this schema
                            'price': f"£{config[1]}"
                        }
                    ]
                    
                    laptop['tables'].append({
                        'title': 'Prices',
                        'data': price_data
                    })
                
                # Get processor info if available
                specs_data = {}  # Initialize it outside the if statements
                
                if config[6]:  # processor
                    processor_model = config[6]
                    cur.execute("""
                        SELECT brand, model
                        FROM processors
                        WHERE model = %s
                    """, (processor_model,))
                    
                    processor = cur.fetchone()
                    if processor:
                        processor_data = {
                            'Processor Brand': processor[0],  # brand
                            'Processor Name': processor[1]    # model
                        }
                        
                        # Add to Specs table
                        specs_data.update(processor_data)
                
                # Get graphics card info
                if config[7]:  # graphics_card
                    graphics_model = config[7]
                    cur.execute("""
                        SELECT brand, model
                        FROM graphics_cards
                        WHERE model = %s
                    """, (graphics_model,))
                    
                    graphics = cur.fetchone()
                    if graphics:
                        # Add to specs data
                        specs_data['Graphics Card'] = f"{graphics[0]} {graphics[1]}"  # brand model
                
                # Get storage info
                cur.execute("""
                    SELECT storage_type, capacity
                    FROM configuration_storage
                    WHERE config_id = %s
                """, (config_id,))
                
                storages = cur.fetchall()
                if storages:
                    # Combine all storage entries into one string
                    storage_strings = []
                    for storage in storages:
                        storage_strings.append(f"{storage[1]} {storage[0]}")  # capacity storage_type
                    
                    if storage_strings:
                        # Add to specs data
                        specs_data['Storage'] = ", ".join(storage_strings)
                
                # Add specs table if we have data
                if specs_data:
                    laptop['tables'].append({
                        'title': 'Specs',
                        'data': specs_data
                    })
                
                # Get screen info
                cur.execute("""
                    SELECT size, resolution, touchscreen, refresh_rate
                    FROM screens
                    WHERE config_id = %s
                """, (config_id,))
                
                screen = cur.fetchone()
                if screen:
                    screen_data = {}
                    if screen[0]:  # size
                        screen_data['Size'] = screen[0]
                    if screen[1]:  # resolution
                        screen_data['Resolution'] = screen[1]
                    if screen[2] is not None:  # touchscreen
                        screen_data['Touchscreen'] = bool(screen[2])
                    if screen[3]:  # refresh_rate
                        screen_data['Refresh Rate'] = screen[3]
                    
                    if screen_data:
                        laptop['tables'].append({
                            'title': 'Screen',
                            'data': screen_data
                        })
                
                # Get features
                cur.execute("""
                    SELECT backlit_keyboard, numeric_keyboard, bluetooth
                    FROM features
                    WHERE config_id = %s
                """, (config_id,))
                
                features = cur.fetchone()
                if features:
                    feature_data = {}
                    if features[0] is not None:  # backlit_keyboard
                        feature_data['Backlit Keyboard'] = bool(features[0])
                    if features[1] is not None:  # numeric_keyboard
                        feature_data['Numeric Keyboard'] = bool(features[1])
                    if features[2] is not None:  # bluetooth
                        feature_data['Bluetooth'] = bool(features[2])
                    
                    if feature_data:
                        laptop['tables'].append({
                            'title': 'Features',
                            'data': feature_data
                        })
                
                # Get ports
                cur.execute("""
                    SELECT ethernet, hdmi, usb_type_c, thunderbolt, display_port
                    FROM ports
                    WHERE config_id = %s
                """, (config_id,))
                
                ports = cur.fetchone()
                if ports:
                    port_data = {}
                    if ports[0] is not None:  # ethernet
                        port_data['Ethernet (RJ45)'] = bool(ports[0])
                    if ports[1] is not None:  # hdmi
                        port_data['HDMI'] = bool(ports[1])
                    if ports[2] is not None:  # usb_type_c
                        port_data['USB Type-C'] = bool(ports[2])
                    if ports[3] is not None:  # thunderbolt
                        port_data['Thunderbolt'] = bool(ports[3])
                    if ports[4] is not None:  # display_port
                        port_data['Display Port'] = bool(ports[4])
                    
                    if port_data:
                        laptop['tables'].append({
                            'title': 'Ports',
                            'data': port_data
                        })
                
                # Add this laptop to the list
                laptops.append(laptop)
            
            logger.info(f"Successfully loaded {len(laptops)} laptops from database")
            return laptops
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            return []
        finally:
            # Always close/release the connection properly
            if HAS_DB_MODULE and conn and cur:
                try:
                    release_db_connection(conn, cur)
                    logger.info("Released database connection back to pool")
                except Exception as e:
                    logger.error(f"Error releasing database connection: {str(e)}")
            elif conn:
                if cur:
                    cur.close()
                conn.close()
                logger.info("Closed direct database connection")

    def _create_feature_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Create embeddings for predefined features and use cases with enhanced descriptions
        """
        features = {
            "gaming": """high-performance gaming laptop with dedicated graphics card for AAA games, 
                     high refresh rate display, powerful processor, gaming aesthetics, RGB lighting,
                     excellent cooling, high-end GPU for modern games, gaming laptop, NVIDIA RTX,
                     AMD Radeon, fast storage for game loading, 16GB+ RAM""",
            
            "business": """professional laptop with good battery life, 
                       portable design, windows professional, business laptop, work laptop,
                       productivity features, professional appearance, office work, MS Office,
                       video conferencing, business travel, reliable connectivity""",
            
            "student": """affordable laptop for students with good battery life, 
                      portable, sufficient storage for documents, budget-friendly,
                      college laptop, university laptop, school laptop, student laptop,
                      education laptop, studying, homework, assignments, note-taking""",
            
            "design": """laptop for designers with high-resolution display, color accuracy, 
                     powerful graphics capabilities, creative work, graphic design,
                     photo editing, video editing, art creation, design laptop, creative laptop,
                     Adobe Creative Suite, color calibration, pen support""",
            
            "programming": """laptop for coding with good processor, sufficient RAM, 
                         comfortable keyboard and display, development laptop, coding laptop,
                         software engineering, programming laptop, computer science,
                         software development, web development, app development, multitasking""",
            
            "portable": """lightweight laptop with long battery life, 
                       compact size, good build quality, travel laptop, thin and light,
                       ultraportable, mobility, on-the-go, commuting, travel, under 1.5kg weight""",
            
            "entertainment": """laptop for media consumption with high-quality display, 
                           good speakers, immersive experience, movie watching, music, streaming,
                           content consumption, entertainment laptop, multimedia laptop, HDR support""",
            
            "content_creation": """powerful laptop for content creators, video editing, 
                             rendering, 3D modeling, animation, high-performance processor,
                             professional graphics, large display, content creation laptop, YouTube""",
            
            "budget": """affordable laptop with good value, basic performance,
                    economical, budget-friendly, cost-effective, entry-level laptop,
                    inexpensive laptop, low-cost computing, basic tasks, under £700""",
            
            "premium": """high-end laptop with premium build quality, top specifications,
                     luxury design, excellent display, premium materials, flagship laptop,
                     premium laptop, high-performance, top-tier device, premium price tag""",
                     
            "workstation": """professional workstation laptop with powerful CPU and GPU,
                         CAD software, engineering applications, scientific computing,
                         virtualization, data analysis, simulation, reliable performance""",
                         
            "ultrabook": """ultra-thin laptop with premium design, lightweight portability,
                      fast SSD storage, modern connectivity, long battery life,
                      high-resolution display, metal chassis, elegant appearance"""
        }
        
        return {key: self.model.encode(desc) for key, desc in features.items()}

    # The remaining methods are unchanged from your original implementation
    # I'm omitting them here to keep the artifact focused on the connection logic
    
    # You can include the rest of your LaptopRecommendationBot class methods here
    # They remain the same as in the previous STPrototype3.py

def converse_with_chatbot():
    """
    Main function to run an interactive conversation with the laptop recommendation bot
    """
    # Welcome message and instructions
    print("\n" + "="*60)
    print("Welcome to the Enhanced Laptop Recommendation Bot!")
    print("="*60)
    print("This bot will help you find the perfect laptop based on your needs.")
    print("You can be as specific as you like about your requirements.")
    print("Examples:")
    print("- \"I need a gaming laptop with a 15-inch screen and good battery life\"")
    print("- \"Looking for a lightweight Dell for college under £800\"")
    print("- \"Need a powerful laptop for video editing with at least 16GB RAM\"")
    print("\nYou can exit the conversation by typing 'quit', 'exit', or 'bye'.")
    print("Type 'restart' to begin a new search.\n")
    
    # Initialize the chatbot
    try:
        logger.info("Initializing chatbot...")
        chatbot = LaptopRecommendationBot()
        
        # Check if laptops were loaded
        if not chatbot.laptops:
            logger.error("Error: No laptop data available. Please check your database connection.")
            print("\nError: Could not load laptop data.")
            print("This could be due to database connection issues or missing data files.")
            print("Please check the logs for more information.")
            return
            
        logger.info(f"Chatbot initialized with {len(chatbot.laptops)} laptops")
        
    except Exception as e:
        logger.error(f"Error initializing the chatbot: {str(e)}")
        logger.error("This could be due to issues with the SentenceTransformer model or database connection.")
        print("\nError initializing the chatbot. Please check the logs for more information.")
        return
    
    # Start the conversation with initial question
    print("\nBot:", chatbot.questions["initial"])
    
    # Main conversation loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to exit
            if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                logger.info("User ended conversation")
                print("\nBot: Thank you for using the Enhanced Laptop Recommendation Bot. Goodbye!")
                break
                
            # Process user input
            response = chatbot.process_input(user_input)
            
            # Display bot response
            print("\nBot:", response["message"])
            
            # Display recommendations if any
            if response["recommendations"]:
                print("\nRecommended Laptops:")
                for i, laptop in enumerate(response["recommendations"], 1):
                    print(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")
                    print(f"   Specs: {laptop['specs']}")
                    
                    # Display key specs in a more readable format
                    if 'key_specs' in laptop and laptop['key_specs']:
                        print("   Key specifications:")
                        for spec_name, spec_value in laptop['key_specs'].items():
                            print(f"   - {spec_name}: {spec_value}")
                    
                    print()

            # Display next question if any
            if response["next_question"]:
                print("Bot:", response["next_question"])
                
        except KeyboardInterrupt:
            print("\n\nBot: Conversation interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            print(f"\nBot: I encountered an error processing your request. Let's try again or type 'restart' to begin a new search.")

if __name__ == "__main__":
    # Run the interactive conversation
    converse_with_chatbot()