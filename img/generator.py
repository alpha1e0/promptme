from typing import List, Tuple

from img.common import convert_image, encode_image, Recorder, image_bytes_to_base64
from common.config import LLMConfig
from common.utils import get_openai_client, get_raw_client


class ImgGenerator:
    """
    图像生成器，使用指定的LLM配置与Banana API进行图像生成和编辑。
    """ 
    def __init__(self, llm_config: LLMConfig):
        self._llm_config = llm_config
        self._client = get_openai_client(self._llm_config)
        self._recorder = Recorder()

    # 3. 调用 API 进行图像编辑（以图生图）
    def generate_img(self, prompt: str, img_files: List[bytes], count=1, size="512x512", 
                    quality="", ratio="") -> Tuple[bool, List[bytes]|str]:
        raise NotImplementedError()
    
    def prepare_img(self, img_bytes: bytes, img_name: str) -> bytes:
        """
        预处理图片：图片格式统一转换为jpeg，并记录
        
        :param img_bytes: 原始图片内容
        :type img_bytes: bytes
        :param img_name: 原始图片名称
        :type img_name: str
        :return: 转换为jpeg格式后的图片内容
        :rtype: bytes
        """
        new_img_bytes = convert_image(img_bytes)
        self._recorder.record_image(new_img_bytes, img_name)
        return new_img_bytes


# 生成图片，qwen模型，文生图和图生图需要使用不同模型
# 参考：
# 文生图：https://docs.siliconflow.cn/cn/userguide/capabilities/images
# 图生图：https://docs.siliconflow.cn/cn/api-reference/images/images-generations 最多支持3张参考图
class GeminiImgGenerator(ImgGenerator):
    """
    图像生成器，使用指定的LLM配置与Banana API进行图像生成和编辑。
    """
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        self._modalities=["text", "image"]

    def generate_img(self, prompt: str, img_files: List[bytes], count=1, size="512x512", 
                    quality="", ratio="") -> Tuple[bool, List[bytes]|str]:
        query = [{
                    "type": "text",
                    "text": f"Generate {count} images based on this description:\n {prompt}"
                }]
        for img_content in img_files:
            img_url = f"data:image/jpeg;base64,{encode_image(img_content)}"
            query.append({
                "type": "image_url",
                "image_url": {
                    "url": img_url
                }
            })

        img_config = {
            size: size,
        }
        if ratio:
            img_config["aspect_ratio"] = ratio
        if quality:
            img_config["quality"] = quality

        params = {
            "model": self._llm_config.model,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "n": count,
            "extra_body": {
                "modalities": self._modalities,
                "image_config": img_config
            }
        }
        self._recorder.record_prompt(prompt)
        self._recorder.record_params(params)

        response = self._client.chat.completions.create(**params)
        
        self._recorder.record_response(response.to_dict())
        return self.extract_images(response)
    
    def extract_images(self, response) -> Tuple[bool, List[bytes]|str]:
        # print("响应完整内容:", response)
        result = []

        for i, choice in enumerate(response.choices):
            message = choice.message

            # In the 2026 SDK structure, images are usually in message.images or specific parts of content
            if hasattr(message, 'images') and message.images:
                for img in message.images:
                    image_url = img['image_url']['url'] # Usually 'data:image/png;base64,...'
                    result.append(image_url)
                    self._recorder.record_image_base64(image_url, i)
            else:
                print(f"Option {i} does not contain image data: {choice.message.content}")

        if not result:
            message = response.choices[0].message
            return False, str(message)

        return True, result
    

class SeeDreamGenerator(GeminiImgGenerator):
    """
    适用于SeeDream模型的图像生成器，参考：https://openrouter.ai/bytedance-seed/seedream-4.5/api
    """
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        self._modalities=["image"]


class Flux2Generator(GeminiImgGenerator):
    """
    适用于Flux2模型的图像生成器，参考：https://openrouter.ai/black-forest-labs/flux.2-max/api
    """
    def __init__(self, llm_config: LLMConfig):
        super().__init__(llm_config)
        self._modalities=["image"]


class QwenImgGenerator(ImgGenerator):
    def __init__(self, llm_config: LLMConfig, llm_config_editor: LLMConfig):
        self._llm_config = llm_config
        self._llm_config_editor = llm_config_editor

        self._client = get_openai_client(self._llm_config)
        self._client_editor = get_raw_client(self._llm_config_editor)

        self._recorder = Recorder()

    def generate_img(self, prompt, img_files, batch_size=1, size="512x512", steps=20):
        self._recorder.record_prompt(prompt)

        # qwen 生成图像只能用qwen-image
        if not img_files:
            result = self._client_editor.post("/images/generations", json={
                "model": self._llm_config.model,
                "prompt": prompt,
                "image_size": size,
                "batch_size": batch_size,
                "num_inference_steps": steps,
                "size": size
            })

            img_result = []
            if result.status_code != 200 or "images" not in result.json():
                print("错误响应:", result.text)
                return False, result.text
            
            self._recorder.record_response(result.json())
            for i, img in enumerate(result.json().get("images", [])):
                img_result.append(img["url"]) # 目前qwen图生图只返回url
                self._recorder.record_image_from_url(img["url"], i)
            return True, img_result
        # qwen 图生图只能用 qwen-image-edit
        else:
            result = self._client_editor.post("/images/generations", json={
                "model": self._llm_config_editor.model,
                "prompt": prompt,
                "image": image_bytes_to_base64(img_files[0]),
                "image_size": size,
                "batch_size": batch_size,
                "num_inference_steps": steps,
                "size": size
            })

            img_result = []
            if result.status_code != 200 or "images" not in result.json():
                print("错误响应:", result.text)
                return False, result.text
            
            self._recorder.record_response(result.json())
            for i, img in enumerate(result.json().get("images", [])):
                img_result.append(img["url"]) # 目前qwen图生图只返回url
                self._recorder.record_image_from_url(img["url"], i)
            return True, img_result
    

def get_img_generator(llm_config: LLMConfig) -> ImgGenerator:
    """
    ImgGenerator的工厂函数
    
    :param llm_config: 模型配置
    :type llm_config: LLMConfig
    :return: ImgGenerator
    :rtype: ImgGenerator
    """
    if "gemini" in llm_config.model.lower():
        return GeminiImgGenerator(llm_config)
    elif "seedream" in llm_config.model.lower():
        return SeeDreamGenerator(llm_config)
    elif "flux" in llm_config.model.lower():
        return Flux2Generator(llm_config)
    elif "qwen" in llm_config.model.lower():
        return QwenImgGenerator(llm_config)
    else:
        raise NotImplementedError(f"不支持的模型类型: {llm_config.model}")