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
        # Store carrier phrases for strict prefix matching: {tag: [phrases]}
        self.intent_carrier_phrases = {}
        self.training_data = {"intents": []}
        
        # Custom Logic Configuration
        self.SYNONYM_GROUPS = {
             "open": ["open", "launch", "start", "run", "fire up", "execute", "open up"],
             "close": ["close", "quit", "exit", "terminate", "kill", "stop", "shut down"],
             "list": ["list", "show", "check", "display", "what are", "see"],
             "app": ["app", "application", "program", "software", "tool"],
             "system": ["system", "pc", "computer", "machine", "windows"]
        }
        
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
                
            # Store carrier phrases if present
            if 'carrier_phrases' in intent:
                self.intent_carrier_phrases[tag] = [cp.lower() for cp in intent['carrier_phrases']]

            for pattern in intent['patterns']:
                self.patterns.append(pattern)
                self.tags.append(tag)
                
                # --- AUTOMATED PATTERN AUGMENTATION ---
                # Add common polite prefixes automatically
                prefixes = ["please ", "can you ", "could you ", "i want to ", "go ahead and ", "assistant "]
                for pref in prefixes:
                    self.patterns.append(pref + pattern)
                    self.tags.append(tag)
            
            if tag not in self.intents:
                self.intents.append(tag)
                
            # Store anchors if present
            if 'anchors' in intent:
                if not hasattr(self, 'intent_anchors'):
                    self.intent_anchors = {}
                self.intent_anchors[tag] = [a.lower() for a in intent['anchors']]
                
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
        
        # --- -1. Strict Carrier Phrase Matching (Highest Priority) ---
        # If the input strictly starts with a defined carrier phrase for an intent,
        # we immediately execute it. This protects open-ended intents (like file search)
        # from being overshadowed by generic nouns (like "traffic", "port") that might
        # match system intents.
        best_carrier_tag = None
        max_carrier_len = 0
        
        # Ensure we pad text to match whole words exactly at the start
        padded_text_start = text + " "
        
        for tag, phrases in self.intent_carrier_phrases.items():
            for phrase in phrases:
                # Carrier phrases must appear at the VERY START of the utterance
                test_phrase = phrase + " "
                if padded_text_start.startswith(test_phrase):
                    # In case of overlapping carrier phrases (e.g. "search" vs "search for"), pick the longest
                    if len(phrase) > max_carrier_len:
                        max_carrier_len = len(phrase)
                        best_carrier_tag = tag
                        
        if best_carrier_tag:
             print(f"NLU: Carrier Phrase Match '{best_carrier_tag}' (Length: {max_carrier_len})")
             return best_carrier_tag, 1.0

        # --- 0. Anchor Filtering (Domain Guard) ---
        # Checks if ALL keywords for a specific intent are present in the text.
        # If so, boost confidence to 1.0 immediately.
        # --- 0. Anchor Filtering (Domain Guard) ---
        # If an intent has 'anchors' defined, the text MUST contain at least one anchor.
        # Otherwise, the intent is disqualified from both Keyword Boost and Fuzzy Match.
        valid_intents = set(self.intents)
        if hasattr(self, 'intent_anchors'):
            for tag, anchors in self.intent_anchors.items():
                if tag in valid_intents:
                    # Check if any anchor (or its synonym) is in text
                    has_anchor = False
                    for anchor in anchors:
                        if anchor in text:
                            has_anchor = True
                            break
                        # Check synonym groups
                        syn_group = self.SYNONYM_GROUPS.get(anchor)
                        if syn_group and any(syn in text for syn in syn_group):
                            has_anchor = True
                            break
                    
                    if not has_anchor:
                        valid_intents.discard(tag)
        
        # --- 1. Keyword Boosting (Dynamic Logic) ---
        # Strategy: Find the intent with the LONGEST matching keyword phrase.
        # This prevents generic keywords (e.g., "wifi") from shadowing specific ones (e.g., "wifi password").
        
        best_keyword_match_tag = None
        max_keyword_len = 0
        
        for tag, keywords in self.intent_keywords.items():
            if tag not in valid_intents: continue # Skip disqualified intents
            if not keywords: continue
            
            for keyword in keywords:
                # pad with spaces to match whole words if short
                padded_text = f" {text} "
                padded_keyword = f" {keyword} "
                
                # Check 1: Exact word boundary match for ALL keywords
                if padded_keyword in padded_text:
                     # Check length of the matched keyword
                     k_len = len(keyword)
                     if k_len > max_keyword_len:
                         max_keyword_len = k_len
                         best_keyword_match_tag = tag
        
        if best_keyword_match_tag:
             print(f"NLU: Keyword Boost '{best_keyword_match_tag}' (Length: {max_keyword_len})")
             return best_keyword_match_tag, 1.0
        
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
                # Check validity
                if best_match_tag in valid_intents:
                    print(f"NLU: Fuzzy Match '{text}' -> '{best_match_pattern}' ({best_match_tag}) Score: {best_match_score:.2f}")
                    return best_match_tag, 1.0

        # --- 3. ML Classifier Fallback ---
        try:
            X_input = self.vectorizer.transform([text])
            probs = self.classifier.predict_proba(X_input)[0]
            
            # Enforce Semantic Guard (Anchors) on ML results
            # Set probability of invalid intents to 0
            for i, tag in enumerate(self.classifier.classes_):
                if tag not in valid_intents:
                    probs[i] = 0.0
            
            # Re-normalize or just take max? Just max is fine.
            if np.sum(probs) == 0:
                return None, 0.0
                
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
