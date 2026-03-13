import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)  # Force .env file to override environment variables
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit(1)

# Test using REST API
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

payload = {
    "contents": [
        {
            "parts": [
                {"text": "Explain AI in 2 lines"}
            ]
        }
    ]
}

response = requests.post(
    url,
    json=payload,
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
)

if response.status_code == 200:
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    print("✅ API Key is valid!")
    print(f"Response: {text}")
else:
    print(f"❌ API Error ({response.status_code})")
    print(response.text)