# This is prototype 2 of the Sentence transformer chatbot

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional, Union
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from collections import defaultdict
from loguru import logger

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
            "performance": "How important is performance to you (e.g., high, medium, basic needs)?"
        }
        
        # Create embeddings for predefined features and use cases
        self.feature_embeddings = self._create_feature_embeddings()

    # This code block is to be inserted into your STPrototype3.py file
    # Replace the existing load_from_database method with this version

    # This is the corrected load_from_database method
    # Replace this in your STPrototype3.py file

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
            # Try to connect to the database 
            try:
                try:
                    # Make sure we're looking for the correct module name
                    import sys
                    import os
                    # Get current directory and make sure it's in the path
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    if current_dir not in sys.path:
                        sys.path.append(current_dir)
                    
                    # Try to import the db_new_access module
                    from db_new_access import get_db_connection, release_db_connection
                    conn, cur = get_db_connection()
                    logger.info("Connected to database using db_new_access module!")
                except Exception as import_err:
                    # If import failed, connect directly
                    logger.error(f"db_new_access module error: {str(import_err)}")
                    logger.info("Connecting directly to database")
                    conn = psycopg2.connect(
                        database="laptopchatbot_new",  
                        user="samuel",
                        host="86.19.219.159",
                        password="QwErTy1243!",
                        port=5432
                    )
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    logger.info("Connected to database directly!")
                # Check if tables exist in this database
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                available_tables = [row['table_name'] for row in cur.fetchall()]
                logger.info(f"Available tables: {', '.join(available_tables)}")
                
                # First, we need to identify the key columns in laptop_models
                # Let's check the column names in the laptop_models table
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'laptop_models' 
                    ORDER BY ordinal_position
                """)
                
                columns = cur.fetchall()
                column_names = [col['column_name'] for col in columns]
                logger.info(f"Columns in laptop_models: {', '.join(column_names)}")
                
                # Determine the primary key column
                # Based on the ERD, it's likely model_id or something similar
                primary_key_column = 'model_id'  # Default assumption
                model_name_column = 'model_name'  # Default assumption
                
                # Try to find the right columns
                for col in column_names:
                    if col.lower() in ('id', 'model_id'):
                        primary_key_column = col
                    if col.lower() in ('model', 'model_name', 'name'):
                        model_name_column = col
                
                logger.info(f"Using {primary_key_column} as primary key and {model_name_column} as model name")
                
                # Now get the laptop IDs from the primary table
                cur.execute(f"SELECT {primary_key_column} FROM laptop_models LIMIT {limit}")
                laptop_ids = cur.fetchall()
                
                if not laptop_ids:
                    logger.error("No laptops found in database")
                    return []
                    
                logger.info(f"Loading {len(laptop_ids)} laptops (limited from total)")
                
                # Create a list to store all laptop data
                laptops = []
                
                # Process each laptop
                for laptop_id_row in laptop_ids:
                    laptop_id = laptop_id_row[primary_key_column]
                    
                    # Create a laptop entry
                    laptop = {'tables': []}
                    
                    # Get basic laptop info
                    cur.execute(f"""
                        SELECT * FROM laptop_models WHERE {primary_key_column} = %s
                    """, (laptop_id,))
                    
                    laptop_info = cur.fetchone()
                    if not laptop_info:
                        continue
                    
                    # Add product details
                    product_details = {}
                    
                    # Map fields based on what's available
                    brand_column = next((c for c in column_names if c.lower() == 'brand'), None)
                    weight_column = next((c for c in column_names if c.lower() == 'weight'), None)
                    
                    if model_name_column in laptop_info:
                        product_details["Name"] = laptop_info[model_name_column]
                    if brand_column and brand_column in laptop_info:
                        product_details["Brand"] = laptop_info[brand_column]
                    if weight_column and weight_column in laptop_info:
                        product_details["Weight"] = laptop_info[weight_column]
                    
                    laptop['tables'].append({
                        'title': 'Product Details',
                        'data': product_details
                    })
                    
                    # Get configuration details if available
                    if 'laptop_configurations' in available_tables:
                        try:
                            # First, get the column names in laptop_configurations
                            cur.execute("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_schema = 'public' AND table_name = 'laptop_configurations' 
                            """)
                            config_columns = [col['column_name'] for col in cur.fetchall()]
                            
                            # Find the column that references laptop_models
                            # It could be model_id, laptop_id, etc.
                            fk_column = None
                            for col in config_columns:
                                if col.lower() in (f'{primary_key_column}', 'laptop_id', 'model_id'):
                                    fk_column = col
                                    break
                            
                            if fk_column:
                                # Get configuration details
                                cur.execute(f"""
                                    SELECT * FROM laptop_configurations WHERE {fk_column} = %s
                                """, (laptop_id,))
                                
                                config = cur.fetchone()
                                if config:
                                    # Extract memory, OS, processor, etc.
                                    misc_data = {}
                                    
                                    # Map fields to expected keys
                                    for key, value in config.items():
                                        if key.lower() in ('memory_installed', 'memory', 'ram'):
                                            misc_data["Memory Installed"] = value
                                        elif key.lower() in ('operating_system', 'os'):
                                            misc_data["Operating System"] = value
                                        elif key.lower() in ('battery_life', 'battery'):
                                            misc_data["Battery Life"] = value
                                    
                                    if misc_data:
                                        laptop['tables'].append({
                                            'title': 'Misc',
                                            'data': misc_data
                                        })
                        except Exception as e:
                            logger.error(f"Error getting configuration details: {str(e)}")
                    
                    # Get processor info if available
                    if 'processors' in available_tables:
                        try:
                            # First, get the column names in processors
                            cur.execute("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_schema = 'public' AND table_name = 'processors' 
                            """)
                            proc_columns = [col['column_name'] for col in cur.fetchall()]
                            
                            # Find the column that references laptop configurations
                            # It could be config_id, laptop_model, etc.
                            fk_column = None
                            for col in proc_columns:
                                if col.lower() in ('laptop_model', f'{primary_key_column}', 'config_id'):
                                    fk_column = col
                                    break
                            
                            if fk_column:
                                # Get processor details
                                cur.execute(f"""
                                    SELECT * FROM processors WHERE {fk_column} = %s
                                """, (laptop_id,))
                                
                                processor = cur.fetchone()
                                if processor:
                                    processor_data = {}
                                    
                                    # Map fields to expected keys
                                    for key, value in processor.items():
                                        if key.lower() in ('brand'):
                                            processor_data["Brand"] = value
                                        elif key.lower() in ('model'):
                                            processor_data["Name"] = value
                                    
                                    if processor_data:
                                        laptop['tables'].append({
                                            'title': 'Processor',
                                            'data': processor_data
                                        })
                        except Exception as e:
                            logger.error(f"Error getting processor details: {str(e)}")
                    
                    # Get screen info if available
                    if 'screens' in available_tables:
                        try:
                            # Get the column names in screens
                            cur.execute("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_schema = 'public' AND table_name = 'screens' 
                            """)
                            screen_columns = [col['column_name'] for col in cur.fetchall()]
                            
                            # Find the column that references laptop
                            fk_column = None
                            for col in screen_columns:
                                if col.lower() in ('laptop_model', f'{primary_key_column}', 'config_id'):
                                    fk_column = col
                                    break
                            
                            if fk_column:
                                # Get screen details
                                cur.execute(f"""
                                    SELECT * FROM screens WHERE {fk_column} = %s
                                """, (laptop_id,))
                                
                                screen = cur.fetchone()
                                if screen:
                                    screen_data = {}
                                    
                                    # Map fields to expected keys
                                    for key, value in screen.items():
                                        if key.lower() in ('resolution'):
                                            screen_data["Resolution"] = value
                                        elif key.lower() in ('refresh_rate'):
                                            screen_data["Refresh Rate"] = value
                                        elif key.lower() in ('touchscreen'):
                                            screen_data["Touchscreen"] = value
                                        elif key.lower() in ('size'):
                                            screen_data["Size"] = value
                                    
                                    if screen_data:
                                        laptop['tables'].append({
                                            'title': 'Screen',
                                            'data': screen_data
                                        })
                        except Exception as e:
                            logger.error(f"Error getting screen details: {str(e)}")
                    
                    # Add this laptop to the list
                    laptops.append(laptop)
                
                logger.info(f"Successfully loaded {len(laptops)} laptops from database")
                return laptops
                
            except Exception as db_e:
                logger.error(f"Error with primary database: {str(db_e)}")
                
                # Try connecting to the old database format as fallback
                logger.info("Trying fallback to old database schema...")
                
                # Code for old database format (similar to your original method)
                # This would contain your original implementation that works with the old schema
                # ...
                
                return []
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            return []
        finally:
            # Close the database connection
            try:
                if 'release_db_connection' in locals():
                    release_db_connection(conn, cur)
                    logger.info("Database connection released using DBAccess module.")
                else:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                    logger.info("Database connection closed directly.")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
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
        processor = ""
        
        # Try to find processor info
        for table in tables:
            if table.get('title') == 'Processor' and 'data' in table:
                processor = f"{table['data'].get('Brand', '')} {table['data'].get('Name', '')}"
                break
        
        # If not found in dedicated processor table, try to find it in Specs table
        if not processor:
            for table in tables:
                if table.get('title') == 'Specs' and 'data' in table:
                    proc_brand = table['data'].get('Processor Brand', '')
                    proc_name = table['data'].get('Processor Name', '')
                    if proc_brand and proc_name:
                        processor = f"{proc_brand} {proc_name}"
                        break
        
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
        
        # Build the description with available information
        description = f"{brand} {name}"
        
        if processor:
            description += f" with {processor} processor"
        
        if memory:
            description += f", {memory} RAM"
        
        if storage:
            description += f", {storage} storage"
        
        if screen_size or resolution:
            screen_info = ""
            if screen_size:
                screen_info += f"{screen_size}"
            if resolution:
                if screen_info:
                    screen_info += f" {resolution}"
                else:
                    screen_info = resolution
            description += f", {screen_info} display"
        
        if graphics:
            description += f", {graphics} graphics"
        
        if os:
            description += f", {os}"
        
        if battery_life:
            description += f", {battery_life} battery life"
        
        # Add weight information if available
        weight = details.get('Weight', '')
        if weight:
            description += f", weighing {weight}"
        
        return description

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
        Filter laptops based on user preferences
        """
        if not filters:
            return self.laptops

        filtered_laptops = self.laptops
        
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
        
        # Check for backlit keyboard
        if re.search(r'\b(?:backlit|lit keyboard|keyboard lighting)\b', user_input.lower()):
            features['backlit_keyboard'] = True
        
        # Check for ports (HDMI, USB-C, etc.)
        if re.search(r'\b(?:hdmi|port)\b', user_input.lower()):
            features['ports'] = True
        
        # Check for battery life
        battery_match = re.search(r'(?:battery|battery life|long battery|last\w*\s+\d+\s+hours)', user_input.lower())
        if battery_match:
            features['battery_life'] = True
        
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

    def _keyword_based_use_case(self, user_input: str) -> str:
        """
        Use keyword matching as a fallback for use case detection
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

        # Process based on conversation state
        if self.conversation_state == "initial":
            # Analyze initial input comprehensively
            preferences = self._analyze_preferences(user_input)
            self.user_preferences.update(preferences)
            
            # Provide information about detected preferences
            use_case = self.user_preferences.get('use_case', '')
            response["detected_preferences"] = preferences
            response["message"] = f"I understand you're looking for a {use_case} laptop."
            
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
                    recommendations = self._get_recommendations(filtered_laptops, preferences.get('use_case', 'student'), 3)
                    
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
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 5)
                
                if recommendations:
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
                    response["message"] += " Here are your personalized recommendations:"
                else:
                    response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                    # Relax some constraints
                    relaxed_filters = {k: v for k, v in filters.items() if k != 'features'}
                    relaxed_laptops = self._filter_laptops(relaxed_filters)
                    recommendations = self._get_recommendations(relaxed_laptops, self.user_preferences.get('use_case', 'student'), 3)
                    response["recommendations"] = recommendations
                    self.last_recommendations = recommendations
            else:
                response["message"] += " I couldn't find laptops matching all your criteria. Let me show you some alternatives."
                # Try with minimal filtering
                minimal_laptops = self._filter_laptops({})
                recommendations = self._get_recommendations(minimal_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
            
            self.conversation_state = "refine"
            response["next_question"] = "Would you like to refine your search or see more options?"
        
        elif self.conversation_state == "refine":
            # Handle refinement requests or requests for more options
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
                
                filtered_laptops = self._filter_laptops(filters)
                
                # Skip laptops that were already recommended
                previous_names = [rec['name'] for rec in self.last_recommendations]
                new_laptops = [laptop for laptop in filtered_laptops if not any(
                    self._get_laptop_name(laptop) == name for name in previous_names
                )]
                
                if new_laptops:
                    recommendations = self._get_recommendations(new_laptops, use_case, 3)
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
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
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
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
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
                
                filtered_laptops = self._filter_laptops(filters)
                recommendations = self._get_recommendations(filtered_laptops, self.user_preferences.get('use_case', 'student'), 3)
                response["recommendations"] = recommendations
                self.last_recommendations = recommendations
        
        return response

    def _get_recommendations(self, laptops: List[Dict], use_case: str, count: int = 3) -> List[Dict]:
        """
        Get top laptop recommendations based on use case
        """
        if not laptops:
            return []
        
        laptop_embeddings = self._get_laptop_embeddings(laptops)
        use_case_embedding = self.feature_embeddings.get(use_case, self.feature_embeddings['student'])
        
        similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
        
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
                
                recommendations.append({
                    'brand': brand,
                    'name': name,
                    'specs': self._format_laptop_description(laptop),
                    'price': price_string if price_string else "Price not available",
                    'similarity_score': similarities[idx]
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
        self.last_recommendations = []

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
            logger.info("\nBot:", response["message"])
            print("\nBot:", response["message"])
            
            # Display recommendations if any
            if response["recommendations"]:
                print("\nRecommended Laptops:")
                logger.info(f"got recommendations for the user:")
                for i, laptop in enumerate(response["recommendations"], 1):
                    logger.info(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")
                    logger.info(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")

                    print(f"{i}. {laptop['brand']} {laptop['name']} - {laptop['price']}")
                    print(f"   Specs: {laptop['specs']}")
                print()

            # Display next question if any
            if response["next_question"]:
                logger.info("Bot:", response["next_question"])

                print("Bot:", response["next_question"])
                
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