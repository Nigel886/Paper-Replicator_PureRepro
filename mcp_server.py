from fastmcp import FastMCP
import os
import sys
import logging
from core.engine import PaperReplicator
from core.processors.dual_stage_processor import DualStageProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PureRepro-MCP")

# 初始化 FastMCP
mcp = FastMCP("PureRepro")

# 初始化核心引擎
# 注意：这里假设 .env 文件在当前目录中，包含 GEMINI_API_KEY
engine = PaperReplicator()
processor = DualStageProcessor(engine)

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
