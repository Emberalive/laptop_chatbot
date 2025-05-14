# Enhanced Sentence Transformer Chatbot with Improved Database Integration and Random Selection

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
import random  # Import random module for random selection
import time 

# Setup logger
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/API.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="API")

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
server_side_path = os.path.join(project_root, "Sam", "server_side")
dbaccess_path = os.path.join(server_side_path, "DBAccess")

# Add paths to sys.path if they're not already there
for path in [project_root, server_side_path, dbaccess_path]:
    if path not in sys.path and os.path.exists(path):
        sys.path.append(path)

# First try to import database module via DBAccess
HAS_DB_MODULE = False
try:
    from DBAccess.dbAccess import get_db_connection, release_db_connection
    logger.info("Successfully imported database module")
    
    # Override the database name in .env with laptopchatbot_new if needed
    if "DATABASE_NAME" in os.environ:
        original_db = os.environ["DATABASE_NAME"]
        os.environ["DATABASE_NAME"] = "laptopchatbot_new"
        logger.info(f"Database name overridden from {original_db} to laptopchatbot_new")
    else:
        os.environ["DATABASE_NAME"] = "laptopchatbot_new"
        logger.info("Set DATABASE_NAME environment variable to laptopchatbot_new")
    
    # Initialize the database connection pool
    # init_db_pool()
    # logger.info("Database pool initialized")
    
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
    logger.error(f"Failed to import database modules: {e}")

# Try to load settings from a potential .env file if it exists
def load_environment_settings():
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        logger.info(f"Found .env file at {env_path}")
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                        logger.info(f"Loaded setting {key} from .env file")
            return True
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
    else:
        logger.error(f"No .env file found at {env_path}")
    return False

# Attempt to load .env if we don't have a working database connection
if not HAS_DB_MODULE:
    load_environment_settings()
    try:
        from DBAccess.dbAccess import get_db_connection, release_db_connection
        # Force database name to be correct
        os.environ["DATABASE_NAME"] = "laptopchatbot_new"
        logger.info("Set DATABASE_NAME environment variable to laptopchatbot_new")
        
        # Try to initialize the pool again
        # init_db_pool()
        
        # Test connection
        conn, cur = get_db_connection()
        if conn and cur:
            logger.info("Successfully connected to database pool on second attempt")
            release_db_connection(conn, cur)
            HAS_DB_MODULE = True
    except Exception as e:
        logger.error(f"Second attempt to connect to database failed: {e}")

# Direct database connection function as a fallback
def direct_db_connection():
    """Create a direct connection to the database, bypassing the connection pool"""
    try:
        logger.info("Attempting direct connection to the database")
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
        # Add potential paths to JSON files here
        os.path.join(server_side_path, 'scrapers', 'scraped_data', 'latest.json'),
        os.path.join(project_root, 'Sam', 'server_side', 'scrapers', 'scraped_data', 'latest.json'),
        os.path.join(project_root, 'scrapers', 'scraped_data', 'latest.json'),
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
        
        # Add new variables for storing top similar laptops and search criteria
        self.top_similar_laptops = []  # Store the top 15 most similar laptops
        self.last_search_criteria = {}  # Store the last search criteria to detect repeats
        
        # Expanded predefined questions for gathering user preferences
        self.questions = {
            "initial": "What kind of laptop are you looking for? Please describe your needs in detail.",
            "purpose": "What will you primarily use the laptop for (e.g., gaming, work, studies, design)?",
            "size": "Do you have a preferred screen size (e.g., 13\", 14\", 15.6\", 16\", 17\")? You can also say small, medium, or large.",
            "budget": "What's your approximate budget range? This helps me find laptops that fit your price expectations.",
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
                        specs_data = {}
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
                        if 'specs_data' not in locals():
                            specs_data = {}
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
                        if 'specs_data' not in locals():
                            specs_data = {}
                        specs_data['Storage'] = ", ".join(storage_strings)
                
                # Add specs table if we have data
                if 'specs_data' in locals() and specs_data:
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

    def _format_laptop_description(self, laptop: Dict) -> str:
        """
        Create a detailed description string from laptop specifications
        """
        tables = laptop.get('tables', [])
        details = {}
        
        # Extract relevant information from nested structure
        for table in tables:
            title = table.get('title', '')
            data = table.get('data', {})
            
            if isinstance(data, dict):
                if title == 'Product Details':
                    details.update(data)
                elif title == 'Specs':
                    details.update(data)
                elif title == 'Screen':
                    for key, value in data.items():
                        details[f"Screen {key}"] = value
                elif title == 'Features':
                    for key, value in data.items():
                        details[f"Feature {key}"] = value
                elif title == 'Ports':
                    for key, value in data.items():
                        if value:  # Only include ports that are present
                            details[f"Has {key}"] = value
                elif title == 'Misc':
                    details.update(data)
        
        # Build the description with available information
        brand = details.get('Brand', '')
        name = details.get('Name', '')
        description = f"{brand} {name}"
        
        # Add processor info
        processor_brand = details.get('Processor Brand', '')
        processor_name = details.get('Processor Name', '')
        if processor_brand and processor_name:
            description += f" with {processor_brand} {processor_name} processor"
        
        # Add memory
        memory = details.get('Memory Installed', '')
        if memory:
            description += f", {memory} RAM"
        
        # Add storage
        storage = details.get('Storage', '')
        if storage:
            description += f", {storage} storage"
        
        # Add screen info
        screen_size = details.get('Screen Size', '')
        screen_resolution = details.get('Screen Resolution', '')
        if screen_size or screen_resolution:
            screen_info = ""
            if screen_size:
                screen_info += f"{screen_size}"
            if screen_resolution:
                if screen_info:
                    screen_info += f" {screen_resolution}"
                else:
                    screen_info = screen_resolution
            description += f", {screen_info} display"
        
        # Add screen refresh rate if available
        refresh_rate = details.get('Screen Refresh Rate', '')
        if refresh_rate:
            description += f" with {refresh_rate} refresh rate"
        
        # Add graphics card
        graphics = details.get('Graphics Card', '')
        if graphics:
            description += f", {graphics} graphics"
        
        # Add operating system
        os = details.get('Operating System', '')
        if os:
            description += f", {os}"
        
        # Add battery life
        battery_life = details.get('Battery Life', '')
        if battery_life:
            description += f", {battery_life} battery life"
        
        # Add weight information
        weight = details.get('Weight', '')
        if weight:
            description += f", weighing {weight}"
        
        # Add key features
        features = []
        for key, value in details.items():
            if key.startswith('Feature ') and value is True:
                feature_name = key.replace('Feature ', '')
                features.append(feature_name)
        
        if features:
            description += f". Features include: {', '.join(features)}"
        
        # Add ports information
        ports = []
        for key, value in details.items():
            if key.startswith('Has ') and value is True:
                port_name = key.replace('Has ', '')
                ports.append(port_name)
        
        if ports:
            description += f". Ports include: {', '.join(ports)}"
        
        return description

    def _extract_price_range(self, laptop: Dict) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract the lowest price from a laptop's price table with improved robustness
        Returns: (price_value, price_string)
        """
        price_value = None
        price_string = None
        
        # First look in Prices table
        for table in laptop.get('tables', []):
            if table.get('title') == 'Prices' and 'data' in table:
                prices_data = table['data']
                if isinstance(prices_data, list) and prices_data:
                    # Find the lowest price
                    lowest_price = None
                    lowest_price_str = None
                    
                    for price_entry in prices_data:
                        price_str = price_entry.get('price', '')
                        if price_str and price_str != 'N/A':
                            # Clean and convert price string to float
                            clean_price = re.sub(r'[^0-9.]', '', price_str.replace(',', ''))
                            try:
                                price_val = float(clean_price)
                                if lowest_price is None or price_val < lowest_price:
                                    lowest_price = price_val
                                    lowest_price_str = price_str
                            except ValueError:
                                continue
                    
                    price_value = lowest_price
                    price_string = lowest_price_str
        
        # If no price found in Prices table look for price in Product Details or other tables
        if price_value is None:
            for table in laptop.get('tables', []):
                data = table.get('data', {})
                if isinstance(data, dict):
                    # Check for common price field names
                    for field in ['Price', 'price', 'Cost', 'cost', 'MSRP', 'msrp', 'RRP', 'rrp']:
                        if field in data and data[field]:
                            price_str = str(data[field])
                            if price_str and price_str != 'N/A':
                                # Clean and convert price string to float
                                clean_price = re.sub(r'[^0-9.]', '', price_str.replace(',', ''))
                                try:
                                    price_value = float(clean_price)
                                    price_string = price_str
                                    break
                                except ValueError:
                                    continue
        
        return (price_value, price_string)

    def _enhanced_parse_budget_range(self, budget_input: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Enhanced parser for budget ranges with better pattern recognition
        Returns: (min_budget, max_budget) in float values
        """
        # Remove currency symbols and commas
        cleaned_input = budget_input.replace('£', '').replace('$', '').replace('€', '').replace(',', '').lower()
        
        # Look for range patterns like "500-1000" or "between 500 and 1000"
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', cleaned_input)
        between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', cleaned_input)
        from_to_match = re.search(r'from\s+(\d+)\s+to\s+(\d+)', cleaned_input)
        
        if range_match:
            return (float(range_match.group(1)), float(range_match.group(2)))
        elif between_match:
            return (float(between_match.group(1)), float(between_match.group(2)))
        elif from_to_match:
            return (float(from_to_match.group(1)), float(from_to_match.group(2)))
        
        # Look for "under X" or "less than X" patterns
        under_match = re.search(r'(?:under|less than|below|max|maximum|no more than)\s+(\d+)', cleaned_input)
        if under_match:
            return (None, float(under_match.group(1)))
        
        # Look for "over X" or "more than X" patterns
        over_match = re.search(r'(?:over|more than|above|min|minimum|at least)\s+(\d+)', cleaned_input)
        if over_match:
            return (float(over_match.group(1)), None)
        
        # Look for "around X" patterns
        around_match = re.search(r'(?:around|about|approximately|roughly|circa)\s+(\d+)', cleaned_input)
        if around_match:
            budget = float(around_match.group(1))
            # Give a wider 30% range for "around"
            return (budget * 0.7, budget * 1.3)
        
        # Look for "X pounds" or just a number
        number_match = re.search(r'(\d+)(?:\s*(?:pounds|pound|gbp))?', cleaned_input)
        if number_match:
            budget = float(number_match.group(1))
            # Assume 20% flexibility around the stated budget
            return (budget * 0.8, budget * 1.2)
        
        # Detect budget ranges from common terms
        budget_terms = {
            "budget": (None, 500),
            "cheap": (None, 400),
            "affordable": (None, 600),
            "mid-range": (600, 1000),
            "mid range": (600, 1000),
            "high-end": (1000, None),
            "high end": (1000, None),
            "premium": (1200, None),
            "expensive": (1500, None)
        }
        
        for term, (min_val, max_val) in budget_terms.items():
            if term in cleaned_input:
                return (min_val, max_val)
        
        # If no patterns match, return None
        return (None, None)

    def _filter_laptops(self, filters: Dict = None) -> List[Dict]:
        """
        Filter laptops based on user preferences
        """
        if not filters:
            return self.laptops

        filtered_laptops = self.laptops
        logger.info(f"Starting filtering with {len(filtered_laptops)} laptops")
        
        # Filter by screen size
        if 'size' in filters and filters['size']:
            # Convert string sizes to actual sizes for comparison
            size_values = []
            for size in filters['size']:
                try:
                    # Handle ranges like "13-14"
                    if isinstance(size, str) and '-' in size:
                        min_size, max_size = map(float, size.split('-'))
                        size_values.extend([min_size, max_size])
                    else:
                        size_values.append(float(str(size).replace('"', '')))
                except ValueError:
                    continue
            
            if size_values:
                min_size = min(size_values)
                max_size = max(size_values)
                
                size_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Screen' and 'data' in table:
                            size_str = table['data'].get('Size', '')
                            if size_str:
                                try:
                                    # Extract just the numeric part
                                    laptop_size = float(re.search(r'(\d+(\.\d+)?)', size_str).group(1))
                                    if min_size <= laptop_size <= max_size:
                                        size_filtered.append(laptop)
                                        break
                                except (ValueError, AttributeError):
                                    continue
                filtered_laptops = size_filtered
                logger.info(f"After size filtering: {len(filtered_laptops)} laptops")
        
        # Filter by brand
        if 'brand' in filters and filters['brand']:
            brand_filtered = []
            brand_names = [b.lower() for b in filters['brand']]
            
            for laptop in filtered_laptops:
                for table in laptop.get('tables', []):
                    if table.get('title') == 'Product Details' and 'data' in table:
                        brand = table['data'].get('Brand', '').lower()
                        if brand and any(b in brand for b in brand_names):
                            brand_filtered.append(laptop)
                            break
            filtered_laptops = brand_filtered
            logger.info(f"After brand filtering: {len(filtered_laptops)} laptops")
        
        # Filter by budget - IMPROVED VERSION
        if 'budget' in filters and (filters['budget'][0] is not None or filters['budget'][1] is not None):
            min_budget, max_budget = filters['budget']
            
            # Separate laptops with and without prices
            laptops_with_price = []
            laptops_without_price = []
            
            for laptop in filtered_laptops:
                price_value, _ = self._extract_price_range(laptop)
                
                if price_value is not None:
                    # Only add laptops that meet the budget criteria
                    if (min_budget is None or price_value >= min_budget) and \
                       (max_budget is None or price_value <= max_budget):
                        laptops_with_price.append(laptop)
                else:
                    laptops_without_price.append(laptop)
            
            # If we have laptops with prices that meet criteria, use those
            if laptops_with_price:
                filtered_laptops = laptops_with_price
                logger.info(f"After budget filtering: {len(filtered_laptops)} laptops with prices in range")
            else:
                # If no laptops with prices in range, include some laptops without prices
                # to avoid empty results, but limit to a reasonable number
                filtered_laptops = laptops_without_price[:min(50, len(laptops_without_price))]
                logger.info(f"No laptops with prices in range. Using {len(filtered_laptops)} laptops without price info")
        
        # Filter by features
        if 'features' in filters:
            features = filters['features']
            
            # Filter by touchscreen
            if 'touchscreen' in features:
                feature_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Screen' and 'data' in table:
                            touchscreen = table['data'].get('Touchscreen')
                            if touchscreen is True:
                                feature_filtered.append(laptop)
                                break
                filtered_laptops = feature_filtered
                logger.info(f"After touchscreen filtering: {len(filtered_laptops)} laptops")
            
            # Filter by backlit keyboard
            if 'backlit_keyboard' in features:
                feature_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Features' and 'data' in table:
                            backlit = table['data'].get('Backlit Keyboard')
                            if backlit is True:
                                feature_filtered.append(laptop)
                                break
                filtered_laptops = feature_filtered
                logger.info(f"After backlit keyboard filtering: {len(filtered_laptops)} laptops")
            
            # Filter by numeric keyboard
            if 'numeric_keyboard' in features:
                feature_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Features' and 'data' in table:
                            numeric = table['data'].get('Numeric Keyboard')
                            if numeric is True:
                                feature_filtered.append(laptop)
                                break
                filtered_laptops = feature_filtered
                logger.info(f"After numeric keyboard filtering: {len(filtered_laptops)} laptops")
            
            # Filter by bluetooth
            if 'bluetooth' in features:
                feature_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Features' and 'data' in table:
                            bluetooth = table['data'].get('Bluetooth')
                            if bluetooth is True:
                                feature_filtered.append(laptop)
                                break
                filtered_laptops = feature_filtered
                logger.info(f"After bluetooth filtering: {len(filtered_laptops)} laptops")
        
        # Filter by ports
        if 'ports' in filters:
            ports = filters['ports']
            
            # Filter by USB-C
            if 'usb_c' in ports:
                ports_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Ports' and 'data' in table:
                            usb_c = table['data'].get('USB Type-C')
                            if usb_c is True:
                                ports_filtered.append(laptop)
                                break
                filtered_laptops = ports_filtered
                logger.info(f"After USB-C filtering: {len(filtered_laptops)} laptops")
            
            # Filter by HDMI
            if 'hdmi' in ports:
                ports_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Ports' and 'data' in table:
                            hdmi = table['data'].get('HDMI')
                            if hdmi is True:
                                ports_filtered.append(laptop)
                                break
                filtered_laptops = ports_filtered
                logger.info(f"After HDMI filtering: {len(filtered_laptops)} laptops")
            
            # Filter by Ethernet
            if 'ethernet' in ports:
                ports_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Ports' and 'data' in table:
                            ethernet = table['data'].get('Ethernet (RJ45)')
                            if ethernet is True:
                                ports_filtered.append(laptop)
                                break
                filtered_laptops = ports_filtered
                logger.info(f"After Ethernet filtering: {len(filtered_laptops)} laptops")
            
            # Filter by Thunderbolt
            if 'thunderbolt' in ports:
                ports_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Ports' and 'data' in table:
                            thunderbolt = table['data'].get('Thunderbolt')
                            if thunderbolt is True:
                                ports_filtered.append(laptop)
                                break
                filtered_laptops = ports_filtered
                logger.info(f"After Thunderbolt filtering: {len(filtered_laptops)} laptops")
            
            # Filter by Display Port
            if 'display_port' in ports:
                ports_filtered = []
                for laptop in filtered_laptops:
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Ports' and 'data' in table:
                            display_port = table['data'].get('Display Port')
                            if display_port is True:
                                ports_filtered.append(laptop)
                                break
                filtered_laptops = ports_filtered
                logger.info(f"After Display Port filtering: {len(filtered_laptops)} laptops")
        
        # Filter by performance level
        if 'performance' in filters:
            perf_level = filters['performance']
            
            if perf_level == 'high':
                # Look for high-end processors and GPUs
                performance_filtered = []
                high_end_patterns = [
                    r'i7', r'i9', r'Ryzen 7', r'Ryzen 9', 
                    r'RTX', r'Radeon RX', r'Quadro', 
                    r'32GB', r'64GB'
                ]
                
                for laptop in filtered_laptops:
                    laptop_desc = self._format_laptop_description(laptop)
                    if any(re.search(pattern, laptop_desc, re.IGNORECASE) for pattern in high_end_patterns):
                        performance_filtered.append(laptop)
                
                filtered_laptops = performance_filtered if performance_filtered else filtered_laptops
                logger.info(f"After high performance filtering: {len(filtered_laptops)} laptops")
            
            elif perf_level == 'medium':
                # Look for mid-range processors and GPUs
                performance_filtered = []
                mid_range_patterns = [
                    r'i5', r'Ryzen 5', 
                    r'GTX', r'Radeon', 
                    r'16GB'
                ]
                
                for laptop in filtered_laptops:
                    laptop_desc = self._format_laptop_description(laptop)
                    if any(re.search(pattern, laptop_desc, re.IGNORECASE) for pattern in mid_range_patterns):
                        performance_filtered.append(laptop)
                
                filtered_laptops = performance_filtered if performance_filtered else filtered_laptops
                logger.info(f"After medium performance filtering: {len(filtered_laptops)} laptops")
            
            elif perf_level == 'basic':
                # Look for entry-level processors and integrated graphics
                performance_filtered = []
                basic_patterns = [
                    r'i3', r'Celeron', r'Pentium', r'Ryzen 3', r'A\d+', 
                    r'UHD Graphics', r'Intel Graphics', r'AMD Graphics', 
                    r'4GB', r'8GB'
                ]
                
                for laptop in filtered_laptops:
                    laptop_desc = self._format_laptop_description(laptop)
                    if any(re.search(pattern, laptop_desc, re.IGNORECASE) for pattern in basic_patterns):
                        performance_filtered.append(laptop)
                
                filtered_laptops = performance_filtered if performance_filtered else filtered_laptops
                logger.info(f"After basic performance filtering: {len(filtered_laptops)} laptops")
        
        # If no laptops left after filtering, return a small portion of the original dataset
        if not filtered_laptops and self.laptops:
            logger.warning("No laptops left after filtering, returning a subset of all laptops")
            return self.laptops[:min(5, len(self.laptops))]
        
        return filtered_laptops

    def _get_laptop_embeddings(self, laptops: List[Dict]) -> List[np.ndarray]:
        """
        Create embeddings for laptop descriptions
        """
        descriptions = [self._format_laptop_description(laptop) for laptop in laptops]
        return self.model.encode(descriptions)

    def _extract_features_from_input(self, user_input: str) -> Dict:
        """
        Extract feature preferences from user input
        Returns a dictionary of features and their values
        """
        features = {}
        
        # Check for touchscreen
        if re.search(r'\b(?:touch|touchscreen)\b', user_input.lower()):
            features['touchscreen'] = True
        
        # Check for backlit keyboard
        if re.search(r'\b(?:backlit|lit keyboard|keyboard lighting)\b', user_input.lower()):
            features['backlit_keyboard'] = True
        
        # Check for numeric keypad
        if re.search(r'\b(?:numeric|numpad|number pad|keypad)\b', user_input.lower()):
            features['numeric_keyboard'] = True
        
        # Check for bluetooth
        if re.search(r'\bbluetooth\b', user_input.lower()):
            features['bluetooth'] = True
        
        # Check for battery life
        battery_match = re.search(r'(?:battery|battery life|long battery|last\w*\s+\d+\s+hours)', user_input.lower())
        if battery_match:
            features['battery_life'] = True
        
        return features

    def _extract_ports_from_input(self, user_input: str) -> Dict:
        """
        Extract port preferences from user input
        Returns a dictionary of ports and their values
        """
        ports = {}
        
        # Check for USB-C
        if re.search(r'\b(?:usb-c|usb c|type-c|type c)\b', user_input.lower()):
            ports['usb_c'] = True
        
        # Check for HDMI
        if re.search(r'\bhdmi\b', user_input.lower()):
            ports['hdmi'] = True
        
        # Check for Ethernet
        if re.search(r'\b(?:ethernet|lan|rj45|network port)\b', user_input.lower()):
            ports['ethernet'] = True
        
        # Check for Thunderbolt
        if re.search(r'\b(?:thunderbolt)\b', user_input.lower()):
            ports['thunderbolt'] = True
        
        # Check for Display Port
        if re.search(r'\b(?:displayport|display port)\b', user_input.lower()):
            ports['display_port'] = True
        
        return ports

    def _parse_size_preference(self, user_input: str) -> List[Union[int, str]]:
        """
        Parse screen size preferences from user input
        Returns a list of sizes or size ranges
        """
        sizes = []
        
        # Look for size descriptions first
        if re.search(r'\b(?:small|compact|portable)\b', user_input.lower()):
            sizes.extend([13, 14])
        elif re.search(r'\b(?:medium|standard)\b', user_input.lower()):
            sizes.extend([15, 15.6])
        elif re.search(r'\b(?:large|big|desktop replacement)\b', user_input.lower()):
            sizes.extend([16, 17])
        
        # If no descriptive sizes, look for specific measurements
        if not sizes:
            # Extract exact sizes like "13 inch", "15.6\"", etc.
            size_matches = re.findall(r'(\d+(\.\d+)?)["\s]*(?:inch|"|inches)?', user_input)
            for match in size_matches:
                try:
                    sizes.append(float(match[0]))
                except ValueError:
                    continue
            
            # Look for size ranges like "13-15 inch"
            range_matches = re.findall(r'(\d+(\.\d+)?)\s*-\s*(\d+(\.\d+)?)["\s]*(?:inch|"|inches)?', user_input)
            for match in range_matches:
                try:
                    sizes.append(f"{match[0]}-{match[2]}")
                except (ValueError, IndexError):
                    continue
        
        return sizes

    def _extract_brands_from_input(self, user_input: str) -> List[str]:
        """
        Extract brand preferences from user input
        Returns a list of brand names
        """
        brands = []
        common_brands = [
            "dell", "lenovo", "hp", "asus", "acer", "apple", "msi", 
            "samsung", "microsoft", "lg", "razer", "toshiba", "alienware",
            "huawei", "sony", "fujitsu", "gigabyte", "chuwi"
        ]
        
        # Convert input to lowercase for case-insensitive comparison
        user_input_lower = user_input.lower()
        
        # Search for brand mentions
        for brand in common_brands:
            if brand in user_input_lower:
                # Verify it's not part of another word
                if re.search(r'\b' + brand + r'\b', user_input_lower):
                    brands.append(brand)
        
        return brands

    def _extract_performance_level(self, user_input: str) -> str:
        """
        Determine the performance level preference from user input
        Returns: 'high', 'medium', or 'basic'
        """
        user_input_lower = user_input.lower()
        
        # High performance indicators
        high_perf = [
            "high performance", "powerful", "fast", "gaming", "rendering",
            "video editing", "3d modeling", "simulation", "high-end", "top spec",
            "best performance", "fastest", "i7", "i9", "ryzen 7", "ryzen 9"
        ]
        
        # Medium performance indicators
        medium_perf = [
            "medium performance", "balanced", "mid-range", "moderate",
            "good performance", "decent", "i5", "ryzen 5"
        ]
        
        # Basic performance indicators
        basic_perf = [
            "basic", "budget", "entry level", "simple tasks", "browsing",
            "office work", "light use", "casual", "everyday", "i3", "celeron"
        ]
        
        # Count matches for each category
        high_count = sum(1 for term in high_perf if term in user_input_lower)
        medium_count = sum(1 for term in medium_perf if term in user_input_lower)
        basic_count = sum(1 for term in basic_perf if term in user_input_lower)
        
        # Determine the highest matching category
        if high_count > medium_count and high_count > basic_count:
            return "high"
        elif medium_count > basic_count:
            return "medium"
        else:
            return "basic"

    def _keyword_based_use_case(self, user_input: str) -> str:
        """
        Use keyword matching as a fallback for use case detection
        """
        user_input = user_input.lower()
        
        # Define keywords for each category
        keywords = {
            "gaming": ["gaming", "game", "play", "fps", "aaa", "shooter", "mmo", "rpg", "esports", "stream"],
            "business": ["business", "work", "office", "professional", "meetings", "presentation", "teams", "zoom"],
            "student": ["student", "school", "college", "university", "education", "study", "homework", "notes"],
            "design": ["design", "creative", "art", "photo", "video", "editing", "creator", "adobe", "illustrator", "photoshop"],
            "programming": ["programming", "coding", "development", "software", "code", "developer", "programming", "ide"],
            "portable": ["portable", "light", "travel", "thin", "lightweight", "carry", "commute", "mobility"],
            "entertainment": ["entertainment", "media", "movies", "streaming", "netflix", "videos", "watch", "content"],
            "content_creation": ["content", "creator", "youtube", "stream", "render", "production", "vlog"],
            "budget": ["budget", "cheap", "affordable", "inexpensive", "economical", "low cost", "value"],
            "premium": ["premium", "high-end", "luxury", "best", "top", "flagship", "expensive"],
            "workstation": ["workstation", "cad", "engineering", "simulation", "data science", "virtualization"],
            "ultrabook": ["ultrabook", "ultraportable", "thin and light", "premium build", "sleek"]
        }
        
        # Count keyword matches for each category
        category_scores = {category: 0 for category in keywords}
        
        for category, words in keywords.items():
            for word in words:
                # Use word boundary to match whole words
                matches = len(re.findall(r'\b' + word + r'\b', user_input))
                category_scores[category] += matches
                
        # Find the category with the highest score
        if max(category_scores.values()) > 0:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        # Default to "student" if no keywords match
        return "student"

    def _analyze_preferences(self, user_input: str) -> Dict:
        """
        Analyze user input for all possible preferences in one go
        """
        preferences = {}
        
        # Extract use case using embeddings first, then keywords as fallback
        user_embedding = self.model.encode(user_input)
        similarities = {
            use_case: cosine_similarity([user_embedding], [emb])[0][0]
            for use_case, emb in self.feature_embeddings.items()
        }
        most_relevant = max(similarities.items(), key=lambda x: x[1])
        
        # Use embedding if similarity is high enough, otherwise keyword matching
        if most_relevant[1] < 0.3:  # Threshold for low confidence
            preferences['use_case'] = self._keyword_based_use_case(user_input)
        else:
            preferences['use_case'] = most_relevant[0]
        
        # Extract screen size preferences
        size_pref = self._parse_size_preference(user_input)
        if size_pref:
            preferences['size'] = size_pref
        
        # Extract brand preferences
        brand_pref = self._extract_brands_from_input(user_input)
        if brand_pref:
            preferences['brand'] = brand_pref
        
        # Extract budget range
        budget_match = re.search(r'\b(?:budget|price|cost|spend|around|under|below|max)\b[^.]*?(\d[\d,.]*)', user_input, re.IGNORECASE)
        if budget_match:
            budget_input = budget_match.group(0)
            min_budget, max_budget = self._enhanced_parse_budget_range(budget_input)
            if min_budget is not None or max_budget is not None:
                preferences['budget'] = (min_budget, max_budget)
        
        # Extract feature preferences
        feature_pref = self._extract_features_from_input(user_input)
        if feature_pref:
            preferences['features'] = feature_pref
        
        # Extract port preferences
        ports_pref = self._extract_ports_from_input(user_input)
        if ports_pref:
            preferences['ports'] = ports_pref
        
        # Extract performance level
        preferences['performance'] = self._extract_performance_level(user_input)
        
        return preferences

    def _handle_price_refinement(self, user_input: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Handle user requests to adjust price range during refinement
        Returns: (filtered_laptops, response_message) or (None, None) if not a price request
        """
        price_input = user_input.lower()
        original_min, original_max = self.user_preferences.get('budget', (None, None))
        
        # Handle request to ignore price constraints
        if any(term in price_input for term in ["ignore price", "don't care about price", 
                                         "forget the price", "remove price", 
                                         "price doesn't matter", "no price limit"]):
            # Remove budget constraint
            if 'budget' in self.user_preferences:
                del self.user_preferences['budget']
            
            # Apply filters without budget
            filters = {k: v for k, v in self.user_preferences.items() if k != 'budget'}
            filtered_laptops = self._filter_laptops(filters)
            
            return filtered_laptops, "I've removed the price constraints. Here are some options across different price points:"
        
        # Handle cheaper request
        elif any(term in price_input for term in ["cheaper", "less expensive", "lower price", 
                                          "budget", "affordable", "cost less"]):
            new_min, new_max = None, None
            
            if original_max is not None:
                # Reduce max budget by 30%
                new_max = original_max * 0.7
                new_min = original_min  # Keep the original minimum if it exists
            elif original_min is not None:
                # If only min was set, set a max that's 30% above min
                new_max = original_min * 1.3
                new_min = None  # Remove the minimum to get cheaper options
            else:
                # If no budget was set, set a default max budget
                new_max = 600
                new_min = None
            
            self.user_preferences['budget'] = (new_min, new_max)
            
            # Apply the new budget filter
            filters = {}
            for key, value in self.user_preferences.items():
                if key != 'budget' and value:
                    filters[key] = value
            filters['budget'] = (new_min, new_max)
            
            filtered_laptops = self._filter_laptops(filters)
            
            if new_min is not None:
                return filtered_laptops, f"Looking for more affordable options between £{new_min:.0f} and £{new_max:.0f}:"
            else:
                return filtered_laptops, f"Looking for more affordable options under £{new_max:.0f}:"
        
        # Handle more expensive request
        elif any(term in price_input for term in ["expensive", "higher price", "premium", 
                                          "better", "high-end", "higher budget", 
                                          "more expensive", "higher quality"]):
            new_min, new_max = None, None
            
            if original_min is not None:
                # Increase min budget by 30%
                new_min = original_min * 1.3
                new_max = original_max  # Keep the original maximum if it exists
            elif original_max is not None:
                # If only max was set, set a min that's 70% of max
                new_min = original_max * 0.7
                new_max = None  # Remove the maximum to get more premium options
            else:
                # If no budget was set, set a default min budget
                new_min = 1000
                new_max = None
            
            self.user_preferences['budget'] = (new_min, new_max)
            
            # Apply the new budget filter
            filters = {}
            for key, value in self.user_preferences.items():
                if key != 'budget' and value:
                    filters[key] = value
            filters['budget'] = (new_min, new_max)
            
            filtered_laptops = self._filter_laptops(filters)
            
            if new_max is not None:
                return filtered_laptops, f"Looking for more premium options between £{new_min:.0f} and £{new_max:.0f}:"
            else:
                return filtered_laptops, f"Looking for more premium options above £{new_min:.0f}:"
        
        # Handle specific price range request
        else:
            min_budget, max_budget = self._enhanced_parse_budget_range(price_input)
            
            if min_budget is not None or max_budget is not None:
                self.user_preferences['budget'] = (min_budget, max_budget)
                
                # Apply the new budget filter
                filters = {}
                for key, value in self.user_preferences.items():
                    if key != 'budget' and value:
                        filters[key] = value
                filters['budget'] = (min_budget, max_budget)
                
                filtered_laptops = self._filter_laptops(filters)
                
                if min_budget is not None and max_budget is not None:
                    return filtered_laptops, f"Looking for laptops between £{min_budget:.0f} and £{max_budget:.0f}:"
                elif min_budget is not None:
                    return filtered_laptops, f"Looking for laptops above £{min_budget:.0f}:"
                else:
                    return filtered_laptops, f"Looking for laptops under £{max_budget:.0f}:"
        
        return None, None  # Indicate that this wasn't a price-related query

    def _get_search_criteria_hash(self, filters: Dict, use_case: str) -> str:
        """
        Create a simple hash of search criteria to detect repeated searches
        """
        # Create a simple representation of the search criteria
        hash_components = [f"use_case={use_case}"]
        
        for key, value in sorted(filters.items()):
            if isinstance(value, (list, tuple)) and all(isinstance(v, (str, int, float)) for v in value):
                hash_components.append(f"{key}={','.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                hash_components.append(f"{key}={','.join(sorted(value.keys()))}")
            elif isinstance(value, tuple) and len(value) == 2:
                # Handle budget range
                min_val, max_val = value
                hash_components.append(f"{key}={min_val}_{max_val}")
            else:
                hash_components.append(f"{key}={value}")
        
        return "|".join(hash_components)

    def _get_recommendations(self, laptops: List[Dict], use_case: str, count: int = 3) -> List[Dict]:
        """
        Get laptop recommendations based on use case with random selection from top 15
        """
        if not laptops:
            return []
        
        # Create a hash of the current search criteria
        current_filters = {}
        for key, value in self.user_preferences.items():
            if key not in ['use_case']:  # Use case is handled separately
                current_filters[key] = value
        
        search_hash = self._get_search_criteria_hash(current_filters, use_case)
        logger.info(f"Search criteria hash: {search_hash}")
        
        # Check if this is the same search as before
        is_same_search = search_hash == self.last_search_criteria.get('hash', '')
        logger.info(f"Is same search: {is_same_search}")
        
        # If it's the same search and we already have the top 15, use those
        if is_same_search and self.top_similar_laptops:
            logger.info(f"Using previously computed top {len(self.top_similar_laptops)} laptops")
            # Pick random laptops from the top 15
            count = min(count, len(self.top_similar_laptops))
            if count == 0:
                return []
            
            # Randomly select unique laptops
            selected_indices = random.sample(range(len(self.top_similar_laptops)), count)
            recommendations = [self.top_similar_laptops[i] for i in selected_indices]
            
            logger.info(f"Randomly selected {count} laptops from previous top {len(self.top_similar_laptops)}")
            return recommendations
        
        # Otherwise, compute the top similar laptops
        laptop_embeddings = self._get_laptop_embeddings(laptops)
        use_case_embedding = self.feature_embeddings.get(use_case, self.feature_embeddings['student'])
        
        similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
        
        # Get top 15 indices but limit to available laptops
        top_count = min(15, len(laptops))
        if top_count == 0:
            return []
            
        top_indices = np.argsort(similarities)[-top_count:][::-1]
        
        # Store the top 15 laptops with their scores for future use
        self.top_similar_laptops = []
        for idx in top_indices:
            laptop = laptops[idx]
            brand = ""
            name = ""
            
            # Extract brand and name
            for table in laptop.get('tables', []):
                if table.get('title') == 'Product Details' and 'data' in table:
                    brand = table['data'].get('Brand', '')
                    name = table['data'].get('Name', '')
                    break
            
            if brand and name:
                # Extract price information
                price_value, price_string = self._extract_price_range(laptop)
                
                # Get key specifications for this laptop
                key_specs = self._get_key_specs(laptop)
                
                self.top_similar_laptops.append({
                    'brand': brand,
                    'name': name,
                    'specs': self._format_laptop_description(laptop),
                    'price': price_string if price_string else "Price not available",
                    'key_specs': key_specs,
                    'similarity_score': similarities[idx]
                })
        
        # Store the search criteria hash
        self.last_search_criteria = {
            'hash': search_hash,
            'timestamp': time.time()  # If we want to expire cached results after some time
        }
        
        logger.info(f"Computed new top {len(self.top_similar_laptops)} laptops")
        
        # Randomly select from the top 15
        count = min(count, len(self.top_similar_laptops))
        if count == 0:
            return []
            
        selected_indices = random.sample(range(len(self.top_similar_laptops)), count)
        recommendations = [self.top_similar_laptops[i] for i in selected_indices]
        
        logger.info(f"Randomly selected {count} laptops from new top {len(self.top_similar_laptops)}")
        return recommendations

    def _get_key_specs(self, laptop: Dict) -> Dict:
        """
        Extract key specifications from a laptop for quick comparison
        """
        key_specs = {}
        
        # Processor
        for table in laptop.get('tables', []):
            if table.get('title') == 'Specs' and 'data' in table:
                processor_brand = table['data'].get('Processor Brand', '')
                processor_name = table['data'].get('Processor Name', '')
                if processor_brand and processor_name:
                    key_specs['Processor'] = f"{processor_brand} {processor_name}"
                
                # Graphics
                graphics = table['data'].get('Graphics Card', '')
                if graphics:
                    key_specs['Graphics'] = graphics
                
                # RAM
                memory = table['data'].get('Memory Installed', '')
                if memory:
                    key_specs['RAM'] = memory
                
                # Storage
                storage = table['data'].get('Storage', '')
                if storage:
                    key_specs['Storage'] = storage
        
        # Screen
        for table in laptop.get('tables', []):
            if table.get('title') == 'Screen' and 'data' in table:
                screen_size = table['data'].get('Size', '')
                screen_resolution = table['data'].get('Resolution', '')
                if screen_size:
                    key_specs['Screen'] = screen_size
                    if screen_resolution:
                        key_specs['Screen'] += f" {screen_resolution}"
                
                refresh_rate = table['data'].get('Refresh Rate', '')
                if refresh_rate:
                    key_specs['Refresh Rate'] = refresh_rate
        
        # Battery
        for table in laptop.get('tables', []):
            if (table.get('title') == 'Features' or table.get('title') == 'Misc') and 'data' in table:
                battery = table['data'].get('Battery Life', '')
                if battery:
                    key_specs['Battery'] = battery
        
        # Weight
        for table in laptop.get('tables', []):
            if table.get('title') == 'Product Details' and 'data' in table:
                weight = table['data'].get('Weight', '')
                if weight:
                    key_specs['Weight'] = weight
        
        return key_specs

    def _get_laptop_name(self, laptop: Dict) -> str:
        """Helper to get a laptop's full name (brand + name)"""
        brand = ""
        name = ""
        
        for table in laptop.get('tables', []):
            if table.get('title') == 'Product Details' and 'data' in table:
                brand = table['data'].get('Brand', '')
                name = table['data'].get('Name', '')
                break
        
        return f"{brand} {name}".strip()

    def process_input(self, user_input: str) -> Dict:
        """
        Process user input and return appropriate response
        """
        response = {
            "message": "",
            "recommendations": [],
            "next_question": None,
            "detected_preferences": {}
        }

        # Check for restart or new search request
        if any(term in user_input.lower() for term in ["restart", "start over", "new search", "new recommendation"]):
            self.reset_conversation()
            response["message"] = "Let's start over. " + self.questions["initial"]
            self.conversation_state = "initial"
            return response

        # Process based on conversation state
        if self.conversation_state == "initial":
            # Analyze initial input comprehensively
            preferences = self._analyze_preferences(user_input)
            self.user_preferences.update(preferences)
            
            # Provide information about detected preferences
            use_case = self.user_preferences.get('use_case', '')
            response["detected_preferences"] = preferences
            response["message"] = f"I understand you're looking for a {use_case} laptop."
            
            # Add details about detected preferences
            if 'brand' in preferences:
                response["message"] += f" You mentioned {', '.join(preferences['brand'])} brand(s)."
            
            if 'size' in preferences:
                response["message"] += f" You're interested in {', '.join(str(s) for s in preferences['size'])}\" screen size."
            
            if 'budget' in preferences:
                min_budget, max_budget = preferences['budget']
                if min_budget is not None and max_budget is not None:
                    response["message"] += f" Your budget is between £{min_budget:.0f} and £{max_budget:.0f}."
                elif min_budget is not None:
                    response["message"] += f" You're looking to spend above £{min_budget:.0f}."
                else:
                    response["message"] += f" You're looking to spend under £{max_budget:.0f}."
            
            if 'performance' in preferences:
                response["message"] += f" You need {preferences['performance']} performance."
            
            # Move to ask about purpose first, then size, then budget as the 3rd question
            self.conversation_state = "purpose"
            response["next_question"] = self.questions["purpose"]
        
        elif self.conversation_state == "purpose":
            # Extract purpose from input and update preferences
            purpose_input = user_input.lower()
            
            # Map common keywords to use cases
            purpose_mapping = {
                "gaming": ["gaming", "game", "play", "fps", "gamer"],
                "business": ["business", "work", "office", "professional"],
                "student": ["student", "school", "college", "university", "education", "study"],
                "design": ["design", "creative", "art", "photo", "video", "editing", "creator", "adobe"],
                "programming": ["programming", "coding", "development", "software", "code", "developer"]
            }
            
            # Determine purpose from input
            detected_purpose = None
            for purpose, keywords in purpose_mapping.items():
                if any(keyword in purpose_input for keyword in keywords):
                    detected_purpose = purpose
                    break
            
            if detected_purpose:
                self.user_preferences['use_case'] = detected_purpose
                response["message"] = f"Great! I'll focus on laptops suitable for {detected_purpose}."
            else:
                # If no specific purpose detected, keep the existing use case or default to student
                if 'use_case' not in self.user_preferences:
                    self.user_preferences['use_case'] = 'student'
                response["message"] = f"I'll focus on finding a suitable laptop for your needs."
            
            # Move to size question next
            self.conversation_state = "size"
            response["next_question"] = self.questions["size"]
        
        elif self.conversation_state == "size":
            # Extract screen size preference
            size_terms = {"small": [11, 12, 13, 14], "medium": [15, 15.6], "large": [16, 17, 17.3]}
            
            # Check for size descriptors first
            size_input = user_input.lower()
            size_pref = []
            
            for descriptor, sizes in size_terms.items():
                if descriptor in size_input:
                    size_pref.extend(sizes)
                    break
            
            # If no descriptor, check for specific sizes
            if not size_pref:
                size_pref = self._parse_size_preference(user_input)
            
            if size_pref:
                self.user_preferences['size'] = size_pref
                size_desc = 'small' if any(s <= 14 for s in size_pref if isinstance(s, (int, float))) else 'large' if any(s >= 16 for s in size_pref if isinstance(s, (int, float))) else 'medium'
                response["message"] = f"Got it, you prefer a {size_desc} laptop with {', '.join(str(s) for s in size_pref)}\" screen size."
            else:
                response["message"] = "I'll consider laptops with various screen sizes for you."
            
            # Now move to budget question as the 3rd question
            self.conversation_state = "budget"
            response["next_question"] = self.questions["budget"]
        
        elif self.conversation_state == "budget":
            # Enhanced budget parsing
            budget_input = user_input.lower()
            
            # Check if user is declining to provide a budget
            if any(term in budget_input for term in ["don't know", "not sure", "any budget", "doesn't matter", "don't care", "skip"]):
                response["message"] = "No problem. I'll show you options across different price points."
                # Move to next question
                self.conversation_state = "brand"
                response["next_question"] = self.questions["brand"]
                return response
            
            # Try to extract budget
            min_budget, max_budget = self._enhanced_parse_budget_range(budget_input)
            
            if min_budget is not None or max_budget is not None:
                self.user_preferences['budget'] = (min_budget, max_budget)
                
                if min_budget is not None and max_budget is not None:
                    response["message"] = f"I'll look for laptops between £{min_budget:.0f} and £{max_budget:.0f}."
                elif min_budget is not None:
                    response["message"] = f"I'll look for laptops over £{min_budget:.0f}."
                else:
                    response["message"] = f"I'll look for laptops under £{max_budget:.0f}."
                    
                # Move to next question
                self.conversation_state = "brand"
                response["next_question"] = self.questions["brand"]
            else:
                # If we couldn't parse a budget, ask again
                response["message"] = "I'm having trouble understanding your budget. Could you please specify an approximate price range, like '£500-£800' or 'under £1000'?"
                # Stay in budget state until we get a valid response
                self.conversation_state = "budget"
                response["next_question"] = None  # We already asked in the message
            
            return response
        
        elif self.conversation_state == "brand":
            # Extract brand preferences
            if any(term in user_input.lower() for term in ["no", "none", "any", "no preference", "doesn't matter"]):
                response["message"] = "Got it, I won't filter by brand."
            else:
                brands = self._extract_brands_from_input(user_input)
                if brands:
                    self.user_preferences['brand'] = brands
                    response["message"] = f"I'll focus on {', '.join(brands)} laptops."
                else:
                    response["message"] = "I couldn't identify specific brand preferences. I'll show options from various manufacturers."
            
            # Move to features question
            self.conversation_state = "features"
            response["next_question"] = self.questions["features"]
        
        elif self.conversation_state == "features":
            # Extract feature preferences
            features = self._extract_features_from_input(user_input)
            ports = self._extract_ports_from_input(user_input)
            
            if features:
                self.user_preferences['features'] = features
                feature_list = ", ".join(features.keys())
                response["message"] = f"I'll look for laptops with {feature_list}."
            else:
                response["message"] = "No specific features noted."
            
            if ports:
                self.user_preferences['ports'] = ports
                if features:
                    response["message"] += f" And I'll ensure they have the requested ports: {', '.join(ports.keys())}."
                else:
                    response["message"] = f"I'll focus on laptops with the requested ports: {', '.join(ports.keys())}."
            
            # Move to performance question
            self.conversation_state = "performance"
            response["next_question"] = self.questions["performance"]
        
        elif self.conversation_state == "performance":
            # Extract performance level
            if any(term in user_input.lower() for term in ["high", "powerful", "gaming", "top", "best"]):
                self.user_preferences['performance'] = "high"
                response["message"] = "I'll look for high-performance laptops with powerful processors and graphics."
            elif any(term in user_input.lower() for term in ["medium", "mid", "balanced", "moderate"]):
                self.user_preferences['performance'] = "medium"
                response["message"] = "I'll look for mid-range laptops with good balanced performance."
            else:
                self.user_preferences['performance'] = "basic"
                response["message"] = "I'll focus on laptops with basic performance suitable for everyday tasks."
            
            # Generate recommendations based on all preferences
            filters = {}
            
            if 'size' in self.user_preferences:
                filters['size'] = self.user_preferences['size']
            
            if 'brand' in self.user_preferences:
                filters['brand'] = self.user_preferences['brand']
            
            if 'budget' in self.user_preferences:
                filters['budget'] = self.user_preferences['budget']
            
            if 'features' in self.user_preferences:
                filters['features'] = self.user_preferences['features']
            
            if 'ports' in self.user_preferences:
                filters['ports'] = self.user_preferences['ports']
            
            if 'performance' in self.user_preferences:
                filters['performance'] = self.user_preferences['performance']
            
            filtered_laptops = self._filter_laptops(filters)
            
            if filtered_laptops:
                # Get recommendations based on use case and filtered laptops
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
                
                if recommendations:
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
                    response["message"] += " Here are your personalized recommendations:"
                else:
                    response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                    # Relax some constraints
                    relaxed_filters = {k: v for k, v in filters.items() if k not in ['features', 'ports']}
                    relaxed_laptops = self._filter_laptops(relaxed_filters)
                    recommendations = self._get_recommendations(relaxed_laptops, self.user_preferences.get('use_case', 'student'), 3)
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
            else:
                response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                # Try with minimal filtering
                minimal_filters = {}
                if 'budget' in filters:
                    minimal_filters['budget'] = filters['budget']
                if 'brand' in filters:
                    minimal_filters['brand'] = filters['brand']
                
                minimal_laptops = self._filter_laptops(minimal_filters)
                recommendations = self._get_recommendations(minimal_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            self.conversation_state = "refine"
            response["next_question"] = "Would you like to refine your search or see more options?"
        
        elif self.conversation_state == "refine":
            # First check if it's a price-related refinement
            filtered_laptops, price_message = self._handle_price_refinement(user_input)
            
            if filtered_laptops is not None and price_message is not None:
                # It was a price-related query
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
                response["message"] = price_message
                return response
            
            # Handle requests for more options
            if any(term in user_input.lower() for term in ["more", "additional", "other", "alternative", "show more"]):
                # Show more recommendations
                use_case = self.user_preferences.get('use_case', 'student')
                filters = {}
                
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                if 'features' in self.user_preferences:
                    filters['features'] = self.user_preferences['features']
                
                if 'ports' in self.user_preferences:
                    filters['ports'] = self.user_preferences['ports']
                
                filtered_laptops = self._filter_laptops(filters)
                
                # Use same search criteria to get different random selections
                recommendations = self._get_recommendations(filtered_laptops, use_case, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
                response["message"] = "Here are some alternative options that might interest you:"
            
            # Handle specific refinement requests
            elif any(term in user_input.lower() for term in ["smaller", "more portable", "lighter", "portable"]):
                # Find smaller, more portable options
                smaller_sizes = []
                if 'size' in self.user_preferences:
                    current_sizes = self.user_preferences['size']
                    for size in current_sizes:
                        try:
                            if isinstance(size, (int, float)) and size > 14:
                                smaller_sizes.extend([13, 14])
                            elif isinstance(size, str) and '-' in size:
                                min_size, max_size = map(float, size.split('-'))
                                if max_size > 14:
                                    smaller_sizes.extend([13, 14])
                        except (ValueError, TypeError):
                            pass
                
                if not smaller_sizes:
                    smaller_sizes = [13, 14]
                
                self.user_preferences['size'] = smaller_sizes
                response["message"] = "Looking for smaller, more portable laptops:"
                
                # Apply the new size filter
                filters = {}
                filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, 'portable', 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            elif any(term in user_input.lower() for term in ["larger", "bigger screen", "larger display"]):
                # Find laptops with larger screens
                larger_sizes = []
                if 'size' in self.user_preferences:
                    current_sizes = self.user_preferences['size']
                    for size in current_sizes:
                        try:
                            if isinstance(size, (int, float)) and size < 15:
                                larger_sizes.extend([15.6, 16, 17])
                            elif isinstance(size, str) and '-' in size:
                                min_size, max_size = map(float, size.split('-'))
                                if min_size < 15:
                                    larger_sizes.extend([15.6, 16, 17])
                        except (ValueError, TypeError):
                            pass
                
                if not larger_sizes:
                    larger_sizes = [15.6, 16, 17]
                
                self.user_preferences['size'] = larger_sizes
                response["message"] = "Looking for laptops with larger screens:"
                
                # Apply the new size filter
                filters = {}
                filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            elif any(term in user_input.lower() for term in ["gaming", "games", "play games"]):
                # Find gaming laptops
                self.user_preferences['use_case'] = 'gaming'
                self.user_preferences['performance'] = 'high'
                
                response["message"] = "Looking for gaming laptops with high performance:"
                
                # Apply gaming filters
                filters = {}
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                filters['performance'] = 'high'
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, 'gaming', 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            elif any(term in user_input.lower() for term in ["business", "work", "office", "professional"]):
                # Find business laptops
                self.user_preferences['use_case'] = 'business'
                
                response["message"] = "Looking for business laptops with professional features:"
                
                # Apply business filters
                filters = {}
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, 'business', 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            else:
                # Process as a new input to refine search
                new_preferences = self._analyze_preferences(user_input)
                
                # Update existing preferences with new ones
                self.user_preferences.update(new_preferences)
                
                response["message"] = "I've updated your preferences. Here are new recommendations:"
                
                # Apply updated filters
                filters = {}
                
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                if 'features' in self.user_preferences:
                    filters['features'] = self.user_preferences['features']
                
                if 'ports' in self.user_preferences:
                    filters['ports'] = self.user_preferences['ports']
                
                if 'performance' in self.user_preferences:
                    filters['performance'] = self.user_preferences['performance']
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
        
        return response

    def reset_conversation(self):
        """
        Reset the conversation state and user preferences
        """
        self.conversation_state = "initial"
        self.user_preferences = {}
        self.last_recommendations = []
        self.top_similar_laptops = []
        self.last_search_criteria = {}

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