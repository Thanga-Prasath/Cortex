import datetime
import json
import random
import os

class GeneralEngine:
    def __init__(self, speaker, user_config=None):
        self.speaker = speaker
        self.user_config = user_config if user_config else {"name": "Sir"}
        self.load_intents()

    def load_intents(self):
        try:
            path = os.path.join(os.getcwd(), 'data', 'commands.json')
            with open(path, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"Error loading commands: {e}")
            self.data = {"intents": []}

    def handle_intent(self, tag):
        """
        Executes action based on the identified tag.
        """
        user_name = self.user_config.get('name', 'Sir')
        
        # Dynamic Handlers (Logic)
        if tag == 'time':
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speaker.speak(f"The time is {current_time}, {user_name}.")
            return True
        
        elif tag == 'date':
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speaker.speak(f"Today is {current_date}, {user_name}.")
            return True

        # Static Responses (Text) from JSON
        # Find the intent block matches the tag
        for intent in self.data['intents']:
            if intent['tag'] == tag:
                if intent.get('responses'):
                    response = random.choice(intent['responses'])
                    # Format response with name if placeholder exists
                    try:
                        formatted_response = response.format(name=user_name)
                    except Exception:
                        formatted_response = response
                    
                    self.speaker.speak(formatted_response)
                    return True
        
        return False

    def handle(self, command):
        """
        Legacy handler (Optional, kept if needed, but we rely on NLU now)
        """
        return False
