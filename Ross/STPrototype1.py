# ST stands for sentence transformer 
# This will be the first version prototype of how everything will be running
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import json

class LaptopRecommendationBot:
    def __init__(self, laptop_data: List[Dict]):
        """
        Initialize the chatbot with laptop data and load the sentence transformer model
        
        Args:
            laptop_data: List of dictionaries containing laptop information
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.laptops = laptop_data
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

        return response

#Simulated conversation
def sample_conversation(laptop_data):
    chatbot = LaptopRecommendationBot(laptop_data)
    
    # Initial user input
    print("User: I need a laptop for programming and software development")
    response = chatbot.process_input("I need a laptop for programming and software development")
    print("Bot:", response["message"])
    print("Bot:", response["next_question"])
    
    # Screen size preference
    print("\nUser: I prefer a 16-inch screen")
    response = chatbot.process_input("I prefer a 16-inch screen")
    print("Bot:", response["message"])
    if response["recommendations"]:
        for i, laptop in enumerate(response["recommendations"], 1):
            print(f"{i}. {laptop['brand']} {laptop['name']}")
            print(f"   Specs: {laptop['specs']}")
    print("Bot:", response["next_question"])
    
    # Brand preference
    print("\nUser: I prefer Dell or MSI")
    response = chatbot.process_input("I prefer Dell or MSI")
    print("Bot:", response["message"])
    if response["recommendations"]:
        for i, laptop in enumerate(response["recommendations"], 1):
            print(f"{i}. {laptop['brand']} {laptop['name']}")
            print(f"   Specs: {laptop['specs']}")
    
    return chatbot

if __name__ == "__main__":
    # Load laptop data from the provided JSON
    with open('../Sam/python_convert/V2/scraped_data.json', 'r') as f:
        laptop_data = json.load(f)
    
    chatbot = sample_conversation(laptop_data)