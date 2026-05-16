import requests
import os
from dotenv import load_dotenv

def list_models():
    load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY")
    print(f"Key found: {key[:10]}...")
    
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {key}"}
    )
    
    if response.status_code == 200:
        models = response.json()["data"]
        print(f"Found {len(models)} models. Free models:")
        for m in models:
            if "free" in m["id"] or m.get("pricing", {}).get("prompt") == "0":
                print(f"- {m['id']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    list_models()
