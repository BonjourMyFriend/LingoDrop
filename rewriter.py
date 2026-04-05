"""
LingoDrop Rewriter Module
改写功能：选中英文 → 转换为商务英语 → 自动粘贴替换。
"""

import logging
import re
from typing import Optional

try:
    import keyboard
    import pyperclip
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QAbstractAnimation
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect, QTextEdit
    from PyQt6.QtGui import QColor
    from PyQt6.QtCore import Qt
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logging.error("Missing dependency: %s", e)
    import sys
    sys.exit(1)

from config import get_openai_client
from prompts import get_rewrite_prompt, RENDER_THROTTLE_MS, REWRITE_PASTE_DELAY_MS
from ui import CentralFrame

logger = logging.getLogger(__name__)

FADE_DURATION_MS = 150

# 预编译 Markdown 清理正则表达式（性能优化）
_RE_BOLD = re.compile(r'\*\*(.+?)\*\*')
_RE_BOLD_UNDERSCORE = re.compile(r'__(.+?)__')
_RE_ITALIC = re.compile(r'\*(.+?)\*')
_RE_ITALIC_UNDERSCORE = re.compile(r'_(.+?)_')
_RE_INLINE_CODE = re.compile(r'`(.+?)`')
_RE_STRIKETHROUGH = re.compile(r'~~(.+?)~~')
_RE_HEADING = re.compile(r'^#{1,6}\s+', re.MULTILINE)
_RE_UNORDERED_LIST = re.compile(r'^[\*\-\+]\s+', re.MULTILINE)
_RE_ORDERED_LIST = re.compile(r'^\d+\.\s+', re.MULTILINE)
_RE_LINK = re.compile(r'\[(.+?)\]\(.+?\)')
_RE_IMAGE = re.compile(r'!\[.*?\]\(.+?\)')
_RE_HORIZONTAL_RULE = re.compile(r'^[\-\*]{3,}$', re.MULTILINE)
_RE_BLOCKQUOTE = re.compile(r'^>\s?', re.MULTILINE)
_RE_CODE_BLOCK_START = re.compile(r'^```[\w]*', re.MULTILINE)
_RE_CODE_BLOCK_ALT = re.compile(r'^~~~', re.MULTILINE)


# =============================================================================
# Rewrite Worker
# =============================================================================

class RewriteWorker(QThread):
    """改写工作线程"""
    chunk_received = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, text: str, config, parent=None):
        super().__init__(parent)
        self._text = text
        self._config = config

    def run(self) -> None:
        client = get_openai_client(self._config)
        if client is None:
            self.error_signal.emit("API key or Base URL is not configured.")
            self.finished_signal.emit()
            return

        try:
            system_prompt = get_rewrite_prompt(self._config)
            stream = client.chat.completions.create(
                model=self._config.selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": self._text},
                ],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    self.chunk_received.emit(chunk.choices[0].delta.content)
        except Exception as e:
            err_str = str(e).lower()
            if any(x in err_str for x in ["model", "not found", "invalid", "does not exist", "not supported"]):
                self.error_signal.emit(f"Model Error: {self._config.selected_model} is invalid.")
            else:
                self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


# =============================================================================
# Rewrite Window
# =============================================================================

class RewriteWindow(QWidget):
    """改写结果显示窗口 — UI 与 FloatingWindow 保持一致"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._worker: Optional[RewriteWorker] = None
        self._rewrite_result: str = ""
        self._current_full_response: str = ""
        self._fade_out_animation: Optional[QPropertyAnimation] = None
        self._fade_in_anim: Optional[QPropertyAnimation] = None
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_throttled_render)
        self._drag_pos: Optional[QWidget] = None

        # 窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        _shadow_margin = 20
        self.setMinimumSize(380 + _shadow_margin * 2, 280 + _shadow_margin * 2)
        self.setMaximumSize(450 + _shadow_margin * 2, 420 + _shadow_margin * 2)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(_shadow_margin, _shadow_margin, _shadow_margin, _shadow_margin)
        root_layout.setSpacing(0)

        central_widget = CentralFrame(self)
        central_widget.setObjectName("rewriteCentralFrame")
        central_widget.setStyleSheet("""
            QFrame#rewriteCentralFrame {
                background-color: #191919;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel#rewriteBrand {
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
            QPushButton#minimizeBtn {
                background-color: transparent;
                color: #a0a0a0;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 16px;
                min-width: 24px;
            }
            QPushButton#minimizeBtn:hover {
                background-color: #373737;
                color: #e5e5e5;
            }
            QPushButton#actionBtn {
                background-color: #4a9eff;
                border: none;
                border-radius: 6px;
                color: white;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                min-height: 32px;
            }
            QPushButton#actionBtn:hover { background-color: #3a8eef; }
            QPushButton#actionBtn:disabled {
                background-color: #333333;
                color: #666666;
            }
            QPushButton#cancelBtn {
                background-color: #252525;
                border: 1px solid #444444;
                border-radius: 6px;
                color: #aaaaaa;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #333333;
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

        # 顶栏：标题 + 最小化按钮
        top_row = QHBoxLayout()
        self._brand_label = QLabel("Rewrite")
        self._brand_label.setObjectName("rewriteBrand")
        top_row.addWidget(self._brand_label)
        top_row.addStretch(1)
        self._minimize_btn = QPushButton("−")
        self._minimize_btn.setObjectName("minimizeBtn")
        self._minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._minimize_btn.setToolTip("收起")
        self._minimize_btn.clicked.connect(self._start_fade_out)
        top_row.addWidget(self._minimize_btn)
        content_layout.addLayout(top_row)

        # 结果显示区域
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.document().setDefaultStyleSheet(
            "body, p, li, span { color: #EBEBEA; font-size: 14px; font-family: 'Segoe UI', sans-serif; }"
        )
        content_layout.addWidget(self._text_edit, 1)

        # 按钮区域
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._action_btn = QPushButton("Copy & Replace")
        self._action_btn.setObjectName("actionBtn")
        self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_btn.setEnabled(False)
        self._action_btn.clicked.connect(self._on_copy_and_replace)
        btn_row.addWidget(self._action_btn)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancelBtn")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._start_fade_out)
        btn_row.addWidget(self._cancel_btn)
        content_layout.addLayout(btn_row)

        root_layout.addWidget(central_widget)
        self._place_on_screen()

    def _place_on_screen(self) -> None:
        from PyQt6.QtWidgets import QApplication
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

    # ---- 显示逻辑 ----

    def show(self) -> None:
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
        if self._fade_in_anim:
            self._fade_in_anim.stop()
        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setDuration(FADE_DURATION_MS)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in_anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

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

    # ---- 状态显示 ----

    def show_loading(self) -> None:
        self._render_timer.stop()
        self._brand_label.setText("Rewriting...")
        self._current_full_response = ""
        self._text_edit.clear()
        self._text_edit.setVisible(True)
        self._action_btn.setEnabled(False)
        self._action_btn.setText("Copy & Replace")

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
        cursor.movePosition(cursor.MoveOperation.Start)
        self._text_edit.setTextCursor(cursor)

    def show_result(self, result: str) -> None:
        self._render_timer.stop()
        self._rewrite_result = result
        self._brand_label.setText("Rewrite Complete!")
        if result:
            self._text_edit.setMarkdown(result)
            cursor = self._text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._text_edit.setTextCursor(cursor)
        else:
            self._text_edit.clear()
        self._action_btn.setEnabled(True)
        self._action_btn.setText("Copy & Replace")
        self._worker = None

    def show_error(self, message: str) -> None:
        self._render_timer.stop()
        self._brand_label.setText("Rewrite Error")
        self._current_full_response = ""
        self._text_edit.setPlainText(f"Error: {message}")
        self._action_btn.setEnabled(False)

    def show_no_selection(self) -> None:
        self._render_timer.stop()
        self._brand_label.setText("No text detected")
        self._current_full_response = ""
        self._text_edit.setPlainText("Please select or copy some text, then try again.")
        self._text_edit.setVisible(True)
        self._action_btn.setEnabled(False)

    # ---- 拖拽 ----

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None

    # ---- 改写流程 ----

    def start_rewrite(self, text: str) -> None:
        if self._worker and self._worker.isRunning():
            return

        self._rewrite_result = ""
        self._current_full_response = ""
        self.show_loading()
        self._place_on_screen()
        self.show()

        self._worker = RewriteWorker(text, self._config, self)
        self._worker.chunk_received.connect(self.append_chunk)
        self._worker.finished_signal.connect(self._on_rewrite_finished)
        self._worker.error_signal.connect(self.show_error)
        self._worker.start()

    def _on_rewrite_finished(self) -> None:
        self._render_timer.stop()
        result = self._current_full_response.strip()
        self._rewrite_result = result
        self._brand_label.setText("Rewrite Complete!")
        if result:
            self._text_edit.setMarkdown(result)
            cursor = self._text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._text_edit.setTextCursor(cursor)
        self._action_btn.setEnabled(True)
        self._action_btn.setText("Copy & Replace")
        self._worker = None

    # ---- 复制粘贴 ----

    def _on_copy_and_replace(self) -> None:
        if not self._rewrite_result:
            return
        try:
            # 1. 强制复制为纯文本（去除 Markdown 格式符号）
            plain_text = self._strip_markdown(self._rewrite_result)
            pyperclip.copy(plain_text)
            logger.info("Rewrite result copied to clipboard as plain text")

            # 2. 立即隐藏窗口
            self.hide()
            self.setWindowOpacity(1.0)

            # 3. 等待足够长的时间确保窗口已完全隐藏，然后粘贴
            QTimer.singleShot(REWRITE_PASTE_DELAY_MS, self._do_paste)
        except Exception as e:
            logger.error("Failed to copy: %s", e)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """去除 Markdown 格式符号，返回纯文本"""
        text = _RE_BOLD.sub(r'\1', text)
        text = _RE_BOLD_UNDERSCORE.sub(r'\1', text)
        text = _RE_ITALIC.sub(r'\1', text)
        text = _RE_ITALIC_UNDERSCORE.sub(r'\1', text)
        text = _RE_INLINE_CODE.sub(r'\1', text)
        text = _RE_STRIKETHROUGH.sub(r'\1', text)
        text = _RE_HEADING.sub('', text)
        text = _RE_UNORDERED_LIST.sub('', text)
        text = _RE_ORDERED_LIST.sub('', text)
        text = _RE_LINK.sub(r'\1', text)
        text = _RE_IMAGE.sub('', text)
        text = _RE_HORIZONTAL_RULE.sub('', text)
        text = _RE_BLOCKQUOTE.sub('', text)
        text = _RE_CODE_BLOCK_START.sub('', text)
        text = _RE_CODE_BLOCK_ALT.sub('', text)
        return text.strip()

    def _do_paste(self) -> None:
        try:
            # 先释放所有修饰键，避免冲突
            for mod in ("ctrl", "alt", "shift", "win"):
                try:
                    keyboard.release(mod)
                except Exception:
                    pass
            # 模拟 Ctrl+V 粘贴
            keyboard.press_and_release("ctrl+v")
            logger.info("Pasted rewrite result")
        except Exception as e:
            logger.error("Failed to simulate Ctrl+V: %s", e)
