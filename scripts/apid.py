#!/usr/bin/env python3
"""
Diagnostic script for Google Genai API
This will help identify the correct API configuration and available models
"""

import sys

def test_google_genai():
    """Test the google-genai package"""
    print("=" * 70)
    print("GOOGLE GENAI API DIAGNOSTICS")
    print("=" * 70)
    
    # Get API key
    api_key = input("\nEnter your Google AI Studio API key: ").strip()
    
    if not api_key:
        print("Error: API key is required")
        return
    
    print("\n" + "=" * 70)
    print("TEST 1: Import and Version Check")
    print("=" * 70)
    
    try:
        from google import genai
        print("✓ google.genai imported successfully")
        
        # Try to get version
        try:
            print(f"  Version: {genai.__version__}")
        except:
            print("  Version: Unknown")
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        print("\nTry: pip install --upgrade google-genai")
        return
    
    print("\n" + "=" * 70)
    print("TEST 2: Client Initialization")
    print("=" * 70)
    
    try:
        client = genai.Client(api_key=api_key)
        print("✓ Client created successfully")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return
    
    print("\n" + "=" * 70)
    print("TEST 3: List Models (Method 1 - models.list)")
    print("=" * 70)
    
    try:
        print("Attempting: client.models.list()")
        models = client.models.list()
        print("✓ Models list retrieved")
        
        count = 0
        for model in models:
            count += 1
            print(f"\n  Model {count}:")
            print(f"    Name: {getattr(model, 'name', 'N/A')}")
            print(f"    Display Name: {getattr(model, 'display_name', 'N/A')}")
            print(f"    Description: {getattr(model, 'description', 'N/A')[:100]}")
            
            # Try to get supported methods
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Supported methods: {model.supported_generation_methods}")
        
        if count == 0:
            print("  ⚠ No models found")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "=" * 70)
    print("TEST 4: Try Common Model Names")
    print("=" * 70)
    
    test_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash-latest",
        "gemini-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro-001",
    ]
    
    working_models = []
    
    for model_name in test_models:
        try:
            print(f"\nTrying: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents="Say 'test successful' if you can read this."
            )
            print(f"  ✓ SUCCESS! Response: {response.text[:50]}")
            working_models.append(model_name)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"  ✗ Not found (404)")
            elif "403" in error_msg:
                print(f"  ✗ Permission denied (403)")
            else:
                print(f"  ✗ Error: {error_msg[:100]}")
    
    print("\n" + "=" * 70)
    print("TEST 5: Alternative Import Method")
    print("=" * 70)
    
    try:
        import google.generativeai as genai_alt
        print("✓ google.generativeai imported successfully")
        print("  (This is the OLD library - might work better)")
        
        try:
            genai_alt.configure(api_key=api_key)
            print("✓ Configured with API key")
            
            models = genai_alt.list_models()
            print("\nAvailable models via OLD library:")
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    print(f"  • {m.name}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            print("  Try: pip install google-generativeai")
    except ImportError:
        print("✗ google.generativeai not installed")
        print("  To try the old library: pip install google-generativeai")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if working_models:
        print(f"\n✓ Found {len(working_models)} working model(s):")
        for model in working_models:
            print(f"  • {model}")
        print(f"\nUse this in your script:")
        print(f'  model="{working_models[0]}"')
    else:
        print("\n✗ No working models found")
        print("\nTroubleshooting steps:")
        print("1. Verify your API key at: https://aistudio.google.com/apikey")
        print("2. Check if Gemini API is enabled for your project")
        print("3. Try the old library: pip install google-generativeai")
        print("4. Check for regional restrictions")

if __name__ == "__main__":
    test_google_genai()