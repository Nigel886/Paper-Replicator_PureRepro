import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

# 1. Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Initialize Client
client = genai.Client(api_key=API_KEY)

print("--- Available Models ---")
try:
    for m in client.models.list():
        print(f"Model ID: {m.name}")
except Exception as e:
    print(f"List models failed: {e}")
print("------------------------\n")

def analyze_with_new_sdk(image_path):
    if not os.path.exists(image_path):
        print(f"❌ Bro, image not found: {image_path}")
        return

    try:
        print("🚀 Engaging Gemini via New SDK...")
        img = Image.open(image_path)
        
        response = client.models.generate_content(
            model="models/gemini-flash-latest", 
            contents=[
                "You are a world-class AI Architect. Please analyze this paper screenshot, "
                "extract its model logic, and implement the architecture using PyTorch code.",
                img
            ]
        )
        
        print("\n--- The Moment of Truth (New SDK) ---")
        if response.text:
            print(response.text)
        else:
            print("⚠️ Response is empty, bro. Check your safety settings or image.")
        
    except Exception as e:
        print(f"❌ Something went wrong, bro: {e}")

# 3. Execution
if __name__ == "__main__":
    analyze_with_new_sdk('paper_shot.png')