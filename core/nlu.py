import json
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

class NeuralIntentModel:
    def __init__(self, data_file="data/commands.json", model_file="data/model.pkl"):
        self.data_file = data_file
        self.model_file = model_file
        self.vectorizer = CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        self.classifier = LogisticRegression(C=10.0)
        self.intents = []
        self.tags = []
        self.patterns = []
        self.training_data = None
        
        # Load and Train immediately (Fast for small datasets)
        self.load_data()
        self.train()

    def load_data(self):
        if not os.path.exists(self.data_file):
            print(f"Error: {self.data_file} not found.")
            return

        try:
            with open(self.data_file, 'r') as f:
                self.training_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {self.data_file} contains invalid JSON.")
            self.training_data = {"intents": []}
        except Exception as e:
            print(f"Error loading {self.data_file}: {e}")
            self.training_data = {"intents": []}

        for intent in self.training_data['intents']:
            tag = intent['tag']
            for pattern in intent['patterns']:
                self.patterns.append(pattern)
                self.tags.append(tag)
            
            if tag not in self.intents:
                self.intents.append(tag)

    def train(self):
        print("Training NLU Model...")
        # Vectorize patterns
        try:
            X = self.vectorizer.fit_transform(self.patterns)
            y = self.tags
            
            # Train Classifier
            self.classifier.fit(X, y)
            print("Model Trained Successfully.")
        except ValueError:
            print("Error: Not enough data to train. Add more patterns.")

    def predict(self, text):
        """
        Returns (Intent, Probability)
        """
        if not text:
            return None, 0.0

        # --- 1. Fuzzy Matching (Closest Match) ---
        # "Execute the very closest match instead of first match"
        from difflib import SequenceMatcher
        
        best_match_tag = None
        best_match_score = 0.0
        best_match_pattern = ""

        # Check against all known patterns
        for i in range(len(self.patterns)):
            pattern = self.patterns[i]
            input_text = text.lower()
            pattern_text = pattern.lower()

            # Using ratio() for similarity (0.0 to 1.0)
            score = SequenceMatcher(None, input_text, pattern_text).ratio()
            
            if score > best_match_score:
                best_match_score = score
                best_match_tag = self.tags[i]
                best_match_pattern = pattern

        # If we have a very strong match (> 0.8), prefer it over the classifier
        if best_match_score > 0.8:
            print(f"NLU: Fuzzy Match '{text}' -> '{best_match_pattern}' ({best_match_tag}) Score: {best_match_score:.2f}")
            return best_match_tag, 1.0

        # --- 2. ML Classifier Fallback ---
        try:
            # Transform input
            X_input = self.vectorizer.transform([text])
            
            # Predict
            probs = self.classifier.predict_proba(X_input)[0]
            max_index = np.argmax(probs)
            confidence = probs[max_index]
            predicted_tag = self.classifier.classes_[max_index]
            
            return predicted_tag, confidence
        except:
            return None, 0.0

    def get_vocabulary_phrase(self):
        """
        Generates a comma-separated string of all patterns to help Whisper's context.
        """
        all_phrases = []
        if self.training_data and 'intents' in self.training_data:
            for intent in self.training_data['intents']:
                # Add the tag itself (often a good keyword)
                all_phrases.append(intent['tag'].replace("_", " "))
                # Add patterns
                for pattern in intent['patterns']:
                    all_phrases.append(pattern)
        
        # Deduplicate and join
        unique_phrases = list(set(all_phrases))
        # Limit length if necessary, but base.en handles acceptable context length
        return ", ".join(unique_phrases)
