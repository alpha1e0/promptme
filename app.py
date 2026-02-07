import streamlit as st

MAIN_CONTENT = """
**AI工具集**：
- 角色对话平台：与不同角色进行对话交流。
- 图片生成、修改"""

def main():
    st.title("prompt me")
    st.markdown(MAIN_CONTENT)

main_page = st.Page(main, title="Main", icon=":material/home:", default=True)

chat_page = st.Page("chat/page_chat.py", title="角色扮演", icon=":material/chat:")
chat_scenario_editor_page = st.Page("chat/page_scenario_editor.py", title="场景编辑器", icon=":material/edit:")

img_page = st.Page("img/page_img_gen.py", title="文生图", icon=":material/image:")
img_page_qwen = st.Page("img/page_img_gen_qwen.py", title="文生图(Qwen)", icon=":material/image:")

pg = st.navigation(
    {
        "主页": [main_page],
        "角色扮演": [chat_page, chat_scenario_editor_page],
        "生图": [img_page, img_page_qwen]
    },
    position="top"
)

pg.run()