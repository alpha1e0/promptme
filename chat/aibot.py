import httpx
from openai import OpenAI
from dotenv import load_dotenv

from common.config import LLMConfig
from common.utils import get_openai_client
from chat.scenario import Scenario


# 加载环境变量
load_dotenv()


class AIBot:
    """AI聊天机器人类"""
    def __init__(self, config: LLMConfig, scene: Scenario):
        self._config = config
        self._scenario = scene
        self.ctx_messages = []
        self._client = get_openai_client(self._config)
        # 初始化对话历史
        self._init_messages()

    def _init_messages(self):
        """初始化对话历史"""
        # 添加破甲提示词
        if self._config.break_prompt:
            self.ctx_messages.append({
                "role": "system",
                "content": self._config.break_prompt
            })
        # 添加系统提示词
        if self._scenario.system_prompt:
            self.ctx_messages.append({
                "role": "system",
                "content": self._scenario.system_prompt
            })
        # 添加初始消息
        self.ctx_messages.extend(self._scenario.start_messages)

    def reset(self):
        """重置会话，清空对话历史"""
        self.ctx_messages = []
        self._init_messages()

    def update_ctx_messages(self, messages: list):
        """加载上下文消息"""
        self.ctx_messages = messages

    def get_history(self):
        """获取当前会话历史"""
        return {
            "assistant_name": self._scenario.assistant_name,
            "user_name": self._scenario.user_name,
            "config": {
                "base_url": self._config.base_url,
                "model": self._config.model,
                "temperature": self._config.temperature,
                "max_tokens": self._config.max_tokens
            },
            "messages": self.ctx_messages
        }

    def load_history_messages(self, messages: list):
        """加载历史消息"""
        self.ctx_messages = messages

    def format_input(self, user_input: str):
        """格式化用户输入"""
        return f"{self._scenario.user_name}: {user_input}"

    def chat(self, user_input: str, new_system_prompt: str = ""):
        """处理用户输入，返回AI角色的回复（流式输出）"""
        # 普通消息，添加到对话历史
        if user_input.strip():
            self.ctx_messages.append({
                "role": "user",
                "content": f"{self._scenario.user_name}: {user_input}",
                "name": self._scenario.user_name
            })

        if new_system_prompt.strip():
            self.ctx_messages.append({
                "role": "system",
                "content": new_system_prompt,
                "name": "system"
            })

        try:
            # 调用OpenAI API获取流式回复
            stream = self._client.chat.completions.create(
                model=self._config.model,
                messages=self.ctx_messages,
                stream=True  # 启用流式响应
            )
            full_response = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content or ''
                if content:
                    full_response += content
                    yield content  # 逐块返回内容
            # 流式结束后保存完整响应到历史
            full_response = full_response.strip()
            if not full_response.startswith(self._scenario.assistant_name):
                full_response = f"{self._scenario.assistant_name}: {full_response}"
                
            self.ctx_messages.append({
                "role": "assistant",
                "content": full_response,
                "name": self._scenario.assistant_name
            })
        except Exception as e:
            yield f"发生错误: {str(e)}"



