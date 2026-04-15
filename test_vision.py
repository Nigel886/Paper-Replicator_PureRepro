import os
import re
import time
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class PaperReplicator:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_id = "models/gemini-flash-latest"

    # --- UPDATED: Accepts a list of image paths ---
    def analyze_paper_set(self, image_paths, output_file="replicated_model.py"):
        """
        Analyze multiple paper screenshots as a context set to extract PyTorch code.
        """
        valid_images = []
        for path in image_paths:
            if os.path.exists(path):
                valid_images.append(Image.open(path))
            else:
                print(f"⚠️ Warning: File not found at {path}, skipping.")

        if not valid_images:
            print("❌ Error: No valid images to analyze.")
            return

        for attempt in range(3):
            try:
                print(f"🚀 [Attempt {attempt+1}] Analyzing {len(valid_images)} images via Gemini...")
                
                # Build contents list: Instructions + All Images
                prompt_content = [
                    "These images are parts of the same academic paper. Please analyze them collectively. \n\n"
                    "You are a Senior AI Research Engineer specializing in computer vision and deep learning. "
                    "Your mission is to analyze academic paper screenshots and provide high-quality, "
                    "production-ready PyTorch code. \n\n"
                    "Rules:\n"
                    "1. Focus on the core model architecture (layers, forward pass, activation functions).\n"
                    "2. Always include tensor shape comments for each major operation (e.g., # [B, 64, 56, 56]).\n"
                    "3. Use modular design (subclassing nn.Module).\n"
                    "4. If multiple interpretations exist, choose the most standard one in modern research."
                ]
                
                # Add all images to the contents list
                prompt_content.extend(valid_images)

                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt_content
                )
                
                print("\n--- Model Analysis Result ---")
                if response.text:
                    print(response.text)
                    self._extract_and_save(response.text, output_file)
                
                return response.text

            except Exception as e:
                if "429" in str(e) or "503" in str(e):
                    wait = (attempt + 1) * 15
                    print(f"⏳ Server busy. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"❌ Critical Error: {e}")
                    break
        return None

    def _extract_and_save(self, text, filename):
        code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
        if code_match:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code_match.group(1))
            print(f"\n✅ Success: PyTorch code saved to {filename}")

if __name__ == "__main__":
    replicator = PaperReplicator()
    # Now you can pass a list! 
    # Example: ['arch.png', 'formula.png']
    replicator.analyze_paper_set(['paper_shot.png'])