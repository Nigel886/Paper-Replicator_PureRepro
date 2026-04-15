import re

def extract_and_save_code(text, filename="replicated_model.py"):
    """Extracts PyTorch code from Markdown and saves it to a file."""
    code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if code_match:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_match.group(1))
        print(f"✅ Success: Code saved to {filename}")
        return True
    else:
        print("⚠️ Note: No Python code block found in response.")
        return False