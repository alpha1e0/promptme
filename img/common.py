import os
import time
import base64
import json

from io import BytesIO

import requests
from PIL import Image
from pillow_heif import register_heif_opener

from common.config import global_config


# 注册 HEIF 解码器
register_heif_opener()


def get_image_type_from_bytes(img_bytes: bytes) -> str:
    if img_bytes.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif img_bytes.startswith(b'GIF87a') or img_bytes.startswith(b'GIF89a'):
        return 'gif'
    else:
        return 'unknown'
    

def convert_image(img_bytes: bytes) -> bytes:
    """
    将非jpeg和png格式的图片转换为jpeg格式
    
    :param img_bytes: 原始图片的二进制数据
    :type img_bytes: bytes
    :return: 转换后的jpeg格式图片的二进制数据
    :rtype: bytes
    """
    img_type = get_image_type_from_bytes(img_bytes)
    if img_type in ['jpeg', 'png']:
        return img_bytes  # 已经是支持的格式，直接返回

    with BytesIO(img_bytes) as input_buffer:
        with Image.open(input_buffer) as img:
            with BytesIO() as output_buffer:
                img.convert("RGB").save(output_buffer, format="JPEG")
                return output_buffer.getvalue()
            

def encode_image(img_bytes) -> str:
    # 读取二进制数据并转为 base64 字符串
    return base64.b64encode(img_bytes).decode('utf-8')


def image_bytes_to_base64(img_bytes: bytes) -> str:
    return f"data:image/jpeg;base64,{encode_image(img_bytes)}"


class Recorder:
    def __init__(self):
        self._name = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self._record_path = os.path.join(global_config.get_img_workspace(), "history", self._name)

    def record_prompt(self, prompt: str):
        os.makedirs(self._record_path, exist_ok=True)
        with open(os.path.join(self._record_path, "prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)

    def record_params(self, params: dict):
        os.makedirs(self._record_path, exist_ok=True)
        with open(os.path.join(self._record_path, "params.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(params, indent=2, ensure_ascii=False))

    def record_image(self, image_bytes: bytes, file_name: str):
        os.makedirs(self._record_path, exist_ok=True)
        with open(os.path.join(self._record_path, file_name), "wb") as f:
            f.write(image_bytes)

    def record_image_base64(self, image_b64: str, index: int):
        os.makedirs(self._record_path, exist_ok=True)

        def _decode_base64_image(b64: str) -> bytes:
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[1]
            return base64.b64decode(b64)
        
        with open(os.path.join(self._record_path, f"output_{index}.jpg"), "wb") as f:
            f.write(_decode_base64_image(image_b64))

    def record_image_from_url(self, image_url: str, index: int):
        os.makedirs(self._record_path, exist_ok=True)

        # 通过 image_url 下载图片内容并保存
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(os.path.join(self._record_path, f"output_{index}.jpg"), "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed to download image from {image_url}, status code: {response.status_code}")

    def record_response(self, resp: dict):
        os.makedirs(self._record_path, exist_ok=True)
        with open(os.path.join(self._record_path, "response.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(resp, indent=2, ensure_ascii=False))


