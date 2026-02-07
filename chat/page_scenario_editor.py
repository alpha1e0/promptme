import json

import streamlit as st
from streamlit_ace import st_ace

from common.constant import SCENARIO_TEMPLATE
from chat.scenario import ScenarioMgr, Scenario
from chat.chat_history import ChatHistoryMgr, ChatHistory


class EditorState:
    def __init__(self):        
        if not st.session_state.get("e_scenario_mgr", None):
            st.session_state.p_scenario_mgr = ScenarioMgr()

        if "p_current_scenario_name" not in st.session_state:
            st.session_state.p_current_scenario_name = None

        if "p_current_scenario" not in st.session_state:
            st.session_state.p_current_scenario = None

        if "p_current_history_name" not in st.session_state:
            st.session_state.p_current_history_name = None

        if "p_current_history" not in st.session_state:
            st.session_state.p_current_history = None
    
    @property
    def scenario_mgr(self) -> ScenarioMgr:
        return st.session_state.p_scenario_mgr
    
    @property
    def history_mgr(self) -> ChatHistoryMgr:
        if st.session_state.p_current_scenario_name is None:
            return None
        
        return ChatHistoryMgr(st.session_state.p_current_scenario_name)
    
    @property
    def current_scenario_name(self) -> str:
        return st.session_state.p_current_scenario_name

    @property
    def current_scenario(self) -> Scenario:
        return st.session_state.p_current_scenario
    
    @property
    def current_history_name(self) -> str:
        return st.session_state.p_current_history_name

    @property
    def current_history(self) -> ChatHistory:
        return st.session_state.p_current_history
    
    def select_scenario(self, scenario_name) -> None:
        current_scenario = self.scenario_mgr.get_scenario(scenario_name)
        st.session_state.p_current_scenario_name = scenario_name
        st.session_state.p_current_scenario = current_scenario

    def select_history(self, history_name) -> None:
        if st.session_state.p_current_scenario_name is None:
            st.warning("请先选择场景")
            return
        
        current_history = self.history_mgr.get_history(history_name)
        st.session_state.p_current_history_name = history_name
        st.session_state.p_current_history = current_history


def scenario_editor_page(state: EditorState):
    st.set_page_config(page_title="SecnarioEditor", layout="wide")
    scenario_panel, editor_panel = st.columns([1, 4])

    with scenario_panel:
        st.subheader("场景列表")
        scenarios = state.scenario_mgr.list_scenario()
        selected_scenario = st.pills("场景选择", scenarios, selection_mode="single")

    with editor_panel:
        st.subheader("场景编辑")
        if selected_scenario:
            state.select_scenario(selected_scenario)
            _edit_scenario(state)
        else:
            _create_scenario(state)


def _create_scenario(state: EditorState):
    with st.expander("创建新场景"):
        new_scenario_name = st.text_input("新场景名称")
        new_scenario = st_ace(
            value= json.dumps(SCENARIO_TEMPLATE, ensure_ascii=False, indent=2),
            language="json",
            theme="monokai",
            height="900px",
            font_size=14,
            show_gutter=True,
            show_print_margin=True,
            wrap=True,
            auto_update=True,
        )
        create_scenario_submitted = st.button("创建场景", key="create_scenario_submitted")
        if create_scenario_submitted:
            state.scenario_mgr.create_scenario(new_scenario_name, json.loads(new_scenario))
            st.success("场景创建成功")
            state.select_scenario(new_scenario_name)
            st.rerun()


def _edit_scenario(state: EditorState):
    with st.container():
        detail_on = st.toggle("编辑场景定义")
        if not detail_on:
            new_scenario = st_ace(
                value= json.dumps(state.current_scenario.to_json(), ensure_ascii=False, indent=2),
                language="json",
                theme="monokai",
                height="900px",
                font_size=14,
                show_gutter=True,
                show_print_margin=True,
                wrap=True,
                auto_update=True,
            )
            scenario_edit_submitted = st.button("保存场景", key="scenario_edit_submitted")
            if scenario_edit_submitted:
                state.current_scenario.update(json.loads(new_scenario))
                st.success("场景保存成功")
                state.select_scenario(state.current_scenario_name)
        else:
            original_scenario_detail = state.current_scenario.system_prompt
            new_scenario_detail = st_ace(
                value= original_scenario_detail,
                language="markdown",
                theme="monokai",
                height="900px",
                font_size=14,
                show_gutter=True,
                show_print_margin=True,
                wrap=True,
                auto_update=True,
            )
            scenario_content_edit_submitted = st.button("保存场景", key="scenario_content_edit_submitted_detail")
            if scenario_content_edit_submitted:
                state.current_scenario.update_system_prompt(new_scenario_detail)
                st.success("场景保存成功")
                state.select_scenario(state.current_scenario_name)


state = EditorState()
scenario_editor_page(state)
