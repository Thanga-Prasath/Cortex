import datetime
import json
import random
import os

class GeneralEngine:
    def __init__(self, speaker):
        self.speaker = speaker
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
        # Dynamic Handlers (Logic)
        if tag == 'time':
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speaker.speak(f"The time is {current_time}, Sir.")
            return True
        
        elif tag == 'date':
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speaker.speak(f"Today is {current_date}, Sir.")
            return True

        # Static Responses (Text) from JSON
        # Find the intent block matches the tag
        for intent in self.data['intents']:
            if intent['tag'] == tag:
                if intent.get('responses'):
                    response = random.choice(intent['responses'])
                    self.speaker.speak(response)
                    return True
        
        return False

    def handle(self, command):
        """
        Legacy handler (Optional, kept if needed, but we rely on NLU now)
        """
        return False
