import os
import json

from common.config import global_config


class ChatHistory:
    """聊天历史记录类"""
    def __init__(self, history_path: str):
        self.history_path = history_path

        self.assistant_name = ""
        self.user_name = ""
        self.system_prompt = ""

        self.messages = []

        self._content = self.load_history()

    def load_history(self):
        """加载聊天历史记录"""
        with open(self.history_path, 'r', encoding='utf-8') as f:
            # print("=================== load history", self.history_path)
            history_data = json.load(f)
        
            self.assistant_name = history_data["assistant_name"]
            self.user_name = history_data["user_name"]
            self.system_prompt = history_data.get("system_prompt", "")

            self.messages = history_data["messages"]

            return history_data

    def update(self, history_data: dict):
        """更新聊天历史记录"""
        with open(self.history_path, 'w', encoding='utf-8') as f:
            # print("=================== update history", self.history_path)
            json.dump(history_data, f, ensure_ascii=False, indent=2)

    def to_json(self):
        return self._content


class ChatHistoryMgr:
    def __init__(self, scenario_name: str, ):
        scenario_dir = os.path.join(global_config.get_chat_workspace(), "scenario")
        self._history_dir = os.path.join(scenario_dir, scenario_name, "history")

        self._all_history_files = {}
        self._load_all_history_files()

    def _load_all_history_files(self):
        """加载指定场景的聊天历史文件"""
        if os.path.exists(self._history_dir):
            for filename in os.listdir(self._history_dir):
                if filename.endswith('.json'):
                    self._all_history_files[filename] = os.path.join(self._history_dir, filename)
                    
        return list(self._all_history_files.keys())

    def list_histories(self) -> list[str]:
        """列出指定场景的聊天历史名称"""
        return list(self._all_history_files.keys())

    def save_history(self, history_file: str, history: str) -> str:
        """添加新聊天历史到指定场景"""
        # print("=================== save history from mgr", history_file)
        if not history_file.endswith('.json'):
            history_file += '.json'

        history_path = os.path.join(self._history_dir, history_file)

        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        return history_file

    def remove_history(self, history_name: str) -> bool:
        """删除指定场景的聊天历史"""
        if history_name in self._all_history_files:
            os.remove(self._all_history_files[history_name])

            return True
        return False

    def get_history(self, history_name: str) -> ChatHistory:
        """获取指定场景的聊天历史数据"""
        if history_name in self._all_history_files:
            return ChatHistory(self._all_history_files[history_name])

        raise FileNotFoundError(f"聊天历史文件 {history_name} 不存在")

    def get_history_path(self, history_name: str) -> str:
        """获取指定场景的聊天历史文件路径"""
        return self._all_history_files.get(history_name)

    def history_exists(self, history_name: str) -> bool:
        """检查指定场景的聊天历史是否存在"""
        return history_name in self._all_history_files


class ChatHistoryEditor:
    @staticmethod
    def llm_messages_to_text(messages: list) -> str:
        """将LLM消息列表转换为文本格式"""
        text_parts = []
        for msg in messages:
            title = f'{msg.get("role", "")}|{msg.get("name", "")}'
            content = msg.get("content", "")
            text_parts.append(f"{title}\n{content}")
        return "\n---\n".join(text_parts)
    
    @staticmethod
    def text_to_llm_messages(text: str) -> list:
        """将文本格式转换为LLM消息列表"""
        messages = []
        parts = text.strip().split('\n---\n')
        for part in parts:
            if not part:
                continue
            
            lines = part.split('\n', 1)
            if len(lines) != 2:
                raise ValueError("消息格式错误，缺少内容部分")
            
            tilte = lines[0]
            content = lines[1]
            title_sp = tilte.split('|', 1)
            if len(title_sp) != 2:
                raise ValueError("消息格式错误，标题部分缺少角色或名称")
            
            role = title_sp[0]
            name = title_sp[1]
            messages.append({
                "role": role,
                "content": content,
                "name": name
            })

        return messages