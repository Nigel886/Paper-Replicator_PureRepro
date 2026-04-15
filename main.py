import os
from dotenv import load_dotenv
from core.engine import PaperReplicator
from utils.file_handler import extract_and_save_code

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return

    # Initialize Replicator
    replicator = PaperReplicator(api_key)
    
    # Define your paper screenshots here
    # Now you can easily add more: ['page1.png', 'page2.png']
    paper_images = ['paper_shot.png'] 
    
    # Run Engine
    raw_response = replicator.analyze_paper_set(paper_images)
    
    # Handle Output
    if raw_response:
        print("\n--- Analysis Results ---")
        extract_and_save_code(raw_response)

if __name__ == "__main__":
    main()