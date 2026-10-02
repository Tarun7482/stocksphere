import requests
import json

# Test connection to Ollama
try:
    response = requests.get("http://localhost:11434/api/version")
    print(f"Ollama connection: {response.status_code}")
    print(f"Version: {response.json()}")
except Exception as e:
    print(f"Error connecting to Ollama: {str(e)}")
    exit(1)

# Test model
try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:latest",
            "prompt": "Hello, how are you?",
            "stream": False
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result.get('response')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error generating response: {str(e)}") 