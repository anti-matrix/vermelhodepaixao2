import requests
import json
import time

url = "http://localhost:11435/api/generate"

payload = {
    "model": "tinyllama",
    "prompt": "Hello",
    "stream": False,
    "options": {
        "num_gpu": 30,  # Start with fewer layers
        "num_ctx": 2048,  # Smaller context
        "temperature": 0.7
    }
}

print("Sending request...")
try:
    response = requests.post(url, json=payload, timeout=120)  # 120 seconds timeout
    if response.status_code == 200:
        print("✓ Success!")
        result = response.json()
        print(f"Response: {result['response']}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
except requests.exceptions.Timeout:
    print("✗ Timeout! Model taking too long to load.")
    print("Try reducing --num-gpu or using CPU only.")
except Exception as e:
    print(f"✗ Exception: {e}")