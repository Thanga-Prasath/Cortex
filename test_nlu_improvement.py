from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import json
import numpy as np

# Load original data
with open('data/commands.json', 'r') as f:
    data = json.load(f)

patterns = []
tags = []
for intent in data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])

# 1. Baseline Model (Current)
print("--- Baseline Model (Word n-grams) ---")
vec_baseline = CountVectorizer(tokenizer=lambda x: x.split(), token_pattern=None, binary=True, ngram_range=(1, 2))
clf_baseline = LogisticRegression()
pipeline_baseline = make_pipeline(vec_baseline, clf_baseline)
pipeline_baseline.fit(patterns, tags)

# 2. Improved Model (Char n-grams)
print("\n--- Improved Model (Char n-grams) ---")
# analyzer='char_wb', ngram_range=(2, 4) captures subword features
vec_improved = CountVectorizer(analyzer='char_wb', ngram_range=(2, 4)) 
clf_improved = LogisticRegression(C=10) # Slightly stronger regularization maybe? or less? default is 1.0. Let's try default first or loose.
pipeline_improved = make_pipeline(vec_improved, clf_improved)
pipeline_improved.fit(patterns, tags)


test_phrases = [
    "parties to time", # User reported failure (Predicted 'time' but low conf)
    "system info",     # User reported low conf
    "exit",            # Worked
    "what is my ip",   # Standard
    "list files",      # Standard
    "sytem info",      # Typo
    "what tim is it",  # Typo
    "open the pod bay doors", # Out of domain
]

def predict(pipeline, text):
    probs = pipeline.predict_proba([text])[0]
    max_index = np.argmax(probs)
    return pipeline.classes_[max_index], probs[max_index]

print(f"{'Phrase':<25} | {'Baseline Tag':<15} {'Conf':<6} | {'Improved Tag':<15} {'Conf':<6}")
print("-" * 75)

for phrase in test_phrases:
    tag_b, conf_b = predict(pipeline_baseline, phrase)
    tag_i, conf_i = predict(pipeline_improved, phrase)
    print(f"{phrase:<25} | {tag_b:<15} {conf_b:.2f}   | {tag_i:<15} {conf_i:.2f}")
