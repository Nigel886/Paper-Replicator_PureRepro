import ast
import json
import re

class LogicValidator:
    """
    检查生成的代码是否符合数学公式的逻辑约束。
    例如：公式里有 Sum，代码里是否有 .sum() 或 torch.sum()？
    """

    def __init__(self):
        # 常见数学算子到 Python/PyTorch/JAX/TF 函数的映射
        self.operator_map = {
            "sum": ["sum", "torch.sum", "jnp.sum", "tf.reduce_sum", "keepdim=True"],
            "max": ["max", "torch.max", "jnp.max", "tf.reduce_max", "argmax"],
            "mean": ["mean", "torch.mean", "jnp.mean", "tf.reduce_mean", "avg_pool"],
            "exp": ["exp", "torch.exp", "jnp.exp", "tf.exp"],
            "log": ["log", "torch.log", "jnp.log", "tf.math.log"],
            "softmax": ["softmax", "F.softmax", "jax.nn.softmax", "tf.nn.softmax"],
            "expectation": ["mean", "sum", "weighted_sum"],
            "matmul": ["matmul", "mm", "@", "bmm", "linear", "jnp.dot", "tf.matmul"]
        }

    def validate_consistency(self, code, logic_spec_json):
        """
        验证代码是否包含逻辑规范中要求的算子。
        Returns (is_consistent, error_message)
        """
        try:
            if not logic_spec_json:
                return True, None

            if isinstance(logic_spec_json, str):
                spec = json.loads(logic_spec_json)
            else:
                spec = logic_spec_json

            required_ops = spec.get("required_operators", [])
            if not required_ops:
                return True, None

            # 将代码解析为 AST
            tree = ast.parse(code)
            
            # 提取代码中所有的函数调用和操作符
            called_functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 处理 func.method() 或 func()
                    if isinstance(node.func, ast.Attribute):
                        called_functions.append(node.func.attr)
                    elif isinstance(node.func, ast.Name):
                        called_functions.append(node.func.id)
                elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
                    called_functions.append("matmul") # 处理 @ 符号

            # 检查缺失的算子
            missing_ops = []
            for op in required_ops:
                op_lower = op.lower()
                possible_matches = self.operator_map.get(op_lower, [op_lower])
                
                # 如果任何一个可能的匹配项出现在调用的函数中，就认为该算子存在
                found = False
                for match in possible_functions_to_check(possible_matches):
                    if any(match in func for func in called_functions):
                        found = True
                        break
                
                if not found:
                    missing_ops.append(op)

            if missing_ops:
                return False, f"代码中似乎缺失了公式要求的逻辑算子: {', '.join(missing_ops)}"

            return True, None

        except Exception as e:
            return False, f"逻辑验证出错: {str(e)}"

    @staticmethod
    def extract_logic_spec(text):
        """从文本中提取 Logic Spec JSON"""
        # 寻找包含 required_operators 的 JSON 块
        matches = re.finditer(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match.group(1))
                if "required_operators" in data:
                    return data
            except:
                continue
        return None

def possible_functions_to_check(matches):
    """提取简单的函数名进行匹配"""
    results = []
    for m in matches:
        if "." in m:
            results.append(m.split(".")[-1])
        else:
            results.append(m)
    return list(set(results))
