import os
import json

from common.config import global_config


class Scenario:
    """
    场景类
        加载和解析场景文件
    """
    def __init__(self, scene_path):
        self.scene_path = scene_path
        self.assistant_name = ""
        self.user_name = ""
        self.system_prompt = ""
        self.break_prompt = ""
        self.start_messages = []
        self._content = self.load_scenario()

    def load_scenario(self):
        """加载场景文件"""
        with open(self.scene_path, 'r', encoding='utf-8') as f:
            # print("=================== load scene", self.scene_path)
            scenario = json.load(f)
            self.assistant_name = scenario.get("assistant_name", "AI")
            self.user_name = scenario.get("user_name", "用户")
            self.break_prompt = scenario.get("break_prompt", "")
            self.system_prompt = scenario.get("system_prompt", "")
            self.start_messages = scenario.get("start", [])
            return scenario

    def update(self, scene_data):
        """更新场景文件"""
        with open(self.scene_path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, ensure_ascii=False, indent=2)

    def update_system_prompt(self, system_prompt):
        """更新系统提示词"""
        self.system_prompt = system_prompt
        self._content["system_prompt"] = system_prompt
        self.update(self._content)

    def to_json(self):
        return self._content


class ScenarioMgr:
    def __init__(self):
        self._scenario_dir = os.path.join(global_config.get_chat_workspace(), "scenario")
        self._all_scenario_files = {}

        self._load_all_scenarios()

    def list_scenario(self):
        """列出所有场景名称"""
        return list(self._all_scenario_files.keys())

    def create_scenario(self, scene_name, scene_data):
        """添加新场景"""
        scene_dir = os.path.join(self._scenario_dir, scene_name)
        if os.path.exists(scene_dir):
            raise FileExistsError(f"场景 {scene_name} 已存在")
        
        os.makedirs(scene_dir, exist_ok=True)
        scene_json_path = os.path.join(scene_dir, 'scene.json')
        with open(scene_json_path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, ensure_ascii=False, indent=2)
        # 创建history目录
        history_dir = os.path.join(scene_dir, 'history')
        os.makedirs(history_dir, exist_ok=True)
        self._load_all_scenarios()
        return scene_name

    def remove_scenario(self, scene_name):
        """删除场景"""
        import shutil
        if scene_name in self._all_scenario_files:
            shutil.rmtree(self._all_scenario_files[scene_name])
            self._load_all_scenarios()
            return True
        return False

    def get_scenario(self, scene_name):
        """获取场景配置"""
        if scene_name in self._all_scenario_files:
            scene_json_path = os.path.join(self._all_scenario_files[scene_name], 'scene.json')
            return Scenario(scene_json_path)
        
        raise FileNotFoundError(f"场景 {scene_name} 未找到")

    def get_scenario_path(self, scene_name):
        """获取场景文件路径"""
        return self._all_scenario_files.get(scene_name)

    def scenario_exists(self, scene_name):
        """检查场景是否存在"""
        return scene_name in self._all_scenario_files
    
    def _load_all_scenarios(self):
        """加载所有场景目录"""
        for dirname in os.listdir(self._scenario_dir):
            dir_path = os.path.join(self._scenario_dir, dirname)
            if os.path.isdir(dir_path):
                scene_json_path = os.path.join(dir_path, 'scene.json')
                if os.path.exists(scene_json_path):
                    self._all_scenario_files[dirname] = dir_path

