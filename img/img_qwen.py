import base64
from typing import List

import httpx
import streamlit as st
from openai import OpenAI

from common import load_config

# 使用 streamlit 实现图片生成功能：
# - 用户上传本地图片作为参考图
# - 用户输入文本提示词生成图片
# - 显示并支持下载生成的图片
# - 支持设置 HTTP 代理

# 说明：需要用户在侧边栏填写目标文生图接口 `API URL`（请与后端开发确认接口格式），
# 本示例对常见返回格式进行了兼容处理：
#  - 直接返回图片二进制（Content-Type: image/*）
#  - 返回 JSON，字段为 `image`（base64 或 url）或 `images`（列表）

# conf = load_config("banana")
conf = load_config("qwen")

if conf.get("proxy", ""):
    http_proxy_client = httpx.Client(
        proxy=conf["proxy"],
        verify=False
    )
    client = OpenAI(
        base_url=conf["base_url"],
        api_key=conf["key"],
        http_client=http_proxy_client
    )
else:
    client = OpenAI(
        base_url=conf["base_url"],
        api_key=conf["key"],
    )


def extract_images(resp_content) -> List[bytes]:
    result = []
    images = resp_content["choices"][0]["message"]["images"]

    for item in images:
        if item["type"] == "image_url":
            it = item["image_url"]["url"]
            result.append(it)

    return result


def encode_image(img_bytes):
    # 读取二进制数据并转为 base64 字符串
    return base64.b64encode(img_bytes).decode('utf-8')


# 3. 调用 API 进行图像编辑（以图生图）
def generate_img(prompt, img_files, batch_size=1, size="512x512"):
    # if not img_files:
    result = client.images.edit(
        model=conf["model"],
        image=img_files,
        prompt=prompt,
        n=batch_size,
        size=size,
        extra_body={
            # "step": 20
        }
    )
    print(result)
    img_result = []
    for img_resp in result.data:
        if img_resp.b64_json:
            img_result.append(f"data:image/jpeg;base64,{img_resp.b64_json}")
        else:
            img_result.append(img_resp.url)

    return img_result
    # else:
    #     result = client.images.edit(
    #         model=conf["model"],
    #         image=img_files,
    #         prompt=prompt,
    #         n=1,
    #         size="512x512"
    #     )
    #     print(result)
    #     image_base64 = result.data[0].b64_json
    #     return [f"data:image/jpeg;base64,{image_base64}"]


def main():
    st.set_page_config(page_title="文生图演示", layout="centered")
    st.title("文生图生成 Demo")

    with st.sidebar:
        st.header("设置")
        size = st.selectbox("图片大小", options=["512x512", "768x768", "1024x1024"], index=0)
        batch_size = st.slider("生成数量", 1, 4, 1)

    st.markdown("**输入提示词或描述（Prompt）**")
    prompt = st.text_area("Prompt", height=120)

    input_img_file = st.file_uploader("上传参考图（可选）", type=["png", "jpg", "jpeg"])

    if st.button("生成图片"):
        img_results = generate_img(prompt, 
                                   [input_img_file] if input_img_file else [], 
                                   batch_size=batch_size, 
                                   size=size)
        # 显示生成结果 img_results
        if img_results:
            for idx, img_url in enumerate(img_results):
                st.image(img_url, caption=f"生成图片 {idx+1}", width='stretch')


if __name__ == "__main__":
    main()
