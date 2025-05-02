# ST stands for sentence transformer 
# This will be the first version prototype of how everything will be running
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import re

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
        
        # Predefined questions for gathering user preferences
        self.questions = {
            "initial": "What kind of laptop are you looking for? Please describe your needs.",
            "budget": "What's your approximate budget?",
            "purpose": "What will you primarily use the laptop for (e.g., gaming, work, studies)?",
            "size": "Do you have a preferred screen size (e.g., 14\", 15.6\", 16\")?",
            "brand": "Do you have any preferred brands?"
        }
        
        # Create embeddings for predefined features and use cases
        self.feature_embeddings = self._create_feature_embeddings()

    def load_from_database(self, limit=10000) -> List[Dict]:
        """
        Load laptop data from PostgreSQL database with optimizations
        
        Args:
            limit: Maximum number of laptops to load (default: 100)
        
        Returns:
            List of dictionaries containing laptop information in the same format as the JSON
        """
        conn = None
        cur = None
        try:
            # Try to use the imported db_access function
            try:
                conn, cur = get_db_connection()
                print("Connected to database using DBAccess module!")
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
            
            print("Connected to database successfully!")
            
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
                print("No laptop models found in database")
                return []
                
            print(f"Loading {len(models)} laptop models (limited from total)")
            
            # Create a list to store all laptop data in the same format as the JSON
            laptops = []
            total_models = len(models)
            
            # Use a more efficient approach with batch processing
            models_list = [model_row['model'] for model_row in models]
            
            # Create a mapping of models for faster lookups
            laptops_dict = {model: {'tables': []} for model in models_list}
            
            # Batch query for Product Details
            print("Loading product details...")
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
                print("Loading screen details...")
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
                print("Screen table not found, skipping...")
            
            # Check if the cpu table exists
            if 'cpu' in available_tables:
                # Batch query for Processor Details
                print("Loading processor details...")
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
                print("CPU table not found, skipping...")
            
            # Check if required tables exist for misc details
            gpu_exists = 'gpu' in available_tables
            storage_exists = 'storage' in available_tables
            
            # Batch query for Misc Details (conditionally based on table existence)
            print("Loading misc details...")
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
                print("Loading features...")
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
                print("Features table not found, skipping...")
            
            # Check if the ports table exists
            if 'ports' in available_tables:
                # Batch query for Ports
                print("Loading ports...")
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
                print("Ports table not found, skipping...")
            
            # Convert dictionary back to list
            laptops = list(laptops_dict.values())
            
            print(f"Successfully loaded {len(laptops)} laptops from database")
            return laptops
            
        except Exception as e:
            print(f"Error loading data from database: {str(e)}")
            return []
        finally:
            # Put the connection back into the connection pool as noted in the comments
            if conn and cur:
                try:
                    # Try to use the imported release function first
                    release_db_connection(conn, cur)
                    print("Database connection released using DBAccess module.")
                except NameError:
                    # If import failed, close directly
                    cur.close()
                    conn.close()
                    print("Database connection closed directly.")

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
        }
        
        return {key: self.model.encode(desc) for key, desc in features.items()}

    def _format_laptop_description(self, laptop: Dict) -> str:
        """
        Create a detailed description string from laptop specifications
        """
        tables = laptop['tables']
        details = {}
        
        # Extract relevant information from nested structure
        for table in tables:
            if 'data' in table:
                details.update(table['data'])
        
        # Create a more comprehensive description with available data
        brand = details.get('Brand', '')
        name = details.get('Name', '')
        processor = ""
        if 'Processor' in details:
            processor = f"{details['Processor'].get('Brand', '')} {details['Processor'].get('Name', '')}"
        else:
            # Try to find processor info elsewhere
            for table in tables:
                if table.get('title') == 'Processor' and 'data' in table:
                    processor = f"{table['data'].get('Brand', '')} {table['data'].get('Name', '')}"
                    break
        
        # Get other specs from the Misc table
        memory = ""
        storage = ""
        graphics = ""
        screen_size = ""
        resolution = ""
        
        # Extract from Misc table if it exists
        for table in tables:
            if table.get('title') == 'Misc' and 'data' in table:
                memory = table['data'].get('Memory Installed', '')
                storage = table['data'].get('Storage', '')
                graphics = table['data'].get('Graphics Card', '')
        
        # Extract screen info
        for table in tables:
            if table.get('title') == 'Screen' and 'data' in table:
                screen_size = table['data'].get('Size', '')
                resolution = table['data'].get('Resolution', '')
        
        # Build the description with available information
        description = f"{brand} {name}"
        
        if processor:
            description += f" with {processor} processor"
        
        if memory:
            description += f", {memory} RAM"
        
        if storage:
            description += f", {storage} storage"
        
        if screen_size or resolution:
            description += f", {screen_size} {resolution} display"
        
        if graphics:
            description += f", {graphics} graphics"
        
        return description

    def _filter_laptops(self, filters: Dict = None) -> List[Dict]:
        """
        Filter laptops based on user preferences
        """
        if not filters:
            return self.laptops

        filtered_laptops = self.laptops
        
        if 'size' in filters:
            filtered_laptops = [
                laptop for laptop in filtered_laptops 
                if any(table['title'] == 'Screen' and 
                      str(filters['size']) in str(table['data'].get('Size', ''))
                      for table in laptop['tables'])
            ]
            
        if 'brand' in filters:
            filtered_laptops = [
                laptop for laptop in filtered_laptops 
                if any(table['title'] == 'Product Details' and 
                      table['data'].get('Brand', '').lower() in 
                      [b.lower() for b in filters['brand']]
                      for table in laptop['tables'])
            ]

        return filtered_laptops

    def _get_laptop_embeddings(self, laptops: List[Dict]) -> List[np.ndarray]:
        """
        Create embeddings for laptop descriptions
        """
        descriptions = [self._format_laptop_description(laptop) for laptop in laptops]
        return self.model.encode(descriptions)

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
            "portable": ["portable", "light", "travel", "thin", "lightweight", "carry", "commute"]
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

    def process_input(self, user_input: str) -> Dict:
        """
        Process user input and return appropriate response
        """
        response = {
            "message": "",
            "recommendations": [],
            "next_question": None
        }

        # Encode user input
        user_embedding = self.model.encode(user_input)

        if self.conversation_state == "initial":
            # Find most relevant use case using embedding similarity
            similarities = {
                use_case: cosine_similarity([user_embedding], [emb])[0][0]
                for use_case, emb in self.feature_embeddings.items()
            }
            most_relevant = max(similarities.items(), key=lambda x: x[1])
            
            # Fallback to keyword matching if similarity is low
            if most_relevant[1] < 0.3:  # Threshold for low confidence
                keyword_use_case = self._keyword_based_use_case(user_input)
                print(f"Embedding similarity too low ({most_relevant[1]:.2f}), using keyword matching: {keyword_use_case}")
                self.user_preferences['use_case'] = keyword_use_case
            else:
                # Use the embedding similarity result
                self.user_preferences['use_case'] = most_relevant[0]
                print(f"Using embedding similarity ({most_relevant[1]:.2f}) for use case: {most_relevant[0]}")
            
            
            self.conversation_state = "size"
            response["message"] = f"I understand you're looking for a {self.user_preferences['use_case']} laptop."
            response["next_question"] = self.questions["size"]
            
        elif self.conversation_state == "size":
            # Extract screen size preference
            size_pref = None
            for size in ["13", "14", "15", "16", "17"]:
                if size in user_input:
                    size_pref = int(size)
                    break
            
            if size_pref:
                self.user_preferences['size'] = size_pref
                filtered_laptops = self._filter_laptops({'size': size_pref})
            else:
                filtered_laptops = self.laptops

            if filtered_laptops:
                laptop_embeddings = self._get_laptop_embeddings(filtered_laptops)
                use_case_embedding = self.feature_embeddings[self.user_preferences['use_case']]
                
                similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
                top_indices = np.argsort(similarities)[-3:][::-1]
                
                recommendations = [filtered_laptops[i] for i in top_indices]
                response["recommendations"] = []
                
                for laptop in recommendations:
                    brand = ""
                    name = ""
                    
                    # Extract brand and name from Product Details table
                    for table in laptop['tables']:
                        if table['title'] == 'Product Details' and 'data' in table:
                            brand = table['data'].get('Brand', '')
                            name = table['data'].get('Name', '')
                            break
                    
                    if brand and name:
                        response["recommendations"].append({
                            'brand': brand,
                            'name': name,
                            'specs': self._format_laptop_description(laptop)
                        })
                
                response["message"] = "Based on your preferences, here are some recommendations:"
            else:
                response["message"] = "I couldn't find any laptops matching your screen size preference. Would you like to see other options?"
            
            self.conversation_state = "brand"
            response["next_question"] = self.questions["brand"]
            
        elif self.conversation_state == "brand":
            # Extract brand preferences
            brands = [brand.strip() for brand in user_input.split(',')]
            
            # Special handling for "no" or "none" responses
            if len(brands) == 1 and brands[0].lower() in ["no", "none", "any", "no preference"]:
                response["message"] = "Got it, I won't filter by brand. Here are some recommendations based on your other preferences:"
                filtered_laptops = self._filter_laptops({
                    'size': self.user_preferences.get('size')
                })
            else:
                self.user_preferences['brand'] = brands
                filtered_laptops = self._filter_laptops({
                    'size': self.user_preferences.get('size'),
                    'brand': brands
                })
                response["message"] = "Here are your final personalized recommendations:"
                
            if filtered_laptops:
                laptop_embeddings = self._get_laptop_embeddings(filtered_laptops)
                use_case_embedding = self.feature_embeddings[self.user_preferences['use_case']]
                
                similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
                top_indices = np.argsort(similarities)[-3:][::-1]
                
                recommendations = [filtered_laptops[i] for i in top_indices]
                response["recommendations"] = []
                
                for laptop in recommendations:
                    brand = ""
                    name = ""
                    
                    # Extract brand and name from Product Details table
                    for table in laptop['tables']:
                        if table['title'] == 'Product Details' and 'data' in table:
                            brand = table['data'].get('Brand', '')
                            name = table['data'].get('Name', '')
                            break
                    
                    if brand and name:
                        response["recommendations"].append({
                            'brand': brand,
                            'name': name,
                            'specs': self._format_laptop_description(laptop)
                        })
            else:
                response["message"] = "I couldn't find any laptops matching all your criteria. Would you like to see other options?"
            
            self.conversation_state = "final"
        
        # Final state allows user to ask for different recommendations or restart
        elif self.conversation_state == "final":
            # Reset conversation if user wants to start over
            if any(term in user_input.lower() for term in ["restart", "start over", "new search"]):
                self.conversation_state = "initial"
                self.user_preferences = {}
                response["message"] = "Let's start over. " + self.questions["initial"]
            else:
                # Check if user is asking to see more options
                if any(term in user_input.lower() for term in ["yes", "sure", "okay", "more options", "show more"]):
                    # Show more recommendations with relaxed criteria
                    if 'brand' in self.user_preferences:
                        # Remove brand filter to get more options
                        filtered_laptops = self._filter_laptops({
                            'size': self.user_preferences.get('size')
                        })
                    else:
                        # If no brand filter, just get more recommendations
                        filtered_laptops = self.laptops
                    
                    if filtered_laptops:
                        laptop_embeddings = self._get_laptop_embeddings(filtered_laptops)
                        use_case_embedding = self.feature_embeddings[self.user_preferences['use_case']]
                        
                        similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
                        # Get the next batch of recommendations (positions 4-6)
                        top_indices = np.argsort(similarities)[-6:-3][::-1]
                        
                        recommendations = [filtered_laptops[i] for i in top_indices if i >= 0]
                        response["recommendations"] = []
                        
                        for laptop in recommendations:
                            brand = ""
                            name = ""
                            
                            # Extract brand and name from Product Details table
                            for table in laptop['tables']:
                                if table['title'] == 'Product Details' and 'data' in table:
                                    brand = table['data'].get('Brand', '')
                                    name = table['data'].get('Name', '')
                                    break
                            
                            if brand and name:
                                response["recommendations"].append({
                                    'brand': brand,
                                    'name': name,
                                    'specs': self._format_laptop_description(laptop)
                                })
                        
                        response["message"] = "Here are some additional options that might interest you:"
                    else:
                        response["message"] = "I don't have any more recommendations based on your criteria. Would you like to start a new search?"
                else:
                    # Process any other input in final state
                    response["message"] = "Would you like to explore a different type of laptop? Say 'restart' to begin a new search."

        return response

    def reset_conversation(self):
        """
        Reset the conversation state and user preferences
        """
        self.conversation_state = "initial"
        self.user_preferences = {}

def converse_with_chatbot(limit=10000):
    """
    Main function to run an interactive conversation with the laptop recommendation bot
    
    Args:
        limit: Maximum number of laptops to load (default: 100)
    """
    # Welcome message and instructions
    print("\n" + "="*50)
    print("Welcome to the Laptop Recommendation Bot!")
    print("="*50)
    print("This bot will help you find the perfect laptop based on your needs.")
    print("You can exit the conversation at any time by typing 'quit', 'exit', or 'bye'.")
    print("Type 'restart' to begin a new search.\n")
    print(f"Note: Loading limited to {limit} laptops for performance reasons.")
    
    # Initialize the chatbot with database connection
    try:
        print("Initializing chatbot and connecting to database...")
        chatbot = LaptopRecommendationBot()
        
        # Check if laptops were loaded
        if not chatbot.laptops:
            print("Error: No laptop data available. Please check your database connection.")
            return
            
        print(f"Chatbot initialized with {len(chatbot.laptops)} laptops from database!")
        
    except Exception as e:
        print(f"Error initializing the chatbot: {str(e)}")
        print("This could be due to issues with the SentenceTransformer model or database connection.")
        print("Make sure you have the required packages installed and the database is accessible.")
        return
    
    # Start the conversation with initial question
    print("\nBot:", chatbot.questions["initial"])
    
    # Main conversation loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to exit
            if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                print("\nBot: Thank you for using the Laptop Recommendation Bot. Goodbye!")
                break
                
            # Process user input
            response = chatbot.process_input(user_input)
            
            # Display bot response
            print("\nBot:", response["message"])
            
            # Display recommendations if any
            if response["recommendations"]:
                print("\nRecommended Laptops:")
                for i, laptop in enumerate(response["recommendations"], 1):
                    print(f"{i}. {laptop['brand']} {laptop['name']}")
                    print(f"   Specs: {laptop['specs']}")
                print()
            
            # Display next question if any
            if response["next_question"]:
                print("Bot:", response["next_question"])
                
        except KeyboardInterrupt:
            print("\n\nBot: Conversation interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nBot: I encountered an error processing your request: {str(e)}")
            print("Bot: Let's try again or type 'restart' to begin a new search.")

if __name__ == "__main__":
    # Run the interactive conversation with a limit of 100 laptops for performance
    converse_with_chatbot(limit=10000)