import os
import yaml
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件里的环境变量
load_dotenv()

import os
from dotenv import load_dotenv

load_dotenv()

# --- 调试开始 ---
print("调试: 检查环境变量是否加载成功")
print("DEEPSEEK_API_KEY:", os.getenv("DEEPSEEK_API_KEY"))
# --- 调试结束 ---

class ModelRouter:
    def __init__(self, config_path: str = None):
        # 1. 自动寻找配置文件的位置（防止因为运行路径不同导致找不到文件）
        if config_path is None:
            # 获取当前文件所在目录的上一级（即 backend 目录）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)
            config_path = os.path.join(backend_dir, "config", "models.yaml")
            
        self.config_path = config_path
        
        # 2. 读取 YAML 配置文件
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"读取配置文件失败，请检查路径或 YAML 格式: {e}")
            
        # 3. 缓存已初始化的 OpenAI 客户端，避免每次请求都重新创建
        self._clients = {}

    def _get_client(self, route_name: str):
        """根据路由名获取对应的 OpenAI 客户端和配置"""
        routes = self.config.get("routes", {})
        if route_name not in routes:
            raise ValueError(f"未找到路由配置: {route_name}，请检查 models.yaml")

        route_config = routes[route_name]
        
        # 如果客户端已经创建过，直接返回缓存
        if route_name in self._clients:
            return self._clients[route_name], route_config

        # 从环境变量中读取对应的 API Key
        api_key_env = route_config.get("api_key_env")
        api_key = "sk-816ba0f215374936a62dddaae3a81a52"
        
        if not api_key:
            raise ValueError(f"环境变量中缺少 API Key: {api_key_env}，请检查 .env 文件")

        # 实例化 OpenAI 客户端（因为 DeepSeek 和智谱都兼容 OpenAI 协议）
        client = OpenAI(
            api_key = "sk-816ba0f215374936a62dddaae3a81a52",
            base_url=route_config.get("base_url")
        )
        
        # 存入缓存并返回
        self._clients[route_name] = client
        return client, route_config

    def chat(self, route_name: str, messages: list, **kwargs):
        """
        统一的模型调用入口
        :param route_name: 路由名称（如 interview_agent）
        :param messages: 对话消息列表，如 [{"role": "user", "content": "你好"}]
        :param kwargs: 其他传给模型的高级参数（如 stream=True, response_format={...}）
        """
        client, config = self._get_client(route_name)
        
        # 组装默认参数
        params = {
            "model": config.get("model"),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2048),
        }
        
        # 如果业务代码传了特定参数，则覆盖或追加
        params.update(kwargs)

        # 发起请求
        try:
            response = client.chat.completions.create(**params)
            return response
        except Exception as e:
            print(f"❌ [{route_name}] 模型调用失败: {e}")
            raise

# 实例化一个全局单例，供其他模块直接 import 使用
router = ModelRouter()