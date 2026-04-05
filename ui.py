"""
LingoDrop UI Module
包含 FloatingWindow (浮动窗口) 和 SettingsDialog (设置对话框)。
"""

import sys
from typing import Optional, Generator

try:
    import keyboard
    import pyperclip
    from openai import OpenAI
    from PyQt6.QtCore import (
        Qt,
        QRect,
        QThread,
        pyqtSignal,
        QObject,
        QTimer,
        QPropertyAnimation,
        QEasingCurve,
        QAbstractAnimation,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QTextEdit,
        QPlainTextEdit,
        QLabel,
        QSystemTrayIcon,
        QMenu,
        QFrame,
        QWidget,
        QStyle,
        QLineEdit,
        QPushButton,
        QMessageBox,
        QComboBox,
        QGraphicsDropShadowEffect,
        QInputDialog,
        QScrollArea,
        QTabWidget,
    )
    from PyQt6.QtGui import QIcon, QAction, QMouseEvent, QTextCursor, QPixmap, QPainter, QColor, QFont
except ImportError as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.error("Missing dependency: %s. Run: pip install keyboard pyperclip openai PyQt6", e)
    sys.exit(1)

import logging
logger = logging.getLogger(__name__)

from prompts import UI_LANG_OPTIONS
from config import DEFAULT_MODEL_LIST

# =============================================================================
# 资源路径
# =============================================================================

def get_resource_path(relative_path: str):
    """解析资源文件路径 (开发环境 vs PyInstaller)"""
    from pathlib import Path
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


# =============================================================================
# 公共常量和工具
# =============================================================================

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from config import ConfigManager

# 运行时导入（避免循环依赖）
from prompts import UI_TEXTS, get_system_prompt, RENDER_THROTTLE_MS, build_system_prompt, build_rewrite_prompt, REWRITE_PASTE_DELAY_MS

FADE_DURATION_MS = 150
AUTO_HIDE_DELAY_MS = 200
FOCUS_GRACE_MS = 350
NO_SELECTION_HINT_DELAY_MS = 2500


# =============================================================================
# 剪贴板
# =============================================================================

def get_clipboard_text() -> Optional[str]:
    """安全读取剪贴板"""
    try:
        raw = pyperclip.paste()
    except Exception as e:
        logger.warning("Clipboard read failed: %s", e)
        return None
    if raw is None or not isinstance(raw, str):
        return None
    return raw.strip()


def validate_text(text: Optional[str], max_length: int = 800) -> Optional[str]:
    """验证文本：非空、纯文本、长度限制"""
    if text is None or not text:
        return None
    if len(text) > max_length:
        logger.warning("Text too long (%d chars, max %d); skipping.", len(text), max_length)
        return None
    return text


# =============================================================================
# 热键管理
# =============================================================================

class HotkeyBridge(QObject):
    """热键信号桥接器"""
    hotkey_triggered = pyqtSignal()      # 翻译热键
    rewrite_triggered = pyqtSignal()   # 改写热键


def register_hotkey(hotkey: str, bridge: HotkeyBridge) -> None:
    """
    注册翻译热键
    
    Args:
        hotkey: 热键字符串，如 "ctrl+space"
        bridge: 热键信号桥接器
    """
    if not hotkey:
        return

    def _on_trigger() -> None:
        _trigger_copy_and_emit(bridge.hotkey_triggered)

    keyboard.add_hotkey(hotkey, _on_trigger, suppress=False)


def register_rewrite_hotkey(hotkey: str, bridge: HotkeyBridge) -> None:
    """注册改写热键"""
    if not hotkey:
        return

    def _on_trigger() -> None:
        _trigger_copy_and_emit(bridge.rewrite_triggered)

    keyboard.add_hotkey(hotkey, _on_trigger, suppress=False)


def update_hotkey_registration(config, bridge: HotkeyBridge) -> None:
    """更新热键注册"""
    try:
        keyboard.unhook_all_hotkeys()
    except Exception:
        pass
    register_hotkey(config.hotkey, bridge)
    register_rewrite_hotkey(config.rewrite_hotkey, bridge)


def _trigger_copy_and_emit(signal) -> None:
    """执行复制并发射信号的通用逻辑"""
    try:
        for mod in ("ctrl", "alt", "shift"):
            try:
                keyboard.release(mod)
            except Exception:
                pass
        keyboard.press_and_release("ctrl+c")
    except Exception as e:
        logger.warning("Simulated Ctrl+C failed: %s", e)
    signal.emit()


# =============================================================================
# LLM Worker
# =============================================================================

def stream_llm_chunks(client: "OpenAI", user_text: str, config) -> "Generator[str, None, None]":
    """流式调用 LLM，返回文本块"""
    from prompts import get_system_prompt
    system_prompt = get_system_prompt(config, input_text=user_text)
    user_message = (
        "Analyze the following text snippet only (translation, vocabulary, grammar, replacement):\n\n"
        + user_text
    )
    stream = client.chat.completions.create(
        model=config.selected_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


class LLMWorker(QThread):
    """LLM 工作线程"""
    chunk_received = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, text: str, config, parent=None):
        super().__init__(parent)
        self._text = text
        self._config = config

    def run(self) -> None:
        from config import get_openai_client
        client = get_openai_client(self._config)
        if client is None:
            self.error_signal.emit("API key or Base URL is not configured.")
            self.finished_signal.emit()
            return
        try:
            for chunk in stream_llm_chunks(client, self._text, self._config):
                self.chunk_received.emit(chunk)
        except Exception as e:
            err_str = str(e).lower()
            if any(x in err_str for x in ["model", "not found", "invalid", "does not exist", "not supported"]):
                self.error_signal.emit(f"Model Error: {self._config.selected_model} is invalid.")
            else:
                self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


# =============================================================================
# No-Wheel ComboBox
# =============================================================================

class NoWheelComboBox(QComboBox):
    """禁止滚轮切换的 ComboBox"""
    def wheelEvent(self, event) -> None:
        event.ignore()


# =============================================================================
# Floating Window (浮动翻译窗口)
# =============================================================================

class CentralFrame(QFrame):
    """内部框架，转发鼠标事件到顶层窗口"""
    def mousePressEvent(self, event: QMouseEvent) -> None:
        w = self.window()
        if w is not self:
            w.mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        w = self.window()
        if w is not self:
            w.mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        w = self.window()
        if w is not self:
            w.mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)


class FloatingWindow(QWidget):
    """翻译结果浮动窗口"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        _shadow_margin = 24
        self.setMinimumSize(280 + _shadow_margin * 2, 210 + _shadow_margin * 2)
        self.setMaximumSize(350 + _shadow_margin * 2, 380 + _shadow_margin * 2)
        self._worker: Optional[LLMWorker] = None
        self._drag_pos = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)
        self._fade_out_animation: Optional[QPropertyAnimation] = None
        self._has_had_focus_since_show = False
        self._fade_in_anim: Optional[QPropertyAnimation] = None
        self._current_full_response: str = ""

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_throttled_render)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(_shadow_margin, _shadow_margin, _shadow_margin, _shadow_margin)
        root_layout.setSpacing(0)

        central_widget = CentralFrame(self)
        central_widget.setObjectName("centralFrame")
        central_widget.setStyleSheet("""
            QFrame#centralFrame {
                background-color: #191919;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel#brandHeader {
                color: #888888;
                font-size: 12px;
                font-weight: 600;
            }
            QTextEdit {
                background-color: transparent;
                color: #EBEBEA;
                border: none;
                border-radius: 8px;
                padding: 8px 6px;
                font-size: 14px;
                font-family: "Segoe UI", "SF Pro Display", sans-serif;
                line-height: 1.5;
            }
            QTextEdit QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
                border: none;
                border-radius: 4px;
            }
            QTextEdit QScrollBar::handle:vertical {
                background: #505050;
                border-radius: 4px;
                min-height: 36px;
            }
            QTextEdit QScrollBar::handle:vertical:hover {
                background: #707070;
            }
            QPushButton#minimizeButton {
                background-color: transparent;
                color: #a0a0a0;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 16px;
                min-width: 24px;
            }
            QPushButton#minimizeButton:hover {
                background-color: #373737;
                color: #e5e5e5;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        central_widget.setGraphicsEffect(shadow)

        content_layout = QVBoxLayout(central_widget)
        content_layout.setContentsMargins(8, 12, 8, 14)
        content_layout.setSpacing(8)

        top_row = QHBoxLayout()
        self._header_icon = QLabel()
        self._header_icon.setFixedHeight(18)
        _icon_loaded = False
        _icon_path = get_resource_path("tray_icon.png")
        if _icon_path.exists():
            try:
                px = QPixmap(str(_icon_path))
                if not px.isNull():
                    scaled_pixmap = px.scaledToHeight(18, Qt.TransformationMode.SmoothTransformation)
                    self._header_icon.setPixmap(scaled_pixmap)
                    self._header_icon.setMinimumWidth(scaled_pixmap.width())
                    _icon_loaded = True
            except Exception:
                pass
        if not _icon_loaded:
            self._header_icon.setVisible(False)
        top_row.addWidget(self._header_icon)
        self._brand_label = QLabel("LingoDrop")
        self._brand_label.setObjectName("brandHeader")
        top_row.addWidget(self._brand_label)
        top_row.addStretch(1)
        self._minimize_btn = QPushButton("−")
        self._minimize_btn.setObjectName("minimizeButton")
        self._minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._minimize_btn.setToolTip("收起至托盘")
        self._minimize_btn.clicked.connect(self.hide)
        top_row.addWidget(self._minimize_btn)
        content_layout.addLayout(top_row)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.document().setDefaultStyleSheet(
            "body, p, li, span { color: #EBEBEA; font-size: 14px; font-family: 'Segoe UI', sans-serif; }"
        )
        content_layout.addWidget(self._text_edit, 1)
        root_layout.addWidget(central_widget)
        self._place_on_screen()

    def show(self) -> None:
        self._hide_timer.stop()
        if self._fade_out_animation and self._fade_out_animation.state() == QAbstractAnimation.State.Running:
            self._fade_out_animation.stop()
            self._fade_out_animation = None
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            super().show()
        else:
            self.setWindowOpacity(1.0)
        self.raise_()
        self.activateWindow()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._hide_timer.stop()
        self._has_had_focus_since_show = False
        QTimer.singleShot(FOCUS_GRACE_MS, self._mark_ready_for_auto_hide)
        if self._fade_in_anim:
            self._fade_in_anim.stop()
        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setDuration(FADE_DURATION_MS)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in_anim.finished.connect(self._on_fade_in_finished)
        self._fade_in_anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _on_fade_in_finished(self) -> None:
        self._fade_in_anim = None

    def _mark_ready_for_auto_hide(self) -> None:
        if self.isVisible():
            self._has_had_focus_since_show = True

    def reset_auto_hide_grace(self) -> None:
        self._hide_timer.stop()
        self._has_had_focus_since_show = False
        QTimer.singleShot(FOCUS_GRACE_MS, self._mark_ready_for_auto_hide)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        if not self.isVisible():
            return
        if self._worker and self._worker.isRunning():
            return
        if not self._has_had_focus_since_show:
            return
        self._hide_timer.start(AUTO_HIDE_DELAY_MS)

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self._hide_timer.stop()

    def _start_fade_out(self) -> None:
        if self._fade_out_animation and self._fade_out_animation.state() == QAbstractAnimation.State.Running:
            return
        self._fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out_animation.setStartValue(self.windowOpacity())
        self._fade_out_animation.setEndValue(0.0)
        self._fade_out_animation.setDuration(FADE_DURATION_MS)
        self._fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out_animation.finished.connect(self._on_fade_out_finished)
        self._fade_out_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _on_fade_out_finished(self) -> None:
        self._fade_out_animation = None
        self.hide()
        self.setWindowOpacity(1.0)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None

    def _place_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        w = self.width() or self.minimumWidth()
        h = self.height() or self.minimumHeight()
        x = geo.x() + geo.width() - w - 40
        y = geo.y() + (geo.height() - h) // 2 - 40
        x = max(geo.x(), x)
        y = max(geo.y(), y)
        self.move(x, y)

    def show_welcome_guide(self, hotkey_str: str, rewrite_hotkey_str: str = "") -> None:
        self._brand_label.setText("LingoDrop")
        self._current_full_response = ""
        t = UI_TEXTS.get(self._config.ui_language or "中文", UI_TEXTS["中文"])
        welcome_md = t.get("welcome_guide", "")
        welcome_md = welcome_md.replace("[HOTKEY]", hotkey_str)
        welcome_md = welcome_md.replace("[REWRITE_HOTKEY]", rewrite_hotkey_str)
        self._text_edit.setMarkdown(welcome_md)
        self._text_edit.setVisible(True)

    def show_loading(self) -> None:
        self._render_timer.stop()
        self._brand_label.setText("LingoDrop...")
        self._current_full_response = ""
        self._text_edit.clear()
        self._text_edit.setVisible(True)

    def append_chunk(self, chunk: str) -> None:
        self._text_edit.setVisible(True)
        self._current_full_response += chunk
        if not self._render_timer.isActive():
            self._render_timer.start(RENDER_THROTTLE_MS)

    def _do_throttled_render(self) -> None:
        if not self._current_full_response:
            return
        self._text_edit.setMarkdown(self._current_full_response)
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    def show_done(self) -> None:
        self._render_timer.stop()
        if self._current_full_response:
            self._text_edit.setMarkdown(self._current_full_response)
            cursor = self._text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._text_edit.setTextCursor(cursor)
        self._brand_label.setText("LingoDrop")
        self._worker = None

    def show_error(self, message: str) -> None:
        self._render_timer.stop()
        self._brand_label.setText("LingoDrop")
        self._current_full_response = ""
        self._text_edit.setPlainText(f"Error: {message}")

    def show_no_selection_hint(self) -> None:
        self._render_timer.stop()
        self._brand_label.setText("No text detected")
        self._current_full_response = ""
        self._text_edit.setPlainText("Please select or copy some text, then try again.")
        self._text_edit.setVisible(True)
        QTimer.singleShot(NO_SELECTION_HINT_DELAY_MS, self._clear_no_selection_hint)

    def _clear_no_selection_hint(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._brand_label.setText("LingoDrop")
        self._current_full_response = ""
        self._text_edit.clear()

    def start_llm(self, text: str) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.show_loading()
        self._worker = LLMWorker(text, self._config, self)
        self._worker.chunk_received.connect(self.append_chunk)
        self._worker.finished_signal.connect(self.show_done)
        self._worker.error_signal.connect(self.show_error)
        self._worker.start()


# =============================================================================
# Settings Dialog
# =============================================================================

class SettingsDialog(QDialog):
    """设置对话框 - 两页 Tab 布局：翻译页 + 改写页"""
    def __init__(self, config, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._current_ui_lang = (config.ui_language or "中文").strip()
        if self._current_ui_lang not in UI_LANG_OPTIONS:
            self._current_ui_lang = "中文"
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)

        _icon_path = get_resource_path("logo_large.png")
        if _icon_path.exists():
            try:
                icon = QIcon(str(_icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
            except Exception:
                pass

        self.setStyleSheet("""
            QDialog { background-color: #191919; }
            QTabWidget::pane { background-color: #191919; border: none; }
            QTabBar::tab {
                background-color: #252525;
                color: #888888;
                padding: 10px 24px;
                margin-right: 4px;
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #1f1f1f;
                color: #e0e0e0;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #2a2a2a;
                color: #aaaaaa;
            }
            QLabel { color: #EBEBEA; background: transparent; border: none; }
            QLineEdit, QPlainTextEdit {
                background-color: #252525;
                border: 1px solid #555555;
                border-style: solid;
                border-radius: 6px;
                color: #EBEBEA;
                padding: 8px 10px;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #999999;
                background-color: #2a2a2a;
            }
            QPushButton {
                background-color: #333333;
                border: 1px solid #555555;
                border-style: solid;
                border-radius: 6px;
                color: #EBEBEA;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #444444; border-color: #888888; }
            QPushButton:pressed { background-color: #1a1a1a; }
            QComboBox {
                background-color: #252525;
                border: 1px solid #555555;
                border-style: solid;
                border-radius: 6px;
                color: #EBEBEA;
                padding: 6px 12px;
            }
            QComboBox:focus { border: 1px solid #999999; background-color: #2a2a2a; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #555555;
                border-style: solid;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                background-color: #2a2a2a;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #CCCCCC;
                border-style: solid;
                margin-top: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                border: 1px solid #555555;
                border-style: solid;
                color: #EBEBEA;
                outline: none;
                selection-background-color: #404040;
            }
            QPushButton#cancelButton, QPushButton#ghostButton {
                background-color: #333333;
                border: 1px solid #555555;
                border-style: solid;
            }
            QPushButton#cancelButton:hover, QPushButton#ghostButton:hover {
                background-color: #444444;
                border-color: #888888;
            }
            QLabel#versionLabel { color: #888888; font-size: 11px; }
            QFrame#separatorLine { background-color: #333333; max-height: 1px; }
            QScrollArea QScrollBar:vertical, QPlainTextEdit QScrollBar:vertical {
                background: #191919;
                width: 6px;
                margin: 0;
                border: none;
                border-radius: 3px;
            }
            QScrollArea QScrollBar::handle:vertical, QPlainTextEdit QScrollBar::handle:vertical {
                background: #444444;
                border-radius: 3px;
                min-height: 36px;
            }
            QScrollArea QScrollBar::handle:vertical:hover { background: #555555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0;
                background: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab Widget
        self._tab_widget = QTabWidget()
        main_layout.addWidget(self._tab_widget)

        # ========== Page 1: Translation ==========
        self._page_translate = QWidget()
        self._setup_translate_page()

        # ========== Page 2: Rewrite ==========
        self._page_rewrite = QWidget()
        self._setup_rewrite_page()

        self._tab_widget.addTab(self._page_translate, "")
        self._tab_widget.addTab(self._page_rewrite, "")

        # Bottom buttons
        btn_wrapper = QWidget()
        btn_wrapper.setStyleSheet("background-color: #191919;")
        btn_layout = QVBoxLayout(btn_wrapper)
        btn_layout.setContentsMargins(20, 12, 20, 20)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        # Version label in bottom left
        self.version_label = QLabel()
        self.version_label.setObjectName("versionLabel")
        btn_row.addWidget(self.version_label, 1)
        btn_row.addStretch(1)

        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("cancelButton")
        self.save_btn = QPushButton()
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        btn_layout.addLayout(btn_row)
        main_layout.addWidget(btn_wrapper)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._on_save)

        def _on_ui_lang_changed() -> None:
            self._current_ui_lang = self.ui_lang_combo.currentText()
            self._refresh_ui_texts()

        self.ui_lang_combo.currentIndexChanged.connect(_on_ui_lang_changed)
        self._refresh_ui_texts()

    def _setup_translate_page(self) -> None:
        """设置翻译页内容"""
        layout = QVBoxLayout(self._page_translate)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #191919; border: none; }
            QWidget#scrollContent { background-color: #191919; border: none; }
        """)

        content = QWidget()
        content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 16)
        content_layout.setSpacing(12)

        # UI Language
        self.ui_lang_label = QLabel()
        self.ui_lang_combo = NoWheelComboBox()
        self.ui_lang_combo.addItems(UI_LANG_OPTIONS)
        idx = self.ui_lang_combo.findText(self._current_ui_lang)
        if idx >= 0:
            self.ui_lang_combo.setCurrentIndex(idx)
        content_layout.addWidget(self.ui_lang_label)
        content_layout.addWidget(self.ui_lang_combo)

        # API Key
        self.api_label = QLabel()
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_edit.setText(self._config.api_key)
        content_layout.addWidget(self.api_label)
        content_layout.addWidget(self.api_edit)

        # Base URL
        self.url_label = QLabel()
        self.url_edit = QLineEdit()
        self.url_edit.setText(self._config.base_url)
        content_layout.addWidget(self.url_label)
        content_layout.addWidget(self.url_edit)

        # Model
        self.model_label = QLabel()
        self.model_combo = NoWheelComboBox()
        self.model_combo.setEditable(False)
        self.model_combo.addItems(self._config.model_list)
        idx = self.model_combo.findText(self._config.selected_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setCurrentIndex(0)
        model_row = QHBoxLayout()
        model_row.addWidget(self.model_combo, 1)
        self.add_model_btn = QPushButton()
        self.add_model_btn.setObjectName("ghostButton")
        self.add_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_model_btn = QPushButton()
        self.remove_model_btn.setObjectName("ghostButton")
        self.remove_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        model_row.addWidget(self.add_model_btn)
        model_row.addWidget(self.remove_model_btn)
        content_layout.addWidget(self.model_label)
        content_layout.addLayout(model_row)

        def _on_add_model() -> None:
            t = UI_TEXTS[self._current_ui_lang]
            name, ok = QInputDialog.getText(self, t["add_model_title"], t["add_model_prompt"])
            if ok and name:
                name = name.strip()
                if name and self.model_combo.findText(name) < 0:
                    self.model_combo.addItem(name)
                    self.model_combo.setCurrentText(name)

        def _on_remove_model() -> None:
            if self.model_combo.count() <= 1:
                QMessageBox.warning(self, "Model", "Cannot remove the last model.")
                return
            self.model_combo.removeItem(self.model_combo.currentIndex())

        self.add_model_btn.clicked.connect(_on_add_model)
        self.remove_model_btn.clicked.connect(_on_remove_model)

        # Translation Hotkey
        self.hotkey_label = QLabel()
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setText(self._config.hotkey)
        content_layout.addWidget(self.hotkey_label)
        content_layout.addWidget(self.hotkey_edit)

        # Explanation language
        self.native_label = QLabel()
        self.native_combo = NoWheelComboBox()
        from config import SUPPORTED_LANGUAGES
        self.native_combo.addItems(SUPPORTED_LANGUAGES)
        idx = self.native_combo.findText(self._config.native_language)
        if idx >= 0:
            self.native_combo.setCurrentIndex(idx)
        content_layout.addWidget(self.native_label)
        content_layout.addWidget(self.native_combo)

        # Target language
        self.target_label = QLabel()
        self.target_combo = NoWheelComboBox()
        self.target_combo.addItems(SUPPORTED_LANGUAGES)
        idx = self.target_combo.findText(self._config.target_language)
        if idx >= 0:
            self.target_combo.setCurrentIndex(idx)
        content_layout.addWidget(self.target_label)
        content_layout.addWidget(self.target_combo)

        # Separator
        sep = QFrame()
        sep.setObjectName("separatorLine")
        sep.setFixedHeight(1)
        content_layout.addSpacing(8)
        content_layout.addWidget(sep)
        content_layout.addSpacing(8)

        # Domain Context
        self.domain_label = QLabel()
        self.domain_edit = QLineEdit()
        self.domain_edit.setText(self._config.domain_context)
        content_layout.addWidget(self.domain_label)
        content_layout.addWidget(self.domain_edit)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _setup_rewrite_page(self) -> None:
        """设置改写页内容"""
        layout = QVBoxLayout(self._page_rewrite)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #191919; border: none; }
            QWidget#scrollContent { background-color: #191919; border: none; }
        """)

        content = QWidget()
        content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 16)
        content_layout.setSpacing(12)

        # Rewrite Hotkey
        self.rewrite_hotkey_label = QLabel()
        self.rewrite_hotkey_edit = QLineEdit()
        self.rewrite_hotkey_edit.setText(self._config.rewrite_hotkey)
        content_layout.addWidget(self.rewrite_hotkey_label)
        content_layout.addWidget(self.rewrite_hotkey_edit)

        # Separator
        sep = QFrame()
        sep.setObjectName("separatorLine")
        sep.setFixedHeight(1)
        content_layout.addSpacing(8)
        content_layout.addWidget(sep)
        content_layout.addSpacing(8)

        # Rewrite System Prompt
        self.rewrite_prompt_label = QLabel()
        self.rewrite_prompt_edit = QPlainTextEdit()
        self.rewrite_prompt_edit.setMaximumHeight(300)
        # 如果配置中没有自定义提示词，则显示系统默认提示词
        self._initial_rewrite_prompt = self._config.rewrite_system_prompt
        if not self._initial_rewrite_prompt:
            self._initial_rewrite_prompt = build_rewrite_prompt().strip()
        self.rewrite_prompt_edit.setPlainText(self._initial_rewrite_prompt)
        rewrite_prompt_btn_row = QHBoxLayout()
        self.reset_rewrite_prompt_btn = QPushButton()
        self.reset_rewrite_prompt_btn.setObjectName("ghostButton")
        self.reset_rewrite_prompt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rewrite_prompt_btn_row.addWidget(self.reset_rewrite_prompt_btn)
        rewrite_prompt_btn_row.addStretch(1)
        content_layout.addWidget(self.rewrite_prompt_label)
        content_layout.addWidget(self.rewrite_prompt_edit)
        content_layout.addLayout(rewrite_prompt_btn_row)

        def _on_reset_rewrite_prompt() -> None:
            self.rewrite_prompt_edit.setPlainText(build_rewrite_prompt())

        self.reset_rewrite_prompt_btn.clicked.connect(_on_reset_rewrite_prompt)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _refresh_ui_texts(self) -> None:
        t = UI_TEXTS.get(self._current_ui_lang, UI_TEXTS["中文"])
        self.setWindowTitle(t["window_title_settings"])

        # Tab titles
        self._tab_widget.setTabText(0, t.get("tab_translate", "翻译"))
        self._tab_widget.setTabText(1, t.get("tab_rewrite", "改写"))

        # Translate page
        self.ui_lang_label.setText(t["ui_lang_label"])
        self.api_label.setText(t["api_key"])
        self.url_label.setText(t["base_url"])
        self.url_edit.setPlaceholderText(t["placeholder_base_url"])
        self.model_label.setText(t["model"])
        self.add_model_btn.setText(t["add"])
        self.add_model_btn.setToolTip(t["add_model_tooltip"])
        self.remove_model_btn.setText(t["delete"])
        self.remove_model_btn.setToolTip(t["remove_model_tooltip"])
        self.hotkey_label.setText(t["hotkey"])
        self.native_label.setText(t["native_lang"])
        self.target_label.setText(t["target_lang"])
        self.domain_label.setText(t["domain_context"])
        self.domain_edit.setPlaceholderText(t["placeholder_domain"])

        # Rewrite page
        self.rewrite_hotkey_label.setText(t["rewrite_hotkey"])
        self.rewrite_prompt_label.setText(t["rewrite_prompt_label"])
        self.rewrite_prompt_edit.setPlaceholderText(t["rewrite_prompt_placeholder"])
        self.reset_rewrite_prompt_btn.setText(t["reset_rewrite_prompt"])

        # Bottom
        self.cancel_btn.setText(t["cancel"])
        self.save_btn.setText(t["save"])
        self.version_label.setText(t["version_label"])

    def _on_save(self) -> None:
        t = UI_TEXTS.get(self._current_ui_lang, UI_TEXTS["中文"])
        api = self.api_edit.text().strip()
        url = self.url_edit.text().strip() or "https://api.openai.com/v1"
        hotkey = self.hotkey_edit.text().strip() or "ctrl+space"
        rewrite_hotkey = self.rewrite_hotkey_edit.text().strip() or "shift+ctrl+alt"
        native = self.native_combo.currentText().strip() or "Chinese"
        target = self.target_combo.currentText().strip() or "Korean"
        model_list = [self.model_combo.itemText(i).strip() for i in range(self.model_combo.count()) if self.model_combo.itemText(i).strip()]
        if not model_list:
            model_list = list(DEFAULT_MODEL_LIST)
        selected_model = self.model_combo.currentText().strip() or (model_list[0] if model_list else "gpt-4o-mini")
        if selected_model not in model_list:
            model_list.insert(0, selected_model)
        domain_context = self.domain_edit.text().strip()
        rewrite_prompt = self.rewrite_prompt_edit.toPlainText().strip()
        # Only save as custom if user modified from what was initially displayed
        # This prevents accidentally saving the default prompt as custom
        if rewrite_prompt == self._initial_rewrite_prompt:
            # User didn't modify, use default (empty)
            rewrite_prompt = ""

        if not api:
            QMessageBox.warning(self, t["window_title_settings"], t["msg_api_key_required"])
            return

        self._config.ui_language = self.ui_lang_combo.currentText().strip() or "中文"
        if self._config.ui_language not in UI_LANG_OPTIONS:
            self._config.ui_language = "中文"
        self._config.api_key = api
        self._config.base_url = url
        self._config.hotkey = hotkey
        self._config.rewrite_hotkey = rewrite_hotkey
        self._config.native_language = native
        self._config.target_language = target
        self._config.model_list = model_list
        self._config.selected_model = selected_model
        self._config.domain_context = domain_context
        self._config.rewrite_system_prompt = rewrite_prompt
        self._config.save()
        self.accept()


# =============================================================================
# Tray Icon
# =============================================================================

def make_tray_icon() -> QIcon:
    """加载托盘图标，失败时绘制默认图标"""
    for name in ("tray_icon.png", "icon.png"):
        path = get_resource_path(name)
        if path.exists():
            try:
                icon = QIcon(str(path))
                if not icon.isNull():
                    return icon
            except Exception:
                pass
    size = 32
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setBrush(QColor("#404040"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 6, 6)
    painter.setPen(QColor("#e5e5e5"))
    font = QFont("Segoe UI", 14, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "A")
    painter.end()
    return QIcon(px)
