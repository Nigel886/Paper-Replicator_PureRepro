# PureRepro: AI-Powered Research Paper Replication Engine

PureRepro is a professional tool designed to automate the replication of machine learning research papers. It transforms algorithm screenshots or ArXiv IDs into production-ready, framework-specific code (PyTorch, JAX, TensorFlow) with high-fidelity formula parsing and logical validation.

## 🚀 Key Features

- **One-Click ArXiv Replication**: Enter an ArXiv ID, and PureRepro will download the PDF, extract algorithm blocks, and generate code automatically.
- **Dual-Stage Validation**:
    - **Shape Validation**: Runtime execution with synthetic tensors to catch dimension mismatches.
    - **Logic Validation**: AST-based static analysis to ensure mathematical operator consistency.
- **Multi-Framework Support**: Generate code for PyTorch, JAX, or TensorFlow.
- **High-Precision Formula Parsing**: Specialized `LatexExpert` engine for extracting complex mathematical notations.
- **MCP Native**: Fully integrated with the Model Context Protocol for use in AI desktops (Claude Desktop, etc.).

## 📊 Benchmark Results

PureRepro outperforms general-purpose LLMs in specialized mathematical formula parsing.

| Model | Formula Parsing Accuracy |
| :--- | :--- |
| **PureRepro (Ours)** | **~90%** |
| GPT-4o (Vision) | 82.5% |
| Claude 3.5 Sonnet | 85.0% |

*Results based on the `benchmark/samples` set of 20 complex ML formulas.*

## 🛠 Installation & Usage

### 1. One-Click Run (Docker)
Ensure you have Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/PureRepro.git
cd PureRepro

# 2. Add your GEMINI_API_KEY to a .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# 3. Build and run
docker-compose up --build
```
The application will be available at `http://localhost:8000`.

### 2. Local Setup
```bash
# 1. Create environment
conda create -n PureRepro_env python=3.10
conda activate PureRepro_env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python api.py
```

## 🧪 Running Benchmarks
Evaluate the engine against our internal dataset:
```bash
python benchmark/eval.py
```
Reports will be saved in `benchmark/logs/`.

## 📂 Project Structure
- `core/`: Core engine, processors, and validators.
- `api.py`: FastAPI backend.
- `static/`: Modern Web UI.
- `mcp_server.py`: Model Context Protocol server.
- `benchmark/`: Precision evaluation set and logic.

## 🎓 About
Developed for academic research replication and high-precision code generation.
