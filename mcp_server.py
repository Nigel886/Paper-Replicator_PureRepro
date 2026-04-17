from fastmcp import FastMCP
import os
import sys
import time
import logging
from dotenv import load_dotenv
from core.engine import PaperReplicator
from core.processors.dual_stage_processor import DualStageProcessor
from core.utils.arxiv_downloader import ArxivDownloader
from core.utils.pdf_processor import PdfProcessor
from utils.progress_manager import progress_tracker

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PureRepro-MCP")

# 初始化 FastMCP
mcp = FastMCP("PureRepro")

# 初始化核心引擎
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables!")

engine = PaperReplicator(api_key=api_key)
processor = DualStageProcessor(engine)
arxiv_downloader = ArxivDownloader()
pdf_processor = PdfProcessor()

@mcp.tool()
def replicate_from_arxiv(arxiv_id: str, framework: str = "PyTorch", task_id: str = None) -> str:
    """
    通过 ArXiv ID 自动下载论文，识别其中的算法框图 (Algorithms)，并将其转化为 Python 类定义。
    
    Args:
        arxiv_id: ArXiv 编号 (例如 '2305.16300')
        framework: 目标框架 (PyTorch, JAX, TensorFlow)
        task_id: 任务 ID (可选，用于进度跟踪)
    """
    try:
        def update_task_progress(msg, step, total):
            if task_id:
                progress_tracker.update_progress(task_id, msg, step, total)

        # 1. 下载 PDF
        update_task_progress(f"Downloading PDF for {arxiv_id}...", 2, 10)
        pdf_path = arxiv_downloader.download(arxiv_id)
        
        # 2. PDF 转图像 (前 10 页)
        update_task_progress("Converting PDF to high-res images...", 3, 10)
        image_paths = pdf_processor.pdf_to_images(pdf_path, max_pages=10)
        
        results = []
        results.append(f"## ArXiv ID: {arxiv_id} 自动复现报告 ({framework})\n")
        
        found_algorithm = False
        total_pages = len(image_paths)
        for idx, img_path in enumerate(image_paths):
            if progress_tracker.is_shutdown():
                logger.warning("Replication cancelled during page scanning.")
                return "任务已被用户取消。"

            current_page = idx + 1
            update_task_progress(f"Scanning page {current_page}/{total_pages} for algorithms...", 4, 10)
            
            # 3. 询问 Gemini 该页是否有核心算法逻辑或数学定义
            check_prompt = (
                "你是一个资深的 AI 研究员。请分析这张论文页面。其中是否包含以下核心内容之一：\n"
                "1. 算法伪代码或步骤列表 (Algorithm/Pseudocode/Step-by-step logic)\n"
                "2. 核心数学公式定义 (Core mathematical definitions/formulas)\n"
                "3. 架构的逻辑组件描述 (Logical components of the architecture)\n"
                "如果包含任何可以转化为代码的逻辑定义，请回答'是'，否则回答'否'。只需回答一个字。"
            )
            
            # 主动休眠以适配 Gemini 免费版 15 RPM 的限制，同时支持快速停止
            for _ in range(10): # 5s / 0.5s
                if progress_tracker.is_shutdown():
                    return "任务已被用户取消。"
                time.sleep(0.5) 
            
            is_algo = engine.infer(img_path, check_prompt)
            
            if "是" in is_algo or "Yes" in is_algo or "算法" in is_algo or "包含" in is_algo:
                found_algorithm = True
                page_num = img_path.split("_p")[-1].split(".")[0]
                results.append(f"### 发现关键内容：第 {int(page_num)+1} 页")
                update_task_progress(f"Algorithm found on page {int(page_num)+1}! Starting replication...", 5, 10)
                
                # 4. 使用 DualStageProcessor 处理该页
                # 针对多智能体框架，调整 prompt 以提取更广泛的逻辑
                processor.action_a_prompt = (
                    "你是一个资深的 AI 论文解析专家。请从这张页面中提取核心的算法逻辑或数学公式。\n"
                    "如果是算法步骤，请将其转化为详细的伪代码或 LaTeX 描述。\n"
                    "如果是数学公式，请保持原始 LaTeX 格式。\n"
                    "直接输出提取内容，不要有任何解释。"
                )
                
                processor.action_b_template = (
                    "将以下论文逻辑/公式转化为高质量的 {framework} 代码实现。\n"
                    "逻辑内容：{{latex}}\n"
                    "要求：\n"
                    "1. 使用类结构 (Class)，并实现核心逻辑方法。\n"
                    "2. 包含完整的 docstrings 和张量维度注释 (Shape annotations)。\n"
                    "3. 在代码末尾提供用于验证的 Shape Dictionary 和 Logic Spec JSON。\n"
                    "4. 如果是多智能体逻辑，请确保组件之间的调用关系清晰。"
                )
                
                # Pass task_id to processor for even more granular progress if needed
                res = processor.process(img_path, framework=framework)
                
                if res.get("validated"):
                    results.append(f"```python\n{res.get('code')}\n```")
                    results.append("✅ **自动验证通过**")
                    update_task_progress(f"Replication successful for page {int(page_num)+1}.", 6, 10)
                else:
                    results.append(f"```python\n{res.get('code')}\n```")
                    results.append(f"⚠️ **验证未完全通过**: {res.get('error', '未知错误')}")
                    update_task_progress(f"Replication finished for page {int(page_num)+1} with warnings.", 6, 10)
                
                results.append("---\n")
        
        if not found_algorithm:
            update_task_progress("No algorithms found in the first 10 pages.", 9, 10)
            return f"在论文 {arxiv_id} 的前 10 页中未检测到明显的算法框图。"
            
        update_task_progress("All pages processed. Generating final report...", 9, 10)
        return "\n".join(results)
        
    except Exception as e:
        if task_id:
            progress_tracker.update_progress(task_id, f"FAILED: {str(e)}", 10, 10)
        return f"自动复现流程失败：{str(e)}"

@mcp.tool()
def analyze_equation(image_path: str) -> str:
    """
    分析论文插图中的数学公式，并将其转换为 LaTeX 和经过维度验证的 PyTorch 代码。
    
    Args:
        image_path: 论文插图的本地绝对路径。
    """
    if not os.path.exists(image_path):
        return f"错误：找不到文件 {image_path}"
    
    logger.info(f"正在分析公式：{image_path}")
    try:
        result = processor.process(image_path)
        
        output = []
        output.append("### 1. LaTeX 公式")
        output.append(f"```latex\n{result.get('latex')}\n```")
        
        output.append("\n### 2. PyTorch 代码实现")
        output.append(f"```python\n{result.get('code')}\n```")
        
        if result.get("validated"):
            output.append("\n✅ **维度验证通过**：该代码已通过 torch.randn 静态检查。")
        else:
            output.append(f"\n❌ **维度验证失败**：\n```\n{result.get('error')}\n```")
            output.append("\n提示：AI 已尝试自动修复但未成功，请检查公式复杂度。")
            
        return "\n".join(output)
    except Exception as e:
        return f"处理过程中发生异常：{str(e)}"

@mcp.tool()
def extract_architecture_graph(image_path: str) -> str:
    """
    提取论文中的模型架构图，并尝试生成其逻辑描述。
    
    Args:
        image_path: 架构图的本地绝对路径。
    """
    # 目前先实现一个基础的视觉描述逻辑
    prompt = "请详细描述这张模型架构图的层级结构、输入输出维度以及关键组件之间的连接关系。"
    try:
        response = engine.infer(image_path, prompt)
        return f"### 模型架构分析\n\n{response}"
    except Exception as e:
        return f"架构分析失败：{str(e)}"

@mcp.tool()
def read_and_fix_error(error_log_path: str, source_code_path: str) -> str:
    """
    读取本地报错日志和源代码，结合论文背景进行自动修复分析。
    
    Args:
        error_log_path: 错误日志文件的路径。
        source_code_path: 对应的源代码文件路径。
    """
    try:
        with open(error_log_path, 'r', encoding='utf-8') as f:
            error_log = f.read()
        with open(source_code_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        prompt = (
            f"我的 PyTorch 代码运行报错了。\n\n"
            f"--- 源代码 ---\n{source_code}\n\n"
            f"--- 错误日志 ---\n{error_log}\n\n"
            f"请根据报错信息修改代码，确保张量维度匹配。"
        )
        
        # 使用引擎进行修复建议
        response = engine._generate_with_retry(prompt)
        return f"### 修复建议\n\n{response.text}"
    except Exception as e:
        return f"修复分析失败：{str(e)}"

if __name__ == "__main__":
    mcp.run()
