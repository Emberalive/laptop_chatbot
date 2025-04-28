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


# Import database connection from dbAccess
try:
    sys.path.append('../Sam/server_side/DBAccess')
    from DBAccess.dbAccess import get_db_connection
    from DBAccess.dbAccess import release_db_connection
except ImportError:
    print("Warning: Could not import db_access module. Using direct connection.")

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

    def load_from_database(self) -> List[Dict]:
        """
        Load laptop data from PostgreSQL database
        
        Returns:
            List of dictionaries containing laptop information in the same format as the JSON
        """
        try:
            # Try to use the imported db_access function
            try:
                conn, cur = get_db_connection()
            except NameError:
                # If import failed, connect directly
                conn = psycopg2.connect(
                    database="laptopchatbot",
                    user="samuel",
                    host="86.19.219.159",
                    password="QwErTy1243!",
                    port=5432
                )
            
            print("Connected to database successfully!")
            
            # Get all laptop models
            cur.execute("SELECT model FROM laptops")
            models = cur.fetchall()
            
            if not models:
                print("No laptop models found in database")
                return []
                
            print(f"Found {len(models)} laptop models in database")
            
            # Create a list to store all laptop data in the same format as the JSON
            laptops = []
            
            # For each laptop model, fetch all related information
            for model_row in models:
                model = model_row['model']
                laptop_data = {'tables': []}
                
                # Get Product Details
                cur.execute("""
                    SELECT model as "Name", brand as "Brand", weight as "Weight"
                    FROM laptops WHERE model = %s
                """, (model,))
                product_details = cur.fetchone()
                if product_details:
                    laptop_data['tables'].append({
                        'title': 'Product Details',
                        'data': dict(product_details)
                    })
                
                # Get Screen Details
                cur.execute("""
                    SELECT s.screen_resolution as "Resolution", s.refresh_rate as "Refresh Rate", 
                           s.touch_screen as "Touchscreen", l.screen_size as "Size"
                    FROM screen s
                    JOIN laptops l ON s.laptop_model = l.model
                    WHERE s.laptop_model = %s
                """, (model,))
                screen_details = cur.fetchone()
                if screen_details:
                    laptop_data['tables'].append({
                        'title': 'Screen',
                        'data': dict(screen_details)
                    })
                
                # Get Processor Details
                cur.execute("""
                    SELECT brand as "Brand", model as "Name"
                    FROM cpu WHERE laptop_model = %s
                """, (model,))
                processor_details = cur.fetchone()
                if processor_details:
                    laptop_data['tables'].append({
                        'title': 'Processor',
                        'data': dict(processor_details)
                    })
                
                # Get Misc Details (GPU, Memory, Storage, OS)
                cur.execute("""
                    SELECT 
                        g.model as "Graphics Card",
                        l.memory_installed as "Memory Installed",
                        s.storage_amount || ' ' || s.storage_type as "Storage",
                        l.operating_system as "Operating System",
                        l.battery_life as "Battery Life"
                    FROM laptops l
                    LEFT JOIN gpu g ON l.model = g.laptop_model
                    LEFT JOIN storage s ON l.model = s.laptop_model
                    WHERE l.model = %s
                """, (model,))
                misc_details = cur.fetchone()
                if misc_details:
                    laptop_data['tables'].append({
                        'title': 'Misc',
                        'data': dict(misc_details)
                    })
                
                # Get Features
                cur.execute("""
                    SELECT backlit_keyboard as "Backlit Keyboard", 
                           num_pad as "Numeric Keyboard",
                           bluetooth as "Bluetooth"
                    FROM features
                    WHERE laptop_model = %s
                """, (model,))
                features_details = cur.fetchone()
                if features_details:
                    laptop_data['tables'].append({
                        'title': 'Features',
                        'data': dict(features_details)
                    })
                
                # Get Ports
                cur.execute("""
                    SELECT hdmi as "HDMI", ethernet as "Ethernet (RJ45)", 
                           thunderbolt as "Thunderbolt", type_c as "USB Type-C"
                    FROM ports
                    WHERE laptop_model = %s
                """, (model,))
                ports_details = cur.fetchone()
                if ports_details:
                    laptop_data['tables'].append({
                        'title': 'Ports',
                        'data': dict(ports_details)
                    })
                
                # Add this laptop to our list
                laptops.append(laptop_data)
            
            # Close cursor but keep connection for possible future use
            cur.close()
            
            print(f"Successfully loaded {len(laptops)} laptops from database")
            return laptops
            
        except Exception as e:
            print(f"Error loading data from database: {str(e)}")
            return []

    def _create_feature_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Create embeddings for predefined features and use cases
        """
        features = {
            "gaming": """high-performance laptop with dedicated graphics card, 
                     high refresh rate display, powerful processor""",
            "business": """professional laptop with good battery life, 
                       portable design, windows professional""",
            "student": """affordable laptop with good battery life, 
                      portable, sufficient storage for documents""",
            "design": """laptop with high-resolution display, color accuracy, 
                     powerful graphics capabilities""",
            "programming": """laptop with good processor, sufficient RAM, 
                         comfortable keyboard and display""",
            "portable": """lightweight laptop with long battery life, 
                       compact size, good build quality"""
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
            details.update(table['data'])
        
        return f"{details.get('Brand', '')} {details.get('Name', '')} with " \
               f"{details.get('Processor', {}).get('Name', '')} processor, " \
               f"{details.get('Misc', {}).get('Memory Installed', '')} RAM, " \
               f"{details.get('Misc', {}).get('Storage', '')}, " \
               f"{details.get('Screen', {}).get('Size', '')} {details.get('Screen', {}).get('Resolution', '')} display, " \
               f"{details.get('Misc', {}).get('Graphics Card', '')} graphics"

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
            # Find most relevant use case
            similarities = {
                use_case: cosine_similarity([user_embedding], [emb])[0][0]
                for use_case, emb in self.feature_embeddings.items()
            }
            most_relevant = max(similarities.items(), key=lambda x: x[1])
            
            self.user_preferences['use_case'] = most_relevant[0]
            self.conversation_state = "size"
            response["message"] = f"I understand you're looking for a {most_relevant[0]} laptop."
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
                response["recommendations"] = [
                    {
                        'brand': next(table['data']['Brand'] 
                                    for table in laptop['tables'] 
                                    if table['title'] == 'Product Details'),
                        'name': next(table['data']['Name'] 
                                   for table in laptop['tables'] 
                                   if table['title'] == 'Product Details'),
                        'specs': self._format_laptop_description(laptop)
                    }
                    for laptop in recommendations
                ]
                
                response["message"] = "Based on your preferences, here are some recommendations:"
            else:
                response["message"] = "I couldn't find any laptops matching your screen size preference. Would you like to see other options?"
            
            self.conversation_state = "brand"
            response["next_question"] = self.questions["brand"]
            
        elif self.conversation_state == "brand":
            # Extract brand preferences
            brands = [brand.strip() for brand in user_input.split(',')]
            self.user_preferences['brand'] = brands
            
            filtered_laptops = self._filter_laptops({
                'size': self.user_preferences.get('size'),
                'brand': brands
            })
            
            if filtered_laptops:
                laptop_embeddings = self._get_laptop_embeddings(filtered_laptops)
                use_case_embedding = self.feature_embeddings[self.user_preferences['use_case']]
                
                similarities = cosine_similarity([use_case_embedding], laptop_embeddings)[0]
                top_indices = np.argsort(similarities)[-3:][::-1]
                
                recommendations = [filtered_laptops[i] for i in top_indices]
                response["recommendations"] = [
                    {
                        'brand': next(table['data']['Brand'] 
                                    for table in laptop['tables'] 
                                    if table['title'] == 'Product Details'),
                        'name': next(table['data']['Name'] 
                                   for table in laptop['tables'] 
                                   if table['title'] == 'Product Details'),
                        'specs': self._format_laptop_description(laptop)
                    }
                    for laptop in recommendations
                ]
                
                response["message"] = "Here are your final personalized recommendations:"
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
                # Process any other input in final state
                response["message"] = "Would you like to explore a different type of laptop? Say 'restart' to begin a new search."

        return response

    def reset_conversation(self):
        """
        Reset the conversation state and user preferences
        """
        self.conversation_state = "initial"
        self.user_preferences = {}

def converse_with_chatbot():
    """
    Main function to run an interactive conversation with the laptop recommendation bot
    """
    # Welcome message and instructions
    print("\n" + "="*50)
    print("Welcome to the Laptop Recommendation Bot!")
    print("="*50)
    print("This bot will help you find the perfect laptop based on your needs.")
    print("You can exit the conversation at any time by typing 'quit', 'exit', or 'bye'.")
    print("Type 'restart' to begin a new search.\n")
    
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
#put the connection back into the connection pool
#call this method "release_db_connection(conn, cur)" passed variables are the connection and the cursor that you have open

if __name__ == "__main__":
    # Run the interactive conversation directly without loading from JSON
    converse_with_chatbot()