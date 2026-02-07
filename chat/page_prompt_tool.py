import streamlit as st
from streamlit_ace import st_ace

# 1. 必须首先配置页面
st.set_page_config(page_title="字符串转换", layout="wide")

st.title("字符串换行符转换工具")

# 初始化 Session State
if "str_coded" not in st.session_state:
    st.session_state["str_coded"] = "aa\\nbb"
if "str_nature" not in st.session_state:
    st.session_state["str_nature"] = "aa\nbb"
# 用于强制刷新组件的计数器
if "version" not in st.session_state:
    st.session_state["version"] = 0

col1, col2 = st.columns(2)

with col1:
    st.subheader("编码字符串 (含\\n)")
    # 使用包含 version 的 key 确保强制刷新
    content1 = st_ace(
        key=f"ace_coded_{st.session_state.version}",
        value=st.session_state["str_coded"],
        language="markdown",
        theme="monokai",
        height=700,
        auto_update=True,
    )
    if st.button("转为自然换行 ➡️"):
        st.session_state["str_nature"] = content1.replace("\\n", "\n")
        st.session_state["str_coded"] = content1
        st.session_state.version += 1 # 改变 key，强制刷新所有编辑器
        st.rerun()

with col2:
    st.subheader("自然换行字符串")
    content2 = st_ace(
        key=f"ace_nature_{st.session_state.version}",
        value=st.session_state["str_nature"],
        language="markdown",
        theme="monokai",
        height=700,
        auto_update=True,
    )
    if st.button("⬅️ 转为编码字符串"):
        st.session_state["str_coded"] = content2.replace("\n", "\\n")
        st.session_state["str_nature"] = content2
        st.session_state.version += 1 # 改变 key，强制刷新所有编辑器
        st.rerun()
