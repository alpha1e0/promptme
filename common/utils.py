import httpx
from openai import OpenAI

from common.config import LLMConfig

def get_openai_client(config: LLMConfig) -> OpenAI:
    """根据配置获取 OpenAI 客户端实例"""
    if config.proxy:
        http_client = httpx.Client(
            proxy=config.proxy,
            verify=False
        )
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            http_client=http_client
        )
    else:
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    return client


def get_raw_client(config: LLMConfig) -> tuple[httpx.Client, dict]:
    """
    当OpenAI Client无法使用的时候，使用原生 httpx 客户端
    
    :param config: LLM配置对象
    :return: 说明
    :rtype: tuple[Client, dict]
    """
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    if config.proxy:
        http_proxy_client = httpx.Client(
            base_url=config.base_url,
            headers=headers,
            proxy=config.proxy,
            verify=False,
            timeout=60
        )
        return http_proxy_client
    else:
        http_client = httpx.Client(
            base_url=config.base_url, 
            headers=headers,
            timeout=60
        )
        return http_client