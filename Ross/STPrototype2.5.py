from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional, Union, Set
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from collections import defaultdict
from loguru import logger
import base64
from io import BytesIO

logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}")
# if you dont like the terminal printing of the logger, then remove the sys.stdout line
logger.add("..Sam/server_side/logs/API.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="API")

class LaptopRecommendationBot:
    def __init__(self, laptop_data: List[Dict] = None):
        """
        Initialize the chatbot with laptop data and load the sentence transformer model
        
        Args:
            laptop_data: List of dictionaries containing laptop information (optional)
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # If laptop_data is provided, use it; otherwise load from database
        self.laptops = laptop_data if laptop_data else self.load_from_database()
        
        # If no laptops were loaded, try a fallback method
        if not self.laptops:
            logger.warning("No laptops loaded from primary database method, trying fallback...")
            self.laptops = self.fallback_load_laptops()
        
        self.conversation_state = "initial"
        self.user_preferences = {}
        self.excluded_brands = set()  # Set of brands to exclude
        self.last_recommendations = []  # Store last recommendations for reference
        self.emphasized_features = []  # Features to emphasize in recommendations
        self.off_topic_counter = 0  # Counter for consecutive off-topic messages
        
        # Expanded predefined questions for gathering user preferences
        self.questions = {
            "initial": "What kind of laptop are you looking for? Please describe your needs in detail.",
            "budget": "What's your approximate budget range?",
            "purpose": "What will you primarily use the laptop for (e.g., gaming, work, studies, design)?",
            "size": "Do you have a preferred screen size (e.g., 13\", 14\", 15.6\", 16\", 17\")?",
            "brand": "Do you have any preferred brands? You can also mention brands you want to avoid.",
            "features": "Are there any specific features you need (e.g., touchscreen, backlit keyboard, long battery life)?",
            "performance": "How important is performance to you (e.g., high, medium, basic needs)?"
        }
        
        # Create reference embeddings for laptop-related topics to measure relevance
        self.laptop_topic_embeddings = self._create_laptop_topic_embeddings()
        
        # Threshold for topic relevance - adjustable as needed
        self.topic_relevance_threshold = 0.25
        
        # Create embeddings for predefined features and use cases
        self.feature_embeddings = self._create_feature_embeddings()

    def load_from_database(self, limit=10000) -> List[Dict]:
        """
        Load laptop data from PostgreSQL database with optimizations
        
        Args:
            limit: Maximum number of laptops to load (default: 10000)
        
        Returns:
            List of dictionaries containing laptop information in the same format as the JSON
        """
        conn = None
        cur = None
        try:
            # Try to use the imported db_access function
            try:
                conn, cur = get_db_connection()
                # print("Connected to database using DBAccess module!")
                # dont need this as, logging is set in the dbAccess class
            except NameError:
                # If import failed, connect directly
                # Try connecting to laptopchatbot database first (original one)
                try:
                    conn = psycopg2.connect(
                        database="laptopchatbot",  # Original database name
                        user="samuel",
                        host="86.19.219.159",
                        password="QwErTy1243!",
                        port=5432
                    )
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    print("Connected to 'laptopchatbot' database directly!")
                except Exception as db_err:
                    print(f"Could not connect to 'laptopchatbot': {str(db_err)}")
                    # Try persistence database as fallback
                    try:
                        #please create a .env!!!!!!!!!!!!!!
                        conn = psycopg2.connect(
                            database="persistence",  # Try another database name
                            user="samuel",
                            host="86.19.219.159",
                            password="QwErTy1243!",
                            port=5432
                        )
                        cur = conn.cursor(cursor_factory=RealDictCursor)
                        print("Connected to 'persistence' database directly!")
                    except Exception as db_err2:
                        # Last attempt with postgres default database to list available databases

                        # might not be needed, as there are no details or tables inside of this database, but can keep if you think is needed
                        try:
                            conn_temp = psycopg2.connect(
                                database="postgres",  # Default postgres database
                                user="samuel",
                                host="86.19.219.159",
                                password="QwErTy1243!",
                                port=5432
                            )
                            cur_temp = conn_temp.cursor()
                            cur_temp.execute("SELECT datname FROM pg_database;")
                            available_dbs = [row[0] for row in cur_temp.fetchall()]
                            cur_temp.close()
                            conn_temp.close()
                            
                            # Try connecting to the first available database that might be related
                            laptop_related_dbs = [db for db in available_dbs if 'laptop' in db.lower() or 'persistence' in db.lower()]
                            
                            if laptop_related_dbs:
                                db_to_try = laptop_related_dbs[0]
                                conn = psycopg2.connect(
                                    database=db_to_try,
                                    user="samuel",
                                    host="86.19.219.159",
                                    password="QwErTy1243!",
                                    port=5432
                                )
                                cur = conn.cursor(cursor_factory=RealDictCursor)
                                print(f"Connected to '{db_to_try}' database directly!")
                            else:
                                print(f"Available databases: {', '.join(available_dbs)}")
                                raise Exception("No suitable database found. Please specify the correct database name.")
                        except Exception as list_err:
                            print(f"Could not list available databases: {str(list_err)}")
                            raise
            
            logger.info("Connected to database successfully!")
            
            # Check if tables exist in this database
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            available_tables = [row['table_name'] for row in cur.fetchall()]
            print(f"Available tables: {', '.join(available_tables)}")
            
            if 'laptops' not in available_tables:
                raise Exception("The 'laptops' table does not exist in this database!")
            
            # Get limited number of laptop models - add LIMIT clause
            cur.execute(f"SELECT model FROM laptops LIMIT {limit}")
            models = cur.fetchall()
            
            if not models:
                logger.error("No laptop models found in database")
                return []
                
            logger.info(f"Loading {len(models)} laptop models (limited from total)")
            
            # Create a list to store all laptop data in the same format as the JSON
            laptops = []
            total_models = len(models)
            
            # Use a more efficient approach with batch processing
            models_list = [model_row['model'] for model_row in models]
            
            # Create a mapping of models for faster lookups
            laptops_dict = {model: {'tables': []} for model in models_list}
            
            # Batch query for Product Details
            logger.info("Loading product details...")
            placeholders = ','.join(['%s'] * len(models_list))
            cur.execute(f"""
                SELECT model as "Name", brand as "Brand", weight as "Weight"
                FROM laptops WHERE model IN ({placeholders})
            """, tuple(models_list))
            
            for row in cur.fetchall():
                model = row["Name"]
                if model in laptops_dict:
                    laptops_dict[model]['tables'].append({
                        'title': 'Product Details',
                        'data': dict(row)
                    })
            
            # Check if the screen table exists
            if 'screen' in available_tables:
                # Batch query for Screen Details
                logger.info("Loading screen details...")
                cur.execute(f"""
                    SELECT s.laptop_model, s.screen_resolution as "Resolution", 
                           s.refresh_rate as "Refresh Rate", s.touch_screen as "Touchscreen", 
                           l.screen_size as "Size"
                    FROM screen s
                    JOIN laptops l ON s.laptop_model = l.model
                    WHERE s.laptop_model IN ({placeholders})
                """, tuple(models_list))
                
                for row in cur.fetchall():
                    model = row.pop('laptop_model')
                    if model in laptops_dict:
                        laptops_dict[model]['tables'].append({
                            'title': 'Screen',
                            'data': dict(row)
                        })
            else:
                logger.warning("Screen table not found, skipping...")
            
            # Check if the cpu table exists
            if 'cpu' in available_tables:
                # Batch query for Processor Details
                logger.info("Loading processor details...")
                cur.execute(f"""
                    SELECT laptop_model, brand as "Brand", model as "Name"
                    FROM cpu WHERE laptop_model IN ({placeholders})
                """, tuple(models_list))
                
                for row in cur.fetchall():
                    model = row.pop('laptop_model')
                    if model in laptops_dict:
                        laptops_dict[model]['tables'].append({
                            'title': 'Processor',
                            'data': dict(row)
                        })
            else:
                logger.warning("CPU table not found, skipping...")
            
            # Check if required tables exist for misc details
            gpu_exists = 'gpu' in available_tables
            storage_exists = 'storage' in available_tables
            
            # Batch query for Misc Details (conditionally based on table existence)
            logger.info("Loading misc details...")
            query_parts = [
                "SELECT l.model as laptop_model",
                "l.memory_installed as \"Memory Installed\"",
                "l.operating_system as \"Operating System\"",
                "l.battery_life as \"Battery Life\""
            ]
            
            join_parts = ["FROM laptops l"]
            
            if gpu_exists:
                query_parts.insert(1, "g.model as \"Graphics Card\"")
                join_parts.append("LEFT JOIN gpu g ON l.model = g.laptop_model")
            
            if storage_exists:
                query_parts.insert(-1, "s.storage_amount || ' ' || s.storage_type as \"Storage\"")
                join_parts.append("LEFT JOIN storage s ON l.model = s.laptop_model")
            
            misc_query = f"""
                {', '.join(query_parts)}
                {' '.join(join_parts)}
                WHERE l.model IN ({placeholders})
            """
            
            cur.execute(misc_query, tuple(models_list))
            
            for row in cur.fetchall():
                model = row.pop('laptop_model')
                if model in laptops_dict:
                    laptops_dict[model]['tables'].append({
                        'title': 'Misc',
                        'data': dict(row)
                    })
            
            # Check if the features table exists
            if 'features' in available_tables:
                # Batch query for Features
                logger.info("Loading features...")
                cur.execute(f"""
                    SELECT laptop_model, backlit_keyboard as "Backlit Keyboard", 
                           num_pad as "Numeric Keyboard", bluetooth as "Bluetooth"
                    FROM features
                    WHERE laptop_model IN ({placeholders})
                """, tuple(models_list))
                
                for row in cur.fetchall():
                    model = row.pop('laptop_model')
                    if model in laptops_dict:
                        laptops_dict[model]['tables'].append({
                            'title': 'Features',
                            'data': dict(row)
                        })
            else:
                logger.warning("Features table not found, skipping...")
            
            # Check if the ports table exists
            if 'ports' in available_tables:
                # Batch query for Ports
                logger.info("Loading ports...")
                cur.execute(f"""
                    SELECT laptop_model, hdmi as "HDMI", ethernet as "Ethernet (RJ45)", 
                           thunderbolt as "Thunderbolt", type_c as "USB Type-C"
                    FROM ports
                    WHERE laptop_model IN ({placeholders})
                """, tuple(models_list))
                
                for row in cur.fetchall():
                    model = row.pop('laptop_model')
                    if model in laptops_dict:
                        laptops_dict[model]['tables'].append({
                            'title': 'Ports',
                            'data': dict(row)
                        })
            else:
                logger.warning("Ports table not found, skipping...")
                
            # Check if the prices table exists
            if 'prices' in available_tables:
                # Batch query for Prices
                logger.info("Loading prices...")
                cur.execute(f"""
                    SELECT laptop_model, price, source_url
                    FROM prices
                    WHERE laptop_model IN ({placeholders})
                """, tuple(models_list))
                
                for row in cur.fetchall():
                    model = row.pop('laptop_model')
                    price = row.get('price')
                    url = row.get('source_url')
                    
                    if model in laptops_dict:
                        # Check if Prices table already exists
                        prices_table = None
                        for table in laptops_dict[model]['tables']:
                            if table['title'] == 'Prices':
                                prices_table = table
                                break
                        
                        # If prices table doesn't exist, create it
                        if not prices_table:
                            prices_table = {
                                'title': 'Prices',
                                'data': []
                            }
                            laptops_dict[model]['tables'].append(prices_table)
                        
                        # Add price data
                        if isinstance(prices_table['data'], list):
                            prices_table['data'].append({
                                'shop_url': url,
                                'price': f"£{price}" if price else "N/A"
                            })
            
            # Check if the images table exists and try to load images if possible
            if 'images' in available_tables:
                logger.info("Checking image table structure...")
                try:
                    # First check if the image columns exist
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'images'
                    """)
                    image_columns = [col['column_name'] for col in cur.fetchall()]
                    logger.info(f"Available image columns: {', '.join(image_columns)}")
                    
                    # Only proceed if necessary columns exist
                    if 'laptop_model' in image_columns:
                        image_query = f"SELECT laptop_model"
                        if 'image_data' in image_columns:
                            image_query += ", image_data"
                        if 'image_type' in image_columns:
                            image_query += ", image_type"
                        elif 'image_format' in image_columns:  # Try alternative column name
                            image_query += ", image_format as image_type"
                        if 'image_url' in image_columns:  # Alternative: direct URL instead of binary data
                            image_query += ", image_url"
                            
                        image_query += f" FROM images WHERE laptop_model IN ({placeholders})"
                        
                        logger.info("Loading images with available columns...")
                        cur.execute(image_query, tuple(models_list))
                        
                        for row in cur.fetchall():
                            model = row.pop('laptop_model')
                            if model in laptops_dict:
                                # Check if we have binary image data
                                if 'image_data' in row and row['image_data']:
                                    image_data = row['image_data']
                                    image_type = row.get('image_type', 'png')
                                    
                                    # Convert image data to base64 for API use
                                    try:
                                        if isinstance(image_data, bytes):
                                            base64_image = base64.b64encode(image_data).decode('utf-8')
                                            image_url = f"data:image/{image_type};base64,{base64_image}"
                                            
                                            # Add image to laptop data
                                            image_table = {
                                                'title': 'Images',
                                                'data': {'url': image_url}
                                            }
                                            laptops_dict[model]['tables'].append(image_table)
                                    except Exception as img_err:
                                        logger.error(f"Error processing image data for {model}: {str(img_err)}")
                                
                                # Check if we have direct image URL instead
                                elif 'image_url' in row and row['image_url']:
                                    image_url = row['image_url']
                                    # Add image to laptop data
                                    image_table = {
                                        'title': 'Images',
                                        'data': {'url': image_url}
                                    }
                                    laptops_dict[model]['tables'].append(image_table)
                    else:
                        logger.warning("Images table exists but doesn't have required columns, skipping...")
                        
                except Exception as img_err:
                    logger.warning(f"Error loading images, continuing without images: {str(img_err)}")
            
            # Convert dictionary back to list
            laptops = list(laptops_dict.values())
            
            logger.info(f"Successfully loaded {len(laptops)} laptops from database")
            return laptops
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            # Return an empty list instead of failing completely
            return []
        finally:
            # Clean up database connection
            if conn and cur:
                try:
                    # Try to use the imported release function first
                    try:
                        release_db_connection(conn, cur)
                        logger.info("Database connection released using DBAccess module.")
                    except NameError:
                        # If import failed, close directly
                        cur.close()
                        conn.close()
                        logger.info("Database connection closed directly.")
                except Exception as close_err:
                    logger.error(f"Error closing database connection: {str(close_err)}")
    def fallback_load_laptops(self) -> List[Dict]:
        """
        Fallback method to load laptop data if the main database connection fails
        Uses a more basic approach with fewer joins to increase chances of success
        """
        conn = None
        cur = None
        try:
            # Try to connect to the database
            try:
                conn = psycopg2.connect(
                    database="laptopchatbot",
                    user="samuel",
                    host="86.19.219.159",
                    password="QwErTy1243!",
                    port=5432
                )
                cur = conn.cursor(cursor_factory=RealDictCursor)
                logger.info("Connected to database in fallback mode!")
            except Exception as db_err:
                logger.error(f"Could not connect to database in fallback mode: {str(db_err)}")
                return []
            
            # Get all laptops with minimal data
            logger.info("Loading basic laptop data in fallback mode...")
            cur.execute("""
                SELECT model as "Name", brand as "Brand", weight as "Weight",
                       memory_installed as "Memory", operating_system as "OS", 
                       screen_size as "ScreenSize"
                FROM laptops
                LIMIT 5000
            """)
            
            laptops_data = cur.fetchall()
            if not laptops_data:
                logger.error("No laptop data found in fallback mode")
                return []
            
            # Create laptop objects in the same format as the main function
            laptops = []
            for row in laptops_data:
                laptop = {
                    'tables': [
                        {
                            'title': 'Product Details',
                            'data': {
                                'Name': row.get('Name', ''),
                                'Brand': row.get('Brand', '')
                            }
                        },
                        {
                            'title': 'Misc',
                            'data': {
                                'Memory Installed': row.get('Memory', ''),
                                'Operating System': row.get('OS', '')
                            }
                        },
                        {
                            'title': 'Screen',
                            'data': {
                                'Size': row.get('ScreenSize', '')
                            }
                        }
                    ]
                }
                laptops.append(laptop)
            
            logger.info(f"Successfully loaded {len(laptops)} laptops in fallback mode")
            return laptops
            
        except Exception as e:
            logger.error(f"Error in fallback laptop loading: {str(e)}")
            return []
        finally:
            if conn and cur:
                try:
                    cur.close()
                    conn.close()
                    logger.info("Fallback database connection closed")
                except Exception:
                    pass    
    def _create_laptop_topic_embeddings(self) -> np.ndarray:
        """
        Create reference embeddings for laptop-related topics to measure conversation relevance
        """
        laptop_topics = [
            "computer specifications laptop hardware components",
            "laptops notebook computers portable computing devices",
            "laptop brands manufacturers Dell HP Lenovo Asus Acer Apple",
            "laptop specs processor CPU RAM memory storage SSD HDD graphics card GPU",
            "laptop features backlit keyboard touchscreen battery life ports connectivity",
            "laptop screen display resolution refresh rate size inches",
            "laptop performance speed benchmark gaming productivity workstation",
            "laptop price budget cost range affordable premium",
            "laptop recommendations suggestions best laptops for specific uses",
            "laptop configuration customization options",
            "laptop weight portability ultrabook thin light travel",
            "laptop operating system Windows macOS Linux Chrome OS",
            "laptop reviews ratings comparison shopping guide"
        ]
        
        # Encode each topic and average them for a comprehensive topic embedding
        topic_embeddings = [self.model.encode(topic) for topic in laptop_topics]
        return np.mean(topic_embeddings, axis=0)# This is the updated LaptopRecommendationBot with enhanced features

    def _create_feature_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Create embeddings for predefined features and use cases with enhanced descriptions
        """
        features = {
            "gaming": """high-performance gaming laptop with dedicated graphics card for AAA games, 
                     high refresh rate display, powerful processor, gaming aesthetics, RGB lighting,
                     excellent cooling, high-end GPU for modern games, gaming laptop""",
            
            "business": """professional laptop with good battery life, 
                       portable design, windows professional, business laptop, work laptop,
                       productivity features, professional appearance, office work""",
            
            "student": """affordable laptop for students with good battery life, 
                      portable, sufficient storage for documents, budget-friendly,
                      college laptop, university laptop, school laptop, student laptop,
                      education laptop, studying, homework, assignments""",
            
            "design": """laptop for designers with high-resolution display, color accuracy, 
                     powerful graphics capabilities, creative work, graphic design,
                     photo editing, video editing, art creation, design laptop, creative laptop""",
            
            "programming": """laptop for coding with good processor, sufficient RAM, 
                         comfortable keyboard and display, development laptop, coding laptop,
                         software engineering, programming laptop, computer science,
                         software development, web development, app development""",
            
            "portable": """lightweight laptop with long battery life, 
                       compact size, good build quality, travel laptop, thin and light,
                       ultraportable, mobility, on-the-go, commuting, travel""",
            
            "entertainment": """laptop for media consumption with high-quality display, 
                           good speakers, immersive experience, movie watching, music, streaming,
                           content consumption, entertainment laptop, multimedia laptop""",
            
            "content_creation": """powerful laptop for content creators, video editing, 
                             rendering, 3D modeling, animation, high-performance processor,
                             professional graphics, large display, content creation laptop""",
            
            "budget": """affordable laptop with good value, basic performance,
                    economical, budget-friendly, cost-effective, entry-level laptop,
                    inexpensive laptop, low-cost computing, basic tasks""",
            
            "premium": """high-end laptop with premium build quality, top specifications,
                     luxury design, excellent display, premium materials, flagship laptop,
                     premium laptop, high-performance, top-tier device"""
        }
        
        return {key: self.model.encode(desc) for key, desc in features.items()}

    def _format_laptop_description(self, laptop: Dict) -> str:
        """
        Create a detailed description string from laptop specifications
        with emphasized features when specified
        """
        tables = laptop.get('tables', [])
        details = {}
        
        # Extract relevant information from nested structure
        for table in tables:
            if 'data' in table:
                if isinstance(table['data'], dict):
                    details.update(table['data'])
        
        # Create a more comprehensive description with available data
        brand = details.get('Brand', '')
        name = details.get('Name', '')
        
        # Get processor info with improved extraction
        processor = self._extract_processor_info(laptop)
        
        # Extract memory, storage, graphics
        memory = ""
        storage = ""
        graphics = ""
        
        # Try Specs table first
        for table in tables:
            if table.get('title') == 'Specs' and 'data' in table:
                memory = table['data'].get('Memory Installed', '')
                storage = table['data'].get('Storage', '')
                graphics = table['data'].get('Graphics Card', '')
        
        # If not found, try Misc table
        if not memory or not storage or not graphics:
            for table in tables:
                if table.get('title') == 'Misc' and 'data' in table:
                    if not memory:
                        memory = table['data'].get('Memory Installed', '')
                    if not storage:
                        storage = table['data'].get('Storage', '')
                    if not graphics:
                        graphics = table['data'].get('Graphics Card', '')
        
        # Extract screen info
        screen_size = ""
        resolution = ""
        
        for table in tables:
            if table.get('title') == 'Screen' and 'data' in table:
                screen_size = table['data'].get('Size', '')
                resolution = table['data'].get('Resolution', '')
        
        # Extract battery life and OS
        battery_life = ""
        os = ""
        
        for table in tables:
            if table.get('title') == 'Features' and 'data' in table:
                os = table['data'].get('Operating System', '')
            elif table.get('title') == 'Misc' and 'data' in table:
                if not os:
                    os = table['data'].get('Operating System', '')
                battery_life = table['data'].get('Battery Life', '')
        
        # Extract special features
        touchscreen = False
        backlit_keyboard = False
        
        for table in tables:
            if table.get('title') == 'Screen' and 'data' in table:
                touchscreen = table['data'].get('Touchscreen', False)
            if table.get('title') == 'Features' and 'data' in table:
                backlit_keyboard = table['data'].get('Backlit Keyboard', False)
        
        # Create components to build the description
        components = []
        components.append(f"{brand} {name}")
        
        # Add emphasized features first if they exist in the laptop
        emphasized_components = []
        if 'processor' in self.emphasized_features and processor:
            emphasized_components.append(f"{processor} processor")
        
        if 'gaming' in self.emphasized_features and graphics:
            emphasized_components.append(f"{graphics} graphics")
        
        if 'memory' in self.emphasized_features and memory:
            emphasized_components.append(f"{memory} RAM")
        
        if 'storage' in self.emphasized_features and storage:
            emphasized_components.append(f"{storage} storage")
        
        if 'touchscreen' in self.emphasized_features and touchscreen:
            emphasized_components.append("touchscreen display")
        
        if 'backlit' in self.emphasized_features and backlit_keyboard:
            emphasized_components.append("backlit keyboard")
        
        if 'battery' in self.emphasized_features and battery_life:
            emphasized_components.append(f"{battery_life} battery life")
            
        if 'screen' in self.emphasized_features and (screen_size or resolution):
            screen_info = ""
            if screen_size:
                screen_info += f"{screen_size}"
            if resolution:
                if screen_info:
                    screen_info += f" {resolution}"
                else:
                    screen_info = resolution
            emphasized_components.append(f"{screen_info} display")
        
        # Add emphasized components first
        if emphasized_components:
            components.append("with " + ", ".join(emphasized_components))
        
        # Add remaining components that weren't emphasized
        remaining_components = []
        
        if processor and 'processor' not in self.emphasized_features:
            remaining_components.append(f"{processor} processor")
        
        if memory and 'memory' not in self.emphasized_features:
            remaining_components.append(f"{memory} RAM")
        
        if storage and 'storage' not in self.emphasized_features:
            remaining_components.append(f"{storage} storage")
        
        if (screen_size or resolution) and 'screen' not in self.emphasized_features:
            screen_info = ""
            if screen_size:
                screen_info += f"{screen_size}"
            if resolution:
                if screen_info:
                    screen_info += f" {resolution}"
                else:
                    screen_info = resolution
            remaining_components.append(f"{screen_info} display")
        
        if graphics and 'gaming' not in self.emphasized_features:
            remaining_components.append(f"{graphics} graphics")
        
        if os:
            remaining_components.append(f"{os}")
        
        if battery_life and 'battery' not in self.emphasized_features:
            remaining_components.append(f"{battery_life} battery life")
        
        # Add touchscreen info if not emphasized
        if touchscreen and 'touchscreen' not in self.emphasized_features:
            remaining_components.append("touchscreen display")
        
        # Add backlit keyboard info if not emphasized
        if backlit_keyboard and 'backlit' not in self.emphasized_features:
            remaining_components.append("backlit keyboard")
        
        # Add weight information if available
        weight = details.get('Weight', '')
        if weight:
            remaining_components.append(f"weighing {weight}")
        
        # Add remaining components if there are any
        if remaining_components:
            if not emphasized_components:
                components.append("with " + ", ".join(remaining_components))
            else:
                components.append(", ".join(remaining_components))
        
        return " ".join(components)

    def _extract_processor_info(self, laptop: Dict) -> str:
        """
        Extract processor information with multiple fallback methods
        to ensure processor info is always available when present
        """
        processor = ""
        
        # Primary method: Check dedicated Processor table
        for table in laptop.get('tables', []):
            if table.get('title') == 'Processor' and 'data' in table:
                proc_brand = table['data'].get('Brand', '')
                proc_name = table['data'].get('Name', '')
                if proc_brand and proc_name:
                    processor = f"{proc_brand} {proc_name}"
                    break
                elif proc_name:
                    processor = proc_name
                    break
        
        # Fallback 1: Check Specs table
        if not processor:
            for table in laptop.get('tables', []):
                if table.get('title') == 'Specs' and 'data' in table:
                    proc_brand = table['data'].get('Processor Brand', '')
                    proc_name = table['data'].get('Processor Name', '')
                    if proc_brand and proc_name:
                        processor = f"{proc_brand} {proc_name}"
                        break
                    elif proc_name:
                        processor = proc_name
                        break
        
        # Fallback 2: Check Misc table or any other tables
        if not processor:
            for table in laptop.get('tables', []):
                if 'data' in table and isinstance(table['data'], dict):
                    for key, value in table['data'].items():
                        if any(term in key.lower() for term in ['processor', 'cpu', 'chip']):
                            processor = value
                            break
                    if processor:
                        break
        
        # Fallback 3: Look in laptop name/model for common processor terms
        if not processor:
            name = ""
            for table in laptop.get('tables', []):
                if table.get('title') == 'Product Details' and 'data' in table:
                    name = table['data'].get('Name', '')
                    break
                    
            if name:
                # Search for common processor patterns in name
                cpu_patterns = [
                    r'i[3579]-\d{4,5}[A-Z]*',  # Intel Core i3/i5/i7/i9
                    r'Ryzen \d [0-9A-Z]{4,}',  # AMD Ryzen
                    r'Snapdragon [0-9X]{3,}',  # Qualcomm
                    r'M[1-3] (Pro|Max|Ultra)?', # Apple Silicon
                    r'Celeron [A-Z0-9-]+',     # Intel Celeron
                    r'Pentium [A-Z0-9-]+'      # Intel Pentium
                ]
                
                for pattern in cpu_patterns:
                    match = re.search(pattern, name)
                    if match:
                        processor = match.group(0)
                        break
        
        return processor

    def _extract_price_range(self, laptop: Dict) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract the lowest price from a laptop's price table
        Returns: (price_value, price_string)
        """
        price_value = None
        price_string = None
        
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
                            clean_price = price_str.replace('£', '').replace(',', '')
                            try:
                                price_val = float(clean_price)
                                if lowest_price is None or price_val < lowest_price:
                                    lowest_price = price_val
                                    lowest_price_str = price_str
                            except ValueError:
                                continue
                    
                    price_value = lowest_price
                    price_string = lowest_price_str
        
        return (price_value, price_string)

    def _parse_budget_range(self, budget_input: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse budget input to extract lower and upper bounds
        Returns: (min_budget, max_budget) in float values
        """
        # Remove currency symbols and commas
        cleaned_input = budget_input.replace('£', '').replace('$', '').replace(',', '').lower()
        
        # Look for range patterns like "500-1000" or "between 500 and 1000"
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', cleaned_input)
        between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', cleaned_input)
        
        if range_match:
            return (float(range_match.group(1)), float(range_match.group(2)))
        elif between_match:
            return (float(between_match.group(1)), float(between_match.group(2)))
        
        # Look for "under X" or "less than X" patterns
        under_match = re.search(r'(?:under|less than|below|max|maximum)\s+(\d+)', cleaned_input)
        if under_match:
            return (None, float(under_match.group(1)))
        
        # Look for "over X" or "more than X" patterns
        over_match = re.search(r'(?:over|more than|above|min|minimum)\s+(\d+)', cleaned_input)
        if over_match:
            return (float(over_match.group(1)), None)
        
        # Look for just a number
        number_match = re.search(r'(\d+)', cleaned_input)
        if number_match:
            budget = float(number_match.group(1))
            # Assume 20% flexibility around the stated budget
            return (budget * 0.8, budget * 1.2)
        
        # If no patterns match, return None
        return (None, None)

    def _filter_laptops(self, filters: Dict = None) -> List[Dict]:
        """
        Filter laptops based on user preferences including excluded brands
        """
        if not filters:
            # Even with no specific filters, we still apply excluded brands
            if self.excluded_brands:
                filtered_laptops = []
                for laptop in self.laptops:
                    brand = ""
                    for table in laptop.get('tables', []):
                        if table.get('title') == 'Product Details' and 'data' in table:
                            brand = table['data'].get('Brand', '').lower()
                            break
                    
                    if brand and brand not in self.excluded_brands:
                        filtered_laptops.append(laptop)
                return filtered_laptops
            return self.laptops

        filtered_laptops = self.laptops
        
        # Apply excluded brands filter first
        if self.excluded_brands:
            excluded_filtered = []
            for laptop in filtered_laptops:
                brand = ""
                for table in laptop.get('tables', []):
                    if table.get('title') == 'Product Details' and 'data' in table:
                        brand = table['data'].get('Brand', '').lower()
                        break
                
                if brand and brand not in self.excluded_brands:
                    excluded_filtered.append(laptop)
            filtered_laptops = excluded_filtered
        
        # Filter by screen size
        if 'size' in filters:
            # Convert string sizes to actual sizes for comparison
            size_values = []
            for size in filters['size']:
                try:
                    # Handle ranges like "13-14"
                    if '-' in str(size):
                        min_size, max_size = map(float, str(size).split('-'))
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
        
        # Filter by budget
        if 'budget' in filters:
            min_budget, max_budget = filters['budget']
            
            if min_budget is not None or max_budget is not None:
                budget_filtered = []
                
                for laptop in filtered_laptops:
                    price_value, _ = self._extract_price_range(laptop)
                    
                    if price_value is not None:
                        if (min_budget is None or price_value >= min_budget) and \
                           (max_budget is None or price_value <= max_budget):
                            budget_filtered.append(laptop)
                
                filtered_laptops = budget_filtered
        
        # Filter by features
        if 'features' in filters:
            features = filters['features']
            
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
            # Add to emphasized features
            if 'touchscreen' not in self.emphasized_features:
                self.emphasized_features.append('touchscreen')
        
        # Check for backlit keyboard
        if re.search(r'\b(?:backlit|lit keyboard|keyboard lighting)\b', user_input.lower()):
            features['backlit_keyboard'] = True
            # Add to emphasized features
            if 'backlit' not in self.emphasized_features:
                self.emphasized_features.append('backlit')
        
        # Check for ports (HDMI, USB-C, etc.)
        if re.search(r'\b(?:hdmi|port)\b', user_input.lower()):
            features['ports'] = True
        
        # Check for battery life
        battery_match = re.search(r'(?:battery|battery life|long battery|last\w*\s+\d+\s+hours)', user_input.lower())
        if battery_match:
            features['battery_life'] = True
            # Add to emphasized features
            if 'battery' not in self.emphasized_features:
                self.emphasized_features.append('battery')
        
        # Check for processor emphasis
        if re.search(r'\b(?:processor|cpu|fast|powerful|i[3579]|ryzen|m[1-3])\b', user_input.lower()):
            # Add to emphasized features
            if 'processor' not in self.emphasized_features:
                self.emphasized_features.append('processor')
        
        # Check for memory emphasis
        if re.search(r'\b(?:ram|memory|16gb|32gb|64gb)\b', user_input.lower()):
            # Add to emphasized features
            if 'memory' not in self.emphasized_features:
                self.emphasized_features.append('memory')
        
        # Check for storage emphasis
        if re.search(r'\b(?:storage|ssd|hard drive|hdd|disk|terabyte|gb|tb)\b', user_input.lower()):
            # Add to emphasized features
            if 'storage' not in self.emphasized_features:
                self.emphasized_features.append('storage')
        
        # Check for screen emphasis
        if re.search(r'\b(?:screen|display|resolution|4k|1080p|oled|ips)\b', user_input.lower()):
            # Add to emphasized features
            if 'screen' not in self.emphasized_features:
                self.emphasized_features.append('screen')
        
        return features

    def _parse_size_preference(self, user_input: str) -> List[Union[int, str]]:
        """
        Parse screen size preferences from user input
        Returns a list of sizes or size ranges
        """
        sizes = []
        
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
        
        # Look for size descriptions
        if re.search(r'\b(?:small|compact|portable)\b', user_input.lower()):
            sizes.extend([13, 14])
        
        if re.search(r'\b(?:medium|standard)\b', user_input.lower()):
            sizes.extend([15, 15.6])
        
        if re.search(r'\b(?:large|big|desktop replacement)\b', user_input.lower()):
            sizes.extend([16, 17])
        
        return sizes

    def _extract_brands_from_input(self, user_input: str) -> Tuple[List[str], List[str]]:
        """
        Extract brand preferences and exclusions from user input
        Returns a tuple of (preferred_brands, excluded_brands)
        """
        preferred_brands = []
        excluded_brands = []
        common_brands = [
            "dell", "lenovo", "hp", "asus", "acer", "apple", "msi", 
            "samsung", "microsoft", "lg", "razer", "toshiba", "alienware",
            "huawei", "sony", "fujitsu", "gigabyte", "chuwi"
        ]
        
        # Convert input to lowercase for case-insensitive comparison
        user_input_lower = user_input.lower()
        
        # Check for brand exclusions
        exclusion_patterns = [
            r"(?:don't|do not|won't|will not|can't|cannot|no|not) (?:want|like|need|interested in|looking for).*?(?:brand[s]?)?.*?([a-z]+)",
            r"(?:anything|any) (?:but|except|other than|besides).*?([a-z]+)",
            r"(?:hate|dislike|avoid).*?([a-z]+)"
        ]
        
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, user_input_lower)
            for match in matches:
                for brand in common_brands:
                    if brand in match:
                        excluded_brands.append(brand)
        
        # Check for direct exclusion mentions
        no_phrases = [f"no {brand}" for brand in common_brands]
        not_phrases = [f"not {brand}" for brand in common_brands]
        
        for brand in common_brands:
            if any(phrase in user_input_lower for phrase in [f"no {brand}", f"not {brand}"]):
                excluded_brands.append(brand)
        
        # Check for preferred brands (if not excluded)
        for brand in common_brands:
            if brand in user_input_lower and brand not in excluded_brands:
                # Verify it's not part of another word
                if re.search(r'\b' + brand + r'\b', user_input_lower):
                    preferred_brands.append(brand)
        
        return preferred_brands, excluded_brands

    def _extract_performance_level(self, user_input: str) -> str:
        """
        Determine the performance level preference from user input
        Returns: 'high', 'medium', or 'basic'
        """
        user_input_lower = user_input.lower()
        
        # High performance indicators
        high_perf = [
            "high performance", "powerful", "fast", "gaming", "rendering",
            "video editing", "3d modeling", "simulation", "high-end", "top spec"
        ]
        
        # Medium performance indicators
        medium_perf = [
            "medium performance", "balanced", "mid-range", "moderate",
            "good performance", "decent"
        ]
        
        # Basic performance indicators
        basic_perf = [
            "basic", "budget", "entry level", "simple tasks", "browsing",
            "office work", "light use", "casual", "everyday"
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

    def _is_off_topic(self, user_input: str) -> bool:
        """
        Dynamically check if user input is off-topic from laptop-related conversation
        by measuring semantic similarity to laptop topics
        
        Returns: True if the message is off-topic, False otherwise
        """
        # Handle empty input
        if not user_input.strip():
            return False
            
        # Convert input to lowercase for processing
        user_input_lower = user_input.lower()
        
        # Skip relevance check for short responses to questions
        if self.conversation_state != "initial" and len(user_input_lower.split()) < 5:
            # Short responses like "yes", "no", "under $1000" are likely relevant
            return False
        
        # Check for common on-topic keywords as a fast first check
        laptop_related_keywords = [
            "laptop", "computer", "pc", "notebook", "processor", "cpu", "gpu", 
            "ram", "memory", "screen", "display", "battery", "keyboard", 
            "touchpad", "port", "usb", "windows", "mac", "linux", "gaming",
            "dell", "hp", "lenovo", "asus", "acer", "apple", "microsoft",
            "ssd", "storage", "drive", "graphics", "price", "budget", "core i",
            "ryzen", "touchscreen", "webcam", "camera", "resolution", "portable",
            "lightweight", "performance", "inch", "hdmi", "brand", "cooling",
            "gaming", "work", "student", "business", "programming", "design",
            "video editing", "backlit", "bluetooth", "wifi", "thunderbolt"
        ]
        
        for keyword in laptop_related_keywords:
            if keyword in user_input_lower:
                return False  # Found a laptop-related keyword, so not off-topic
        
        # If no keywords found, do a more thorough semantic relevance check
        user_embedding = self.model.encode(user_input)
        similarity = cosine_similarity([user_embedding], [self.laptop_topic_embeddings])[0][0]
        
        # Low similarity score indicates the topic is not related to laptops
        return similarity < self.topic_relevance_threshold

    def _keyword_based_use_case(self, user_input: str) -> List[str]:
        """
        Use keyword matching to identify multiple use cases
        Returns a list of use cases
        """
        user_input = user_input.lower()
        
        # Define keywords for each category
        keywords = {
            "gaming": ["gaming", "game", "play", "fps", "aaa", "shooter", "mmo", "rpg", "esports"],
            "business": ["business", "work", "office", "professional", "meetings", "presentation"],
            "student": ["student", "school", "college", "university", "education", "study", "homework"],
            "design": ["design", "creative", "art", "photo", "video", "editing", "creator", "adobe", "illustrator", "photoshop"],
            "programming": ["programming", "coding", "development", "software", "code", "developer", "programming"],
            "portable": ["portable", "light", "travel", "thin", "lightweight", "carry", "commute"],
            "entertainment": ["entertainment", "media", "movies", "streaming", "netflix", "videos", "watch"],
            "content_creation": ["content", "creator", "youtube", "stream", "render", "production"],
            "budget": ["budget", "cheap", "affordable", "inexpensive", "economical", "low cost"],
            "premium": ["premium", "high-end", "luxury", "best", "top", "flagship"]
        }
        
        # Count keyword matches for each category
        category_scores = {category: 0 for category in keywords}
        
        for category, words in keywords.items():
            for word in words:
                # Use word boundary to match whole words
                matches = len(re.findall(r'\b' + word + r'\b', user_input))
                category_scores[category] += matches
        
        # Get categories with scores > 0, sorted by score (highest first)
        matching_categories = [
            category for category, score in 
            sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            if score > 0
        ]
        
        # Return top 2 categories, or "student" as default if none match
        if matching_categories:
            return matching_categories[:2]  # Return top 2 matching categories
        
        # Default to "student" if no keywords match
        return ["student"]

    def _analyze_preferences(self, user_input: str) -> Dict:
        """
        Analyze user input for all possible preferences in one go
        """
        preferences = {}
        
        # First check if the input is off-topic
        if self._is_off_topic(user_input):
            # Set a flag to indicate off-topic content
            preferences['off_topic'] = True
            return preferences
        
        # Extract use case using embeddings first, then keywords as fallback
        user_embedding = self.model.encode(user_input)
        similarities = {
            use_case: cosine_similarity([user_embedding], [emb])[0][0]
            for use_case, emb in self.feature_embeddings.items()
        }
        
        # Get top 2 most relevant use cases
        top_use_cases = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # Use embeddings if similarity is high enough, otherwise keyword matching
        if top_use_cases[0][1] < 0.3:  # Threshold for low confidence
            use_cases = self._keyword_based_use_case(user_input)
            preferences['use_case'] = use_cases  # Now returns a list
        else:
            # Get both top use cases if they're both relevant
            use_cases = []
            for use_case, similarity in top_use_cases:
                if similarity > 0.25:  # Only include if reasonably similar
                    use_cases.append(use_case)
            preferences['use_case'] = use_cases
        
        # Extract screen size preferences
        size_pref = self._parse_size_preference(user_input)
        if size_pref:
            preferences['size'] = size_pref
        
        # Extract brand preferences and exclusions
        brand_pref, excluded_brands = self._extract_brands_from_input(user_input)
        if brand_pref:
            preferences['brand'] = brand_pref
        
        # Update excluded brands
        if excluded_brands:
            self.excluded_brands.update(excluded_brands)
            preferences['excluded_brands'] = list(self.excluded_brands)
        
        # Extract budget range
        budget_match = re.search(r'\b(?:budget|price|cost|spend|around|under|below|max)\b[^.]*?(\d[\d,.]*)', user_input, re.IGNORECASE)
        if budget_match:
            budget_input = budget_match.group(0)
            min_budget, max_budget = self._parse_budget_range(budget_input)
            if min_budget is not None or max_budget is not None:
                preferences['budget'] = (min_budget, max_budget)
        
        # Extract feature preferences
        feature_pref = self._extract_features_from_input(user_input)
        if feature_pref:
            preferences['features'] = feature_pref
        
        # Extract performance level
        preferences['performance'] = self._extract_performance_level(user_input)
        
        return preferences

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
        
        # Check if input is off-topic
        if self._is_off_topic(user_input):
            self.off_topic_counter += 1
            
            # Polite redirection with varying messages based on counter
            if self.off_topic_counter == 1:
                response["message"] = "Let's stay focused on finding you a laptop. Could you please tell me what you're looking for in a computer?"
                # Maintain current conversation state
                response["next_question"] = self.questions[self.conversation_state]
            elif self.off_topic_counter == 2:
                response["message"] = "I'm here to help you find a laptop that meets your needs. Let's get back to discussing computer specifications."
                response["next_question"] = self.questions[self.conversation_state]
            else:
                # More direct redirection after multiple off-topic inputs
                response["message"] = "To provide you with laptop recommendations, I need information about your requirements. Please tell me about what kind of laptop you're looking for."
                # Reset to initial state if user persists with off-topic content
                self.reset_conversation()
                self.conversation_state = "initial"
                response["next_question"] = self.questions["initial"]
            
            return response
        
        # Reset off-topic counter when user provides appropriate input
        self.off_topic_counter = 0

        # Process based on conversation state
        if self.conversation_state == "initial":
            # Analyze initial input comprehensively
            preferences = self._analyze_preferences(user_input)
            self.user_preferences.update(preferences)
            
            # Check if input was off-topic
            if 'off_topic' in preferences and preferences['off_topic']:
                response["message"] = "I'm here to help you find a laptop. Please describe what kind of computer you're looking for."
                return response
            
            # Provide information about detected preferences
            use_cases = self.user_preferences.get('use_case', [''])
            
            # Format use case description with multiple use cases
            if len(use_cases) > 1:
                use_case_str = f"{use_cases[0]} and {use_cases[1]}"
            else:
                use_case_str = use_cases[0] if use_cases else "general purpose"
                
            response["detected_preferences"] = preferences
            response["message"] = f"I understand you're looking for a {use_case_str} laptop."
            
            # Mention excluded brands if any
            if self.excluded_brands:
                excluded_brands_str = ", ".join(self.excluded_brands)
                response["message"] += f" I'll avoid showing {excluded_brands_str} laptops."
            
            # Check if we have enough information to provide recommendations
            if len(preferences) >= 2:
                # Apply filters based on detected preferences
                filters = {}
                
                if 'size' in preferences:
                    filters['size'] = preferences['size']
                
                if 'brand' in preferences:
                    filters['brand'] = preferences['brand']
                
                if 'budget' in preferences:
                    filters['budget'] = preferences['budget']
                
                if 'features' in preferences:
                    filters['features'] = preferences['features']
                
                filtered_laptops = self._filter_laptops(filters)
                
                if filtered_laptops:
                    # Get recommendations based on use case and filtered laptops
                    recommendations = self._get_multi_purpose_recommendations(filtered_laptops, preferences.get('use_case', ['student']), 3)
                    
                    if recommendations:
                        response["recommendations"] = recommendations
                        self.last_recommendations = recommendations
                        response["message"] += " Based on your preferences, here are some initial recommendations:"
                        self.conversation_state = "refine"
                        response["next_question"] = "Would you like to refine your search or see more options?"
                    else:
                        response["message"] += " I couldn't find laptops matching all your criteria. Let me ask you more questions to provide better recommendations."
                        self.conversation_state = "budget"
                        response["next_question"] = self.questions["budget"]
                else:
                    response["message"] += " I need more information to provide good recommendations."
                    self.conversation_state = "size"
                    response["next_question"] = self.questions["size"]
            else:
                # Not enough information yet
                self.conversation_state = "size"
                response["next_question"] = self.questions["size"]
        
        elif self.conversation_state == "size":
            # Extract screen size preference
            size_pref = self._parse_size_preference(user_input)
            
            if size_pref:
                self.user_preferences['size'] = size_pref
                response["message"] = f"Got it, you prefer a {', '.join(str(s) for s in size_pref)}\" screen size."
            else:
                response["message"] = "I'll note that screen size isn't a priority for you."
            
            # Move to next question
            self.conversation_state = "budget"
            response["next_question"] = self.questions["budget"]
        
        elif self.conversation_state == "budget":
            # Extract budget preference
            budget_input = user_input
            min_budget, max_budget = self._parse_budget_range(budget_input)
            
            if min_budget is not None or max_budget is not None:
                self.user_preferences['budget'] = (min_budget, max_budget)
                
                if min_budget is not None and max_budget is not None:
                    response["message"] = f"I'll look for laptops between £{min_budget:.0f} and £{max_budget:.0f}."
                elif min_budget is not None:
                    response["message"] = f"I'll look for laptops over £{min_budget:.0f}."
                else:
                    response["message"] = f"I'll look for laptops under £{max_budget:.0f}."
            else:
                response["message"] = "I'll consider a range of price points for you."
            
            # Move to brand question
            self.conversation_state = "brand"
            response["next_question"] = self.questions["brand"]
        
        elif self.conversation_state == "brand":
            # Extract brand preferences and exclusions
            if any(term in user_input.lower() for term in ["no", "none", "any", "no preference", "doesn't matter"]):
                response["message"] = "Got it, I won't filter by brand."
            else:
                brand_prefs, excluded_brands = self._extract_brands_from_input(user_input)
                
                # Handle preferred brands
                if brand_prefs:
                    self.user_preferences['brand'] = brand_prefs
                    response["message"] = f"I'll focus on {', '.join(brand_prefs)} laptops."
                
                # Handle excluded brands
                if excluded_brands:
                    self.excluded_brands.update(excluded_brands)
                    excluded_str = ", ".join(excluded_brands)
                    if not brand_prefs:
                        response["message"] = f"I'll avoid {excluded_str} laptops in my recommendations."
                    else:
                        response["message"] += f" And I'll avoid {excluded_str} laptops."
                
                if not brand_prefs and not excluded_brands:
                    response["message"] = "I couldn't identify specific brand preferences. I'll show options from various manufacturers."
            
            # Move to features question
            self.conversation_state = "features"
            response["next_question"] = self.questions["features"]
        
        elif self.conversation_state == "features":
            # Extract feature preferences
            features = self._extract_features_from_input(user_input)
            
            if features:
                self.user_preferences['features'] = features
                feature_list = ", ".join(features.keys())
                response["message"] = f"I'll look for laptops with {feature_list}."
            else:
                response["message"] = "No specific features noted."
            
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
            
            filtered_laptops = self._filter_laptops(filters)
            
            if filtered_laptops:
                # Get recommendations based on use case and filtered laptops
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 5)
                
                if recommendations:
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
                    response["message"] += " Here are your personalized recommendations:"
                else:
                    response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                    # Relax some constraints
                    relaxed_filters = {k: v for k, v in filters.items() if k != 'features'}
                    relaxed_laptops = self._filter_laptops(relaxed_filters)
                    recommendations = self._get_multi_purpose_recommendations(relaxed_laptops, use_cases, 3)
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
            else:
                response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                # Try with minimal filtering
                minimal_laptops = self._filter_laptops({})
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(minimal_laptops, use_cases, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            self.conversation_state = "refine"
            response["next_question"] = "Would you like to refine your search or see more options?"
        
        elif self.conversation_state == "refine":
            # Handle refinement requests or requests for more options
            if any(term in user_input.lower() for term in ["more", "additional", "other", "alternative", "show more"]):
                # Show more recommendations
                use_cases = self.user_preferences.get('use_case', ['student'])
                filters = {}
                
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                
                if 'budget' in self.user_preferences:
                    filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                
                # Skip laptops that were already recommended
                previous_names = [rec['name'] for rec in self.last_recommendations]
                new_laptops = [laptop for laptop in filtered_laptops if not any(
                    self._get_laptop_name(laptop) == name for name in previous_names
                )]
                
                if new_laptops:
                    recommendations = self._get_multi_purpose_recommendations(new_laptops, use_cases, 3)
                    response["recommendations"] = recommendations
                    self.last_recommendations.extend(recommendations)
                    response["message"] = "Here are some additional options that might interest you:"
                else:
                    response["message"] = "I don't have any more recommendations matching your criteria. Would you like to broaden your search?"
            
            # Handle specific refinement requests
            elif any(term in user_input.lower() for term in ["cheaper", "less expensive", "lower price", "budget"]):
                # Find cheaper options
                if 'budget' in self.user_preferences:
                    min_budget, max_budget = self.user_preferences['budget']
                    if max_budget is not None:
                        # Reduce max budget by 25%
                        new_max = max_budget * 0.75
                        self.user_preferences['budget'] = (min_budget, new_max)
                        response["message"] = f"Looking for more affordable options under £{new_max:.0f}:"
                else:
                    # Set a default budget cap
                    self.user_preferences['budget'] = (None, 800)
                    response["message"] = "Looking for more affordable options:"
                
                # Apply the new budget filter
                filters = {}
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            elif any(term in user_input.lower() for term in ["expensive", "higher price", "premium", "better"]):
                # Find more premium options
                if 'budget' in self.user_preferences:
                    min_budget, max_budget = self.user_preferences['budget']
                    if min_budget is not None:
                        # Increase min budget by 25%
                        new_min = min_budget * 1.25
                        self.user_preferences['budget'] = (new_min, max_budget)
                        response["message"] = f"Looking for more premium options above £{new_min:.0f}:"
                else:
                    # Set a default budget floor
                    self.user_preferences['budget'] = (1000, None)
                    response["message"] = "Looking for more premium options:"
                
                # Apply the new budget filter
                filters = {}
                if 'size' in self.user_preferences:
                    filters['size'] = self.user_preferences['size']
                if 'brand' in self.user_preferences:
                    filters['brand'] = self.user_preferences['brand']
                filters['budget'] = self.user_preferences['budget']
                
                filtered_laptops = self._filter_laptops(filters)
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            elif any(term in user_input.lower() for term in ["smaller", "more portable", "lighter"]):
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
                use_cases = self.user_preferences.get('use_case', ['student'])
                if 'portable' not in use_cases:
                    use_cases.append('portable')
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 3)
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
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            else:
                # Process as a new input to refine search
                new_preferences = self._analyze_preferences(user_input)
                
                # Check if input was off-topic
                if 'off_topic' in new_preferences and new_preferences['off_topic']:
                    response["message"] = "Let's stay focused on laptop specifications. What specific features are you looking for in your next laptop?"
                    return response
                
                # Update existing preferences with new ones
                self.user_preferences.update(new_preferences)
                
                # Extract any newly mentioned features for emphasis
                self._extract_features_from_input(user_input)
                
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
                
                filtered_laptops = self._filter_laptops(filters)
                use_cases = self.user_preferences.get('use_case', ['student'])
                recommendations = self._get_multi_purpose_recommendations(filtered_laptops, use_cases, 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
        
        return response

    def _get_multi_purpose_recommendations(self, laptops: List[Dict], use_cases: List[str], count: int = 3) -> List[Dict]:
        """
        Get laptop recommendations based on multiple use cases
        This combines the embeddings of different use cases for better multi-purpose recommendations
        
        Args:
            laptops: List of laptop dictionaries
            use_cases: List of use case strings (e.g., ["gaming", "student"])
            count: Number of recommendations to return
            
        Returns:
            List of laptop recommendation dictionaries
        """
        if not laptops:
            return []
        
        # Get laptop embeddings
        laptop_embeddings = self._get_laptop_embeddings(laptops)
        
        # Process for single or multiple use cases
        if len(use_cases) == 1:
            # Single use case - use the standard method
            use_case = use_cases[0]
            use_case_embedding = self.feature_embeddings.get(use_case, self.feature_embeddings['student'])
            similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
        else:
            # Multiple use cases - combine embeddings
            combined_similarities = np.zeros(len(laptops))
            
            # Get embeddings for each use case
            for use_case in use_cases:
                use_case_embedding = self.feature_embeddings.get(use_case, self.feature_embeddings['student'])
                similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
                
                # Add to combined similarities (weighted average)
                combined_similarities += similarities
            
            # Average the similarities
            similarities = combined_similarities / len(use_cases)
        
        # Get top indices but limit to available laptops
        count = min(count, len(laptops))
        if count == 0:
            return []
            
        top_indices = np.argsort(similarities)[-count:][::-1]
        
        recommendations = []
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
                
                # Extract image URL if available
                image_url = None
                for table in laptop.get('tables', []):
                    if table.get('title') == 'Images' and 'data' in table:
                        image_url = table['data'].get('url', None)
                        break
                
                recommendations.append({
                    'brand': brand,
                    'name': name,
                    'specs': self._format_laptop_description(laptop),
                    'price': price_string if price_string else "Price not available",
                    'similarity_score': similarities[idx],
                    'image_url': image_url
                })
        
        return recommendations

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

    def reset_conversation(self):
        """
        Reset the conversation state and user preferences
        """
        self.conversation_state = "initial"
        self.user_preferences = {}
        self.excluded_brands = set()
        self.last_recommendations = []
        self.emphasized_features = []
        self.off_topic_counter = 0

def converse_with_chatbot(limit=10000):
    """
    Main function to run an interactive conversation with the laptop recommendation bot
    
    Args:
        limit: Maximum number of laptops to load (default: 10000)
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
    print("- \"I want a laptop for both gaming and office work\"")
    print("- \"I want any brand except Dell\"")
    print("\nYou can exit the conversation by typing 'quit', 'exit', or 'bye'.")
    print("Type 'restart' to begin a new search.\n")
    
    # Initialize the chatbot with database connection
    try:
        logger.info("Initializing chatbot and connecting to database...")
        chatbot = LaptopRecommendationBot()
        
        # Check if laptops were loaded
        if not chatbot.laptops:
            logger.error("Error: No laptop data available. Please check your database connection.")
            return
            
        logger.info(f"Chatbot initialized with {len(chatbot.laptops)} laptops from database!")
        
    except Exception as e:
        logger.error(f"Error initializing the chatbot: {str(e)}")
        logger.error("This could be due to issues with the SentenceTransformer model or database connection.")
        logger.error("Make sure you have the required packages installed and the database is accessible.")
        return
    
    # Start the conversation with initial question
    print("\nBot:", chatbot.questions["initial"])
    
    # Main conversation loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to exit
            if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                logger.info("\nBot: Thank you for using the Enhanced Laptop Recommendation Bot. Goodbye!")
                print("\nBot: Thank you for using the Enhanced Laptop Recommendation Bot. Goodbye!")
                break
                
            # Process user input
            response = chatbot.process_input(user_input)
            
            # Display bot response
            logger.info(f"\nBot: {response['message']}")
            print(f"\nBot: {response['message']}")
            
            # Display recommendations if any
            if response["recommendations"]:
                print("\nRecommended Laptops:")
                logger.info(f"Got recommendations for the user:")
                for i, laptop in enumerate(response["recommendations"], 1):
                    logger.info(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")
                    print(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")
                    print(f"   Specs: {laptop['specs']}")
                    
                    # Log if image URL is available
                    if 'image_url' in laptop and laptop['image_url']:
                        logger.info(f"   Image available for {laptop['brand']} {laptop['name']}")
                        # Don't print the base64 image URL to console as it's too long
                print()

            # Display next question if any
            if response["next_question"]:
                logger.info(f"Bot: {response['next_question']}")
                print(f"Bot: {response['next_question']}")
                
        except KeyboardInterrupt:
            logger.error("Conversation interrupted. Goodbye! ERROR: 'keyboard interrupt'")
            print("\n\nBot: Conversation interrupted. Goodbye!")
            break
        except Exception as e:
            logger.info(f"The chatbot encountered an error processing the user's request ERROR: {e}")
            print(f"\nBot: I encountered an error processing your request: {str(e)}")
            print("Bot: Let's try again or type 'restart' to begin a new search.")

if __name__ == "__main__":
    # Run the interactive conversation
    converse_with_chatbot()