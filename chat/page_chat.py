import streamlit as st
from streamlit_ace import st_ace

from common.config import global_config, LLMConfig
from chat.scenario import ScenarioMgr, Scenario
from chat.chat_history import ChatHistoryMgr, ChatHistory, ChatHistoryEditor
from chat.aibot import AIBot


class PageState:
    def __init__(self):
        if not st.session_state.get("llm_config", None):
            st.session_state.llm_config = global_config.get_llm_config()
        
        if not st.session_state.get("scenario_mgr", None):
            st.session_state.scenario_mgr = ScenarioMgr()

        if "current_scenario_name" not in st.session_state:
            st.session_state.current_scenario_name = None

        if "current_scenario" not in st.session_state:
            st.session_state.current_scenario = None

        if "current_history_name" not in st.session_state:
            st.session_state.current_history_name = None

        if "current_history" not in st.session_state:
            st.session_state.current_history = None

        if "ai_bot" not in st.session_state:
            st.session_state.ai_bot = None

    @property
    def llm_config(self) -> LLMConfig:
        return st.session_state.llm_config
    
    @property
    def scenario_mgr(self) -> ScenarioMgr:
        return st.session_state.scenario_mgr
    
    @property
    def history_mgr(self) -> ChatHistoryMgr:
        if st.session_state.current_scenario_name is None:
            return None
        return ChatHistoryMgr(st.session_state.current_scenario_name)
    
    @property
    def current_scenario_name(self) -> str:
        return st.session_state.current_scenario_name

    @property
    def current_scenario(self) -> Scenario:
        return st.session_state.current_scenario
    
    @property
    def current_history_name(self) -> str:
        return st.session_state.current_history_name

    @property
    def current_history(self) -> ChatHistory:
        return st.session_state.current_history
    
    @property
    def ai_bot(self) -> AIBot:
        return st.session_state.ai_bot
    
    def select_llm(self, llm_name) -> None:
        llm_config = global_config.get_llm_config(name=llm_name)
        st.session_state.llm_config = llm_config
    
    def select_scenario(self, scenario_name) -> None:
        current_scenario = self.scenario_mgr.get_scenario(scenario_name)
        st.session_state.current_scenario_name = scenario_name
        st.session_state.current_scenario = current_scenario

        ai_boot = AIBot(self.llm_config, self.current_scenario)
        st.session_state.ai_bot = ai_boot

    def select_history(self, history_name) -> None:
        if st.session_state.current_scenario_name is None:
            st.warning("请先选择场景")
            return
        
        current_history = self.history_mgr.get_history(history_name)
        st.session_state.current_history_name = history_name
        st.session_state.current_history = current_history
        
        if st.session_state.ai_bot is None:
            ai_boot = AIBot(self.llm_config, self.current_scenario)
            st.session_state.ai_bot = ai_boot

        self.ai_bot.load_history_messages(current_history.messages)

    def aibot_chat(self, user_input: str, new_system_prompt: str = "") -> str:
        return self.ai_bot.chat(user_input, new_system_prompt)
    
    def aibot_pop_message(self) -> bool:
        if len(self.ai_bot.ctx_messages) > 0:
            self.ai_bot.ctx_messages.pop()
            self.save_history()
            return True
        return False
    
    def save_history(self) -> None:
        if st.session_state.current_history_name is None:
            st.warning("请先选择对话历史")
            return
        
        self.current_history.update(self.ai_bot.get_history())

# 主程序入口
def chat_page(state: PageState):
    st.set_page_config(page_title="RolyPlay", layout="wide")
    
    # 侧边栏 - 场景选择
    with st.sidebar:
        st.subheader("📁 模型")
        llm_names = global_config.list_llm_config()
        selected_llm = st.selectbox("选择模型配置", llm_names, key="llm_selector", index=None)
        if selected_llm:
            state.select_llm(selected_llm)

        st.subheader("📁 场景")
        scenario_names = state.scenario_mgr.list_scenario()
        selected_scenario = st.selectbox("选择场景", scenario_names, key="scene_selector")

        if selected_scenario:
            # 加载场景配置
            state.select_scenario(selected_scenario)
            st.subheader("🗂️ 对话历史")

            # 历史对话选择
            histories = state.history_mgr.list_histories()
            history_options =  histories + ["➕新建对话"]
            selected_history = st.selectbox("选择对话历史", history_options, key="history_selector")

            # 创建新对话按钮
            if selected_history == "➕新建对话":
                new_history_name = st.text_input("新对话名称")
                if st.button("创建对话") and new_history_name:
                    # 这里还没有select history，所以只能通过mgr来创建
                    state.history_mgr.save_history(new_history_name, state.ai_bot.get_history())

                    st.success(f"已创建新对话: {new_history_name}")
                    st.rerun()

    if not selected_scenario:
        st.info("请从左侧选择一个场景开始对话")
        return
    
    if selected_history == "➕新建对话" and not new_history_name:
        st.info("请输入新对话名称并点击创建对话 或者 选择历史对话")
        return
    
    if selected_history == "➕新建对话":
        st.rerun()
        
    # 加载场景和历史
    state.select_history(selected_history)

    st.markdown(f"""
    ### {selected_history}
    > *{state.current_history.user_name}* 和 *{state.current_history.assistant_name}* 的聊天
    """)

    normal_tab, edit_tab, json_history_tab = st.tabs(["对话", "编辑对话", "原始对话"])
    with normal_tab:
        # 对话历史显示
        chat_container = st.container()
        with chat_container:
            for msg in state.ai_bot.ctx_messages:
                if msg["role"] == "system":
                    continue
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        with st.form("chat-form", clear_on_submit=True):
            user_input = st.text_area(f"{state.current_history.user_name} 输入...", height=100, key="user_input")
            with st.expander("追加系统提示词"):
                new_system_prompt = st.text_area(f"系统提示词", height=100, key="new_system_prompt", label_visibility="hidden")
            submitted = st.form_submit_button("发送 ➤")

        if submitted:
            with chat_container:
                if user_input.strip():
                    with st.chat_message("user"):
                        st.write(state.ai_bot.format_input(user_input))

                response_stream = state.aibot_chat(user_input, new_system_prompt)

                with st.chat_message("assistant"):
                    st.write_stream(response_stream)

            # 保存对话历史
            state.save_history()

        button_container = st.container(horizontal=True, horizontal_alignment="right")
        with button_container:
            if st.button("🔙回退"):
                if state.aibot_pop_message():
                    st.rerun()
                else:
                    st.warning("没有可回退的消息")

            if st.button("重新生成"):
                if state.aibot_pop_message():
                    with chat_container:
                        response_stream = state.aibot_chat("", "")

                        with st.chat_message("assistant"):
                            st.write_stream(response_stream)

                        state.save_history()
                        st.rerun()

    with edit_tab:
        st.markdown("**编辑对话**")
        origin_content = ChatHistoryEditor.llm_messages_to_text(state.ai_bot.ctx_messages)
        with st.form("history-editor"):
            content = st_ace(
                value= origin_content,
                language="markdown",
                theme="monokai",
                height="900px",
                font_size=14,
                show_gutter=True,
                show_print_margin=True,
                wrap=True,
                auto_update=True,
            )
            history_edit_submitted = st.form_submit_button("保存", key="history_edit_submitted")

            if history_edit_submitted and content:
                new_messages = ChatHistoryEditor.text_to_llm_messages(content)
                state.ai_bot.update_ctx_messages(new_messages)
                state.save_history()
                st.success("上下文消息已更新")
                st.rerun()

    with json_history_tab:
        st.markdown("**显示当前对话的原始 JSON 内容**")
        st.json(state.current_history.to_json())


state = PageState()
chat_page(state)
