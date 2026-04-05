import sys
import os
"""
LingoDrop - Ambient Learning Assistant
PyQt6: system tray, floating window, hotkey-triggered LLM streaming.

Features:
- Translation: Select text + Ctrl+Space -> LLM translation with vocabulary & grammar
- Rewrite: Select English + Ctrl+Shift+R -> Convert to business English, auto-paste
"""

import logging
from pathlib import Path

try:
    import keyboard
    import pyperclip
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QDialog
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logging.error("Missing dependency: %s. Run: pip install keyboard pyperclip PyQt6", e)
    sys.exit(1)

# 模块导入
from config import ConfigManager, get_config_path
from prompts import UI_TEXTS, UI_LANG_OPTIONS, CLIPBOARD_SYNC_DELAY_MS, MAX_TEXT_LENGTH
from ui import (
    FloatingWindow,
    SettingsDialog,
    HotkeyBridge,
    update_hotkey_registration,
    get_clipboard_text,
    validate_text,
    make_tray_icon,
)
from rewriter import RewriteWindow

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# =============================================================================
# 辅助函数
# =============================================================================

def _get_ui_texts(ui_language: str) -> dict:
    """获取当前 UI 语言对应的文本"""
    lang = ui_language.strip() if ui_language else "中文"
    if lang not in UI_LANG_OPTIONS:
        lang = "中文"
    return UI_TEXTS.get(lang, UI_TEXTS["中文"])


def _show_welcome(window: "FloatingWindow", hotkey: str, rewrite_hotkey: str) -> None:
    """显示欢迎指南窗口"""
    window.show_welcome_guide(hotkey, rewrite_hotkey)
    window.show()
    window.raise_()
    window.activateWindow()
    window.reset_auto_hide_grace()


def _check_first_run_setup(config: "ConfigManager", open_settings_fn) -> bool:
    """
    首次启动检查：未配置 API Key 则弹出设置对话框。
    
    Returns:
        True: 设置完成，可以继续启动
        False: 用户取消，需要退出程序
    """
    if (config.api_key or "").strip():
        return True
    
    open_settings_fn()
    
    if not (config.api_key or "").strip():
        logger.warning("API key still empty after Settings; exiting.")
        return False
    return True


# =============================================================================
# Application Entry Point
# =============================================================================

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 加载配置
    config_path = get_config_path()
    config = ConfigManager(config_path)

    logger.info("LingoDrop starting...")

    # ---- UI 窗口 ----
    # 翻译浮动窗口
    window = FloatingWindow(config)

    # 改写浮动窗口
    rewrite_window = RewriteWindow(config)

    # ---- 系统托盘 ----
    tray = QSystemTrayIcon(app)
    tray.setIcon(make_tray_icon())

    menu = QMenu()
    ui_lang = (config.ui_language or "中文").strip()
    if ui_lang not in UI_LANG_OPTIONS:
        ui_lang = "中文"
    texts = UI_TEXTS.get(ui_lang, UI_TEXTS["中文"])

    show_action = QAction(texts["tray_show"])
    show_action.triggered.connect(window.show)
    show_action.triggered.connect(window.raise_)
    show_action.triggered.connect(window.activateWindow)
    menu.addAction(show_action)

    bridge = HotkeyBridge(app)

    def open_settings() -> None:
        from ui import SettingsDialog
        dlg = SettingsDialog(config, window)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            update_hotkey_registration(config, bridge)
            texts = _get_ui_texts(config.ui_language)
            show_action.setText(texts["tray_show"])
            settings_action.setText(texts["tray_settings"])
            exit_action.setText(texts["tray_exit"])

    settings_action = QAction(texts["tray_settings"])
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)

    exit_action = QAction(texts["tray_exit"])
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)

    # 托盘点击响应
    def on_tray_activated(reason) -> None:
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon as _QSTI
            if reason in (_QSTI.ActivationReason.Trigger, _QSTI.ActivationReason.DoubleClick):
                window.show()
                window.raise_()
                window.activateWindow()
        except Exception:
            window.show()
            window.raise_()
            window.activateWindow()

    tray.activated.connect(on_tray_activated)
    tray.show()

    # ---- 首次启动：显示欢迎指南 ----
    _show_welcome(window, config.hotkey, config.rewrite_hotkey)

    # =====================================================================
    # 热键触发逻辑
    # =====================================================================

    def on_translate_hotkey() -> None:
        """翻译热键触发：读取剪贴板 -> 调用 LLM"""
        QTimer.singleShot(CLIPBOARD_SYNC_DELAY_MS, _after_clipboard_sync_translate)

    def _after_clipboard_sync_translate() -> None:
        text = get_clipboard_text()
        truncated = False
        if text and len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
            truncated = True
            logger.info("Text truncated to %d characters.", MAX_TEXT_LENGTH)
        validated = validate_text(text)
        if validated is None:
            window.show()
            window.raise_()
            window.activateWindow()
            window.reset_auto_hide_grace()
            window.show_no_selection_hint()
            return
        if truncated:
            validated = validated + "\n\n(Text truncated for performance)"
        window.show()
        window.raise_()
        window.activateWindow()
        window.reset_auto_hide_grace()
        window.start_llm(validated)

    def on_rewrite_hotkey() -> None:
        """改写热键触发：读取剪贴板 -> 调用 LLM -> 自动粘贴"""
        QTimer.singleShot(CLIPBOARD_SYNC_DELAY_MS, _after_clipboard_sync_rewrite)

    def _after_clipboard_sync_rewrite() -> None:
        text = get_clipboard_text()

        if not text or not text.strip():
            rewrite_window.show()
            rewrite_window.show_no_selection()
            return
        if len(text) > 2000:
            text = text[:2000]
            logger.info("Rewrite text truncated to 2000 characters.")
        rewrite_window.start_rewrite(text)

    # 连接热键信号
    bridge.hotkey_triggered.connect(on_translate_hotkey)
    bridge.rewrite_triggered.connect(on_rewrite_hotkey)

    # 初始热键注册（翻译 + 改写）
    update_hotkey_registration(config, bridge)

    # =====================================================================
    # 首次启动检查：未配置 API Key 则弹出设置
    # =====================================================================
    if not _check_first_run_setup(config, open_settings):
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
