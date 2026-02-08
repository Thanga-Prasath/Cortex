
def test_match():
    # What we have (Family Name)
    target = "Microsoft.WindowsCalculator_8wekyb3d8bbwe"
    
    # What tasklist gives (Full Name)
    actual = "Microsoft.WindowsCalculator_11.2508.4.0_x64__8wekyb3d8bbwe"
    
    print(f"Target: {target}")
    print(f"Actual: {actual}")
    
    # Current Logic
    match_simple = target.lower() in actual.lower()
    print(f"Simple substring match ('{target}' in '{actual}'): {match_simple}")
    
    # Improved Logic
    # Family Name: Name_PublisherId
    # Full Name: Name_Version_Arch_ResourceId_PublisherId
    
    if "_" in target:
        parts = target.split("_")
        name = parts[0]
        pub_id = parts[-1] 
        
        match_improved = actual.lower().startswith(name.lower()) and actual.lower().endswith(pub_id.lower())
        print(f"Improved match (Starts with '{name}' AND Ends with '{pub_id}'): {match_improved}")
    else:
        print("Target format unexpected.")

if __name__ == "__main__":
    test_match()
