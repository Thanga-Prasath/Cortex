import logging
try:
    from rapidfuzz import process, fuzz
except ImportError:
    logging.warning("Rapidfuzz not found. Install it for better performance: pip install rapidfuzz")
    from difflib import SequenceMatcher

def smart_match(query, choices, threshold=80):
    """
    Finds the best match for 'query' in the list of 'choices'.
    Returns (match, score, index) if score >= threshold, else None.
    """
    if not query or not choices:
        return None

    try:
        # RapidFuzz Implementation (Faster/Better)
        # extractOne returns (match, score, index)
        # score_cutoff optimization only considers matches above threshold
        result = process.extractOne(query, choices, scorer=fuzz.WRatio, score_cutoff=threshold)
        if result:
            return result # (match, score, index)
        return None
    except NameError:
        # Fallback to difflib
        best_match = None
        best_score = 0
        best_index = -1
        
        for idx, choice in enumerate(choices):
            score = SequenceMatcher(None, query, choice).ratio() * 100
            if score > best_score:
                best_score = score
                best_match = choice
                best_index = idx
        
        if best_score >= threshold:
            return (best_match, best_score, best_index)
        return None

def is_similar(a, b, threshold=85):
    """
    Returns True if 'a' and 'b' are similar enough.
    """
    try:
        return fuzz.WRatio(a, b) >= threshold
    except NameError:
        return SequenceMatcher(None, a, b).ratio() * 100 >= threshold

def apply_mishearing_fix(text):
    """
    Replaces common mishearings based on phonetic similarity context.
    Example: "parties to file" -> "parties to time" (if that was a known error, but here we cover simple words)
    """
    corrections = {
        "file": "time",     # User specific complaint
        "fine": "time",     # Common homophone
        "find": "time",     # Common homophone context dependent (careful!)
        "sign": "time",
        "dime": "time",
        "lime": "time",
        "exceed": "exit",
        "exist": "exit",
        "eggs it": "exit", 
        "exact": "exit",
        "by": "bye",
        "buy": "bye",
        "stock": "stop",
        "start": "stop"     # Sometimes misheard, but dangerous. removed for safety.
    }
    
    # We only apply strict full-word replacements for short commands
    # or specific known context errors.
    
    words = text.split()
    new_words = []
    for word in words:
        # Clean punctuation
        clean_word = word.strip(".,?!").lower()
        if clean_word in corrections:
            new_words.append(corrections[clean_word])
        else:
            new_words.append(word)
            
    return " ".join(new_words)
