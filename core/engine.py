import google.generativeai as genai
import os
import PIL.Image
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .processors import DualStageProcessor

class PaperReplicator:
    def __init__(self, api_key):
        """
        Initialize the Gemini engine with the stable production model.
        """
        if not api_key:
            print("[Critical] API Key is missing! Check your .env file.")
        
        genai.configure(api_key=api_key)
        # Using gemini-flash-latest: Stable, multimodal, and publicly available.
        self.model = genai.GenerativeModel('gemini-flash-latest')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception), # Broad for now, can be narrowed
        before_sleep=lambda retry_state: print(f"[Engine] Rate limited. Retrying in {retry_state.next_action.sleep} seconds...")
    )
    def _generate_with_retry(self, contents):
        """Helper to call Gemini API with exponential backoff."""
        return self.model.generate_content(contents)

    def infer(self, image_path, prompt):
        """
        [New] Specialized inference method for expert processors.
        Handles single image analysis with task-specific prompts.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at: {image_path}")

        try:
            # Standardizing image format for better VLM consistency
            img = PIL.Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Use the retry helper
            response = self._generate_with_retry([prompt, img])
            
            if not response or not response.text:
                return ""
            return response.text
            
        except Exception as e:
            print(f"[Engine] Inference Error after retries: {e}")
            raise e

    def dual_stage_analyze(self, image_path):
        """
        Runs the Two-Stage Prompting strategy on a single image.
        """
        processor = DualStageProcessor(self)
        return processor.process(image_path)

    def analyze_paper_set(self, image_paths):
        """
        Analyzes a set of paper images and returns a structured full-report.
        Maintains backward compatibility with the original project logic.
        """
        prompt = r"""
        You are a world-class AI research engineer specializing in paper replication.
        I will provide you with images containing parts of a research paper (architecture, formulas, or descriptions).
        
        Your goal is to replicate the core logic into clean, runnable Python code.
        
        STRICT OUTPUT FORMAT:
        You must organize your response into exactly three sections using these exact Markdown headers:
        
        ## 1. Overview
        Provide a concise summary of the paper's core innovation and mathematical objective. Use LaTeX for formulas (e.g., $ \phi $).
        
        ## 2. Implementation Code
        Provide the complete, well-commented Python implementation. Wrap the code in triple backticks: ```python [code] ```.
        
        ## 3. Key Engineering Insights
        List the most critical implementation details, hyperparameters, or training nuances found in the paper as bullet points.
        
        Begin the analysis now.
        """
        
        contents = [prompt]
        
        # 1. Load and Verify Images
        valid_images = 0
        for path in image_paths:
            if os.path.exists(path):
                try:
                    img = PIL.Image.open(path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    contents.append(img)
                    valid_images += 1
                except Exception as e:
                    print(f"[Engine] Error processing image {path}: {e}")
        
        if valid_images == 0:
            return "## 1. Overview\nError: No valid images found.\n\n## 2. Implementation Code\n# No images were processed.\n\n## 3. Key Engineering Insights\n* Please ensure you are uploading valid image files."

        # 2. Call Gemini API with safety handling and retry logic
        try:
            print(f"[Engine] Sending {valid_images} images to Gemini for full analysis...")
            response = self._generate_with_retry(contents)
            
            if not response.text:
                raise ValueError("Empty response from AI.")
                
            return response.text

        except Exception as e:
            error_details = str(e)
            print(f"[Engine] API Call Failed: {error_details}")
            
            return f"""## 1. Overview
Analysis Failed.

## 2. Implementation Code
# ERROR: {error_details}

## 3. Key Engineering Insights
* Execution failed at the API layer. Technical details: {error_details[:100]}..."""