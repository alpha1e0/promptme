from io import BytesIO

import streamlit as st

from common.config import global_config, LLMConfig
from img.generator import ImgGenerator, get_img_generator


class PageState:
    def __init__(self):
        if not st.session_state.get("llm_config", None):
            st.session_state.llm_config = global_config.get_llm_config(type="img")
        
        if "generator" not in st.session_state:
            st.session_state.generator = get_img_generator(st.session_state.llm_config)

    @property
    def llm_config(self) -> LLMConfig:
        return st.session_state.llm_config
    
    @property
    def generator(self) -> ImgGenerator:
        return st.session_state.generator
    
    def select_llm(self, llm_name) -> None:
        llm_config = global_config.get_llm_config(type="img", name=llm_name)
        st.session_state.llm_config = llm_config
        st.session_state.generator = get_img_generator(llm_config)


def page(state: PageState):
    st.set_page_config(page_title="AI生图", layout="centered")
    st.title("AI生图")

    with st.sidebar:
        st.subheader("📁 模型")
        llm_names = global_config.list_llm_config(type="img")
        llm_names = [name for name in llm_names if "qwen" not in name]
        selected_llm = st.selectbox("选择模型配置", llm_names, key="llm_selector", index=0)
        if selected_llm:
            state.select_llm(selected_llm)

        st.subheader("设置")
        count = st.slider("生成数量", 1, 4, 1)
        size = st.selectbox("图片大小", options=["256x256", "512x512", "768x768", "1024x1024"], index=1)
        ratio = st.selectbox("图片比例", options=["", "1:1", "9:16", "3:4", "16:9", "4:3"], index=2)
        quality = st.selectbox("图片质量", options=["", "standard", "hd"], index=1)

    st.markdown("**输入提示词或描述（Prompt）**")
    prompt = st.text_area("Prompt", height=120, placeholder="例如：背景改为大海边，风格为卡通风格")

    input_images = st.file_uploader("上传参考图（可选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if st.button("生成图片"):
        example_images = []  # 处理后的参考图列表
        if input_images:
            for input_img in input_images:
                # 预处理图片：图片格式统一转换为jpeg，并记录
                new_img_bytes = state.generator.prepare_img(input_img.read(), input_img.name)
                example_images.append(new_img_bytes)

        # 在这里展示参考图 example_images，一行最多显示4张
        if example_images:
            cols = st.columns(4)
            for i, img_bytes in enumerate(example_images):
                with cols[i % 4]:
                    st.image(BytesIO(img_bytes), caption=f"参考图 {i+1}")

        img_results = []
        ok, img_results = state.generator.generate_img(
                                   prompt, 
                                   example_images,
                                   count=count, 
                                   size=size, 
                                   ratio=ratio, 
                                   quality=quality)
        
        if not ok:
            st.error(f"图片生成失败: {img_results}")
            return

        # 显示生成结果 img_results
        if img_results:
            for idx, img_url in enumerate(img_results):
                st.image(img_url, caption=f"生成图片 {idx+1}", width='stretch')


state = PageState()
page(state)
