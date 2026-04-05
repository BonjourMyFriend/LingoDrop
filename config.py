"""
LingoDrop Configuration Module
管理配置文件的加载和保存。
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL_LIST = ["gpt-4o-mini", "gpt-4o"]
SUPPORTED_LANGUAGES = ["Chinese", "English", "Korean", "Japanese", "Spanish", "French", "German"]
LINGODROP_VERSION = "1.0"


def get_config_path() -> Path:
    """配置文件的绝对路径: ~/.lingodrop/config.json"""
    return Path.home() / ".lingodrop" / "config.json"


def get_openai_client(config) -> Optional["OpenAI"]:
    """从配置创建 OpenAI 客户端"""
    from openai import OpenAI
    api_key = (config.api_key or "").strip()
    base_url = (config.base_url or "").strip()
    if not api_key or not base_url:
        logger.warning("API key or Base URL is empty.")
        return None
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        logger.exception("Failed to create OpenAI client: %s", e)
        return None


class ConfigManager:
    """
    JSON-based configuration for non-technical users.
    存储: api_key, base_url, hotkey, native_language, target_language,
    selected_model, model_list, domain_context, ui_language,
    rewrite_hotkey, rewrite_system_prompt.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.api_key: str = ""
        self.base_url: str = ""
        self.hotkey: str = "ctrl+space"
        self.native_language: str = "Chinese"
        self.target_language: str = "Korean"
        self.selected_model: str = "gpt-4o-mini"
        self.model_list: list[str] = list(DEFAULT_MODEL_LIST)
        self.domain_context: str = ""
        self.ui_language: str = "中文"
        self.rewrite_hotkey: str = "shift+ctrl+alt"  # 改写功能快捷键
        self.rewrite_system_prompt: str = ""  # 自定义改写提示词
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load config.json: %s", e)
            return
        self.api_key = str(data.get("api_key", self.api_key) or "")
        self.base_url = str(data.get("base_url", self.base_url) or self.base_url)
        self.hotkey = str(data.get("hotkey", self.hotkey) or self.hotkey)
        self.native_language = str(
            data.get("native_language", self.native_language) or self.native_language
        )
        self.target_language = str(
            data.get("target_language", self.target_language) or self.target_language
        )
        if self.native_language not in SUPPORTED_LANGUAGES:
            self.native_language = "Chinese"
        if self.target_language not in SUPPORTED_LANGUAGES:
            self.target_language = "Korean"

        raw_list = data.get("model_list")
        if isinstance(raw_list, list) and len(raw_list) > 0:
            self.model_list = [str(m).strip() for m in raw_list if str(m).strip()]
        if not self.model_list:
            self.model_list = list(DEFAULT_MODEL_LIST)

        self.selected_model = str(data.get("selected_model", self.selected_model) or "").strip()
        if self.selected_model not in self.model_list:
            self.selected_model = self.model_list[0]

        self.domain_context = str(data.get("domain_context", self.domain_context) or "")
        self.ui_language = str(data.get("ui_language", self.ui_language) or "").strip()
        if self.ui_language not in ["中文", "English"]:
            self.ui_language = "中文"

        self.rewrite_hotkey = str(data.get("rewrite_hotkey", self.rewrite_hotkey) or "shift+ctrl+alt")
        self.rewrite_system_prompt = str(data.get("rewrite_system_prompt", self.rewrite_system_prompt) or "")

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "hotkey": self.hotkey,
            "native_language": self.native_language,
            "target_language": self.target_language,
            "selected_model": self.selected_model,
            "model_list": self.model_list,
            "domain_context": self.domain_context,
            "ui_language": self.ui_language,
            "rewrite_hotkey": self.rewrite_hotkey,
            "rewrite_system_prompt": self.rewrite_system_prompt,
        }
        try:
            self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            logger.error("Failed to save config.json: %s", e)


def get_config_path() -> Path:
    """配置文件的绝对路径: ~/.lingodrop/config.json"""
    return Path.home() / ".lingodrop" / "config.json"
