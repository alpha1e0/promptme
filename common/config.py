import json
import os
from pathlib import Path


class LLMConfig:
    """
    加载和解析配置文件，格式：
        {
            "base_url": "http://aaa.com/v1",
            "model": "GLM-4.7",
            "key": "",
            "temperature": 0.9,
            "max_tokens": 16000,
            "proxy": "http://127.0.0.1:8888"
        }
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.base_url = ""
        self.model = ""
        self.api_key = ""
        self.temperature = 0.7
        self.max_tokens = 200
        self.proxy = ""
        self.break_prompt = ""
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            config_content = Path(self.config_path).read_text(encoding='utf-8')
            config = json.loads(config_content)
            self.base_url = config.get("base_url", self.base_url)
            self.model = config.get("model", self.model)
            self.api_key = config.get("key") or os.getenv("OPENAI_API_KEY", "")
            self.temperature = config.get("temperature", self.temperature)
            self.max_tokens = config.get("max_tokens", self.max_tokens)
            self.proxy = config.get("proxy", self.proxy)
            self.break_prompt = config.get("break_prompt", self.break_prompt)

            self._raw_config = config
        except FileNotFoundError:
            print(f"配置文件 {self.config_path} 未找到，使用默认配置")
        except Exception as e:
            print(f"加载配置文件出错: {e}")

    def __str__(self):
        return json.dumps(self._raw_config, indent=2, ensure_ascii=False)


class Config:
    def __init__(self):
        self.workspace = self.get_workspace()

    def get_workspace(self):
        """获取工作目录"""
        workspace_from_env = os.getenv("PROMPT_ME_WORKSPACE")
        if workspace_from_env and Path(workspace_from_env).exists():
            return workspace_from_env

        return Path(Path(__file__).absolute().parent.parent, ".workspace")

    def get_chat_workspace(self):
        """获取chat工作目录"""
        return Path(self.workspace, "chat")

    def get_img_workspace(self):
        """获取img工作目录"""
        return Path(self.workspace, "img")
    
    def list_llm_config(self, type="chat") -> list[str]:
        files = os.listdir(Path(self.workspace, type))
        config_files = [f for f in files if f.endswith('.json')]
        return config_files
    
    def get_llm_config(self, type="chat", name="config.json"):
        """获取LLM配置文件路径"""
        config_files = self.list_llm_config(type)
        if name not in config_files:
            conf_path = Path(self.workspace, type, config_files[0])
            return LLMConfig(conf_path)
        
        conf_path = Path(self.workspace, type, name)
        return LLMConfig(conf_path)


global_config = Config()
