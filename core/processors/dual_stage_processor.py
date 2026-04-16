from .base import BaseProcessor

class DualStageProcessor(BaseProcessor):
    """
    Implements the "Two-Stage Prompting" strategy:
    Action A: Vision-to-LaTeX (The 'Typist' phase)
    Action B: LaTeX-to-Code (The 'Programmer' phase)
    """
    
    def __init__(self, engine):
        super().__init__(engine)
        # Specific prompts as requested by the user
        self.action_a_prompt = (
            "You are a specialized OCR engine for academic papers. Extract the "
            "mathematical formula from this image into raw LaTeX. DO NOT explain the "
            "formula. DO NOT simplify. Ensure all subscripts, superscripts, and Greek "
            "letters are preserved exactly."
        )
        
        self.action_b_template = (
            "Convert the following LaTeX formula into a PyTorch function.\n"
            "Formula: {latex}\n"
            "Context: It belongs to a Reinforcement Learning agent.\n"
            "Requirements: Use clear variable names, include docstrings defining tensor shapes."
        )

    def process(self, image_path, **kwargs):
        """
        Executes the two-stage prompting flow sequentially.
        """
        # --- Action A: Vision-to-LaTeX ---
        print(f"[DualStage] Action A: Extracting LaTeX from {image_path}...")
        raw_latex = self.engine.infer(image_path, self.action_a_prompt)
        latex_output = self.clean_output(raw_latex)
        
        if not latex_output:
            return {"error": "Failed to extract LaTeX in Action A."}

        # --- Action B: LaTeX-to-Code ---
        print(f"[DualStage] Action B: Converting LaTeX to PyTorch code...")
        action_b_prompt = self.action_b_template.format(latex=latex_output)
        
        # Use the engine's retry helper for text-to-text Action B
        try:
            response = self.engine._generate_with_retry(action_b_prompt)
            code_output = response.text
        except Exception as e:
            print(f"[DualStage] Action B Error: {e}")
            code_output = f"# Error during code generation: {str(e)}"

        return {
            "latex": latex_output,
            "code": self.clean_output(code_output)
        }

    def clean_output(self, text):
        """Cleans model output by removing markdown artifacts."""
        if not text:
            return ""
        # Remove common markdown wrappers (```latex, ```python, ```)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Find the first newline after the opening backticks
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline:].strip()
            # Remove trailing backticks
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        return cleaned
