import json
import os
import pickle
import glob
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from difflib import SequenceMatcher

class NeuralIntentModel:
    def __init__(self, data_dir="data/intents", model_file="data/model.pkl"):
        self.data_dir = data_dir
        self.model_file = model_file
        self.vectorizer = CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        self.classifier = LogisticRegression(C=10.0)
        self.intents = []
        self.tags = []
        self.patterns = []
        # Store keywords for boosting: {tag: [keywords]}
        self.intent_keywords = {} 
        self.training_data = {"intents": []}
        
        # Load and Train immediately
        self.load_data()
        self.train()

    def load_data(self):
        self.training_data = {"intents": []}
        
        # Check if directory exists
        if not os.path.exists(self.data_dir):
            print(f"Error: {self.data_dir} directory not found.")
            return

        # Iterate over all .json files in data/intents/
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        
        if not json_files:
             print(f"Warning: No JSON files found in {self.data_dir}")

        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'intents' in data:
                        self.training_data['intents'].extend(data['intents'])
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        # Process loaded intents
        for intent in self.training_data['intents']:
            tag = intent['tag']
            
            # Store keywords if present
            if 'keywords' in intent:
                self.intent_keywords[tag] = [k.lower() for k in intent['keywords']]

            for pattern in intent['patterns']:
                self.patterns.append(pattern)
                self.tags.append(tag)
            
            if tag not in self.intents:
                self.intents.append(tag)
                
        print(f"NLU: Loaded {len(self.intents)} intents from {len(json_files)} files.")

    def train(self):
        print("Training NLU Model...")
        if not self.patterns:
            print("Error: No patterns to train on.")
            return

        try:
            X = self.vectorizer.fit_transform(self.patterns)
            y = self.tags
            self.classifier.fit(X, y)
            print("Model Trained Successfully.")
        except ValueError as e:
            print(f"Error during training: {e}")

    def predict(self, text):
        """
        Returns (Intent, Probability)
        """
        if not text:
            return None, 0.0
        
        text = text.lower()

        # --- 1. Keyword Boosting (Dynamic Logic) ---
        # Checks if ALL keywords for a specific intent are present in the text.
        # If so, boost confidence to 1.0 immediately.
        for tag, keywords in self.intent_keywords.items():
            if not keywords: continue
            
            # Check if all keywords are in the text
            # Logic: If query is "set volume up" and keywords for 'media_control' are ['volume'], it matches.
            # But we need to be careful. Let's look for strong matches.
            # Strategy: If the input contains specific unique keywords, boost it.
            
            # Simple Strict Match: If any single keyword is a multi-word phrase in the text? 
            # Or if ALL keywords in the list are present?
            # Let's go with: If ANY of the 'keywords' list is in the input? 
            # No, that's too loose (e.g. 'time' keyword matches 'time for bed' -> 'time' tag).
            # Existing hardcoded logic was: if ' memory ' in text -> system_memory.
            
            # Let's iterate and see if any keyword *phrase* is in the text.
            # Let's iterate and see if any keyword *phrase* is in the text.
            for keyword in keywords:
                # pad with spaces to match whole words if short
                padded_text = f" {text} "
                padded_keyword = f" {keyword} "
                
                # Check 1: Exact word boundary match for ALL keywords (prevents "sopen", "opening")
                if padded_keyword in padded_text:
                    
                     # Check 2: Uniqueness/Length Heuristic
                     # If it's a single word and very short/common, be careful.
                     # We trust that the JSON files should NOT contain generic single words like "open"
                     # if they are not unique enough.
                     # However, to be safe, let's say if it's a single word < 5 chars, we might require more context?
                     # Actually, the best fix is to remove generic words from JSON and trust this logic:
                     
                     print(f"NLU: Keyword Boost '{keyword}' -> {tag}")
                     return tag, 1.0
        
        # --- 2. Fuzzy Matching (Closest Match) ---
        best_match_tag = None
        best_match_score = 0.0
        best_match_pattern = ""

        # Optimization: Don't scan everything if text is very long
        if len(text) < 100:
            for i in range(len(self.patterns)):
                pattern = self.patterns[i]
                score = SequenceMatcher(None, text, pattern.lower()).ratio()
                
                if score > best_match_score:
                    best_match_score = score
                    best_match_tag = self.tags[i]
                    best_match_pattern = pattern

            if best_match_score > 0.85:
                print(f"NLU: Fuzzy Match '{text}' -> '{best_match_pattern}' ({best_match_tag}) Score: {best_match_score:.2f}")
                return best_match_tag, 1.0

        # --- 3. ML Classifier Fallback ---
        try:
            X_input = self.vectorizer.transform([text])
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
                all_phrases.append(intent['tag'].replace("_", " "))
                for pattern in intent['patterns']:
                    all_phrases.append(pattern)
        
        unique_phrases = list(set(all_phrases))
        return ", ".join(unique_phrases)
