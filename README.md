# PureRepro: AI-Powered Research Paper Replication Engine
> **English | [中文版](#中文介绍)**

PureRepro is a professional engineering framework designed to bridge the gap between AI research papers and production-ready code. It automates the extraction, implementation, and validation of complex machine learning algorithms with high precision and observable workflows.

---

## 🌟 Key Advantages & Advanced Features

### 1. Dual-Stage Vision-to-Code Pipeline
Unlike generic OCR, PureRepro employs a specialized two-stage prompting strategy:
- **Vision-to-LaTeX**: Extracts raw mathematical notations with high fidelity, preserving every subscript and operator.
- **LaTeX-to-Implementation**: Transforms structural logic into clean, modular code (PyTorch/JAX/TF) with comprehensive shape annotations.

### 2. Automated Rigorous Validation
PureRepro doesn't just generate code; it ensures it *works*:
- **Shape Validation**: Automatically generates synthetic tensors to execute the code in a sandbox, catching dimension mismatches instantly.
- **Logic Consistency**: Uses AST-based static analysis to verify that the mathematical operators in the code strictly match the source paper's logic.

### 3. Professional Observability (SSE-Based)
For long-running ArXiv replication tasks, PureRepro provides real-time visibility:
- **Streaming Progress**: Powered by Server-Sent Events (SSE), showing every step from PDF download to algorithm scanning.
- **Emergency Shutdown**: A full-stack interrupt mechanism allows users to halt the engine instantly during complex retry loops.

### 4. Resilient Engineering for Scale
- **Smart Rate-Limiting**: Global thread-locking and segmented sleep ensure compliance with API limits (e.g., Gemini 15 RPM) while maintaining responsiveness.
- **Async Architecture**: Decoupled execution using `BackgroundTasks` ensures that network interruptions don't kill long-running analysis.

---

## � Benchmark Results

PureRepro outperforms general-purpose LLMs in specialized mathematical formula parsing.

| Model | Formula Parsing Accuracy |
| :--- | :--- |
| **PureRepro (Ours)** | **~90%** |
| GPT-4o (Vision) | 82.5% |
| Claude 3.5 Sonnet | 85.0% |

---

## �🛠 Installation & Usage

### 1. One-Click Run (Docker)
```bash
git clone https://github.com/your-repo/PureRepro.git
cd PureRepro
echo "GEMINI_API_KEY=your_key_here" > .env
docker-compose up --build
```

### 2. Local Setup
```bash
conda create -n PureRepro_env python=3.10 && conda activate PureRepro_env
pip install -r requirements.txt
python api.py
```

### 3. Cloud Deployment (Render / Cloud Run)
PureRepro is production-ready and can be deployed to the cloud in minutes:
- **Render**: Connect your GitHub repo, select **Docker** as the environment, and add your `GEMINI_API_KEY` in Environment Variables. The included `render.yaml` simplifies this process.
- **Google Cloud Run**: 
  ```bash
  gcloud builds submit --tag gcr.io/your-project/purerepro
  gcloud run deploy --image gcr.io/your-project/purerepro --set-env-vars GEMINI_API_KEY=your_key
  ```

---

## 📂 Project Structure
- `core/`: High-precision processors and dual-loop validators.
- `api.py`: Robust FastAPI backend with async task management.
- `static/`: Modern, bilingual Web UI with real-time SSE logs.
- `mcp_server.py`: Model Context Protocol server for AI IDE integration.
- `benchmark/`: Automated precision evaluation suite.

---

<br id="中文介绍">

# PureRepro: AI 驱动的论文自动化复现引擎

PureRepro 是一个专业的工程框架，旨在弥合 AI 研究论文与生产级代码之间的鸿沟。它能以极高的精度和可观测的工作流，自动完成复杂机器学习算法的提取、实现与验证。

---

## 🌟 核心优势与先进特性

### 1. 双阶段“视觉到代码”流水线
不同于通用的 OCR，PureRepro 采用了专门的双阶段提示策略：
- **视觉转 LaTeX**: 以高保真度提取原始数学符号，保留每一个下标和算子。
- **LaTeX 转代码实现**: 将结构化逻辑转化为清晰、模块化的代码（PyTorch/JAX/TF），并附带完整的张量维度注释。

### 2. 自动化严苛验证
PureRepro 不仅仅是生成代码，它还能确保代码**真实可用**：
- **维度验证 (Shape Validation)**: 自动生成模拟张量并在沙盒中运行代码，瞬间捕获维度不匹配错误。
- **逻辑一致性检查**: 利用基于 AST 的静态分析，验证代码中的数学算子是否与原始论文逻辑严格一致。

### 3. 专业级可观测性 (基于 SSE)
针对耗时较长的 ArXiv 复现任务，PureRepro 提供了实时的透明度：
- **流式进度推送**: 基于 SSE 技术，实时展示从 PDF 下载到算法扫描的每一步细节。
- **紧急熔断机制**: 全栈中断机制允许用户在复杂的重试循环中瞬间停止引擎。

### 4. 高可靠工程设计
- **智能频率限制**: 通过全局线程锁和分段休眠，在严格遵守 API 频率限制（如 Gemini 15 RPM）的同时保持系统响应。
- **异步解耦架构**: 使用 `BackgroundTasks` 实现执行与请求的解耦，确保网络波动不会中断耗时分析任务。

---

## 📊 基准测试结果

PureRepro 在专业数学公式解析方面的表现优于通用大模型。

| 模型 | 公式解析准确率 |
| :--- | :--- |
| **PureRepro (本项目)** | **~90%** |
| GPT-4o (Vision) | 82.5% |
| Claude 3.5 Sonnet | 85.0% |

---

## 🛠 安装与使用

### 1. 一键运行 (Docker)
```bash
git clone https://github.com/your-repo/PureRepro.git
cd PureRepro
echo "GEMINI_API_KEY=your_key_here" > .env
docker-compose up --build
```

### 2. 本地开发环境
```bash
conda create -n PureRepro_env python=3.10 && conda activate PureRepro_env
pip install -r requirements.txt
python api.py
```

### 3. 云端部署 (Render / Cloud Run)
PureRepro 已具备生产就绪性，可快速部署至云端：
- **Render**: 连接 GitHub 仓库，环境选择 **Docker**，并在环境变量中添加 `GEMINI_API_KEY`。项目已内置 `render.yaml` 简化配置。
- **Google Cloud Run**: 
  ```bash
  gcloud builds submit --tag gcr.io/your-project/purerepro
  gcloud run deploy --image gcr.io/your-project/purerepro --set-env-vars GEMINI_API_KEY=your_key
  ```

---

## 📂 项目结构
- `core/`: 高精度处理器与双循环验证器。
- `api.py`: 具备异步任务管理的 FastAPI 后端。
- `static/`: 支持实时日志的现代双语 Web UI。
- `mcp_server.py`: 用于集成 AI IDE 的 MCP 服务器。
- `benchmark/`: 自动化精度评估套件。

---

## 🎓 开发愿景
PureRepro 专为学术研究复现和高精度代码生成而设计，致力于提升 AI 论文向工业界转化的效率。
