# LingoDrop — 当前进度说明

用于梳理「已经做到什么」、方便规划下一步的简要说明。

---

## 项目定位

**LingoDrop**：桌面沉浸式学习助手，支持**翻译学习**与**商务改写**两大功能。

- **翻译学习**：选中文字后按全局热键（或先复制再按热键），即可把内容发给 LLM，得到**目标语翻译 + 以母语解释的词汇/语法 + Markdown 渲染**。
- **商务改写**：选中英文内容后按改写热键，将内容转换为专业的商务英语，支持一键复制并粘贴替换原文。

支持在设置中选择解释语言、目标语言、模型、行业领域（Domain Context）和自定义系统提示词。

---

## 已完成功能

### 1. 双热键系统

#### 1.1 翻译热键（默认 `Ctrl+Space`）

- 全局热键，可在 Settings 中修改为其他组合（如 `Ctrl+Alt+S` 等）。
- 任意窗口下可用（`python main.py` 或 `pythonw main.py`，Windows 下若无效可尝试管理员运行）。

#### 1.2 Direct Selection（Bob 式一键分析）

- 按下热键后，在热键回调线程内立即模拟 `Ctrl+C`（保证焦点仍在选中文字的窗口），再将「读取剪贴板」投递到主线程。
- 若热键为 Ctrl+Alt+字母 等组合，会先**释放 Ctrl/Alt/Shift** 再模拟 `Ctrl+C`，避免系统收到 Ctrl+Alt+C 导致应用不识别为「复制」。
- 约 180ms 延迟后再读取剪贴板，避免读到旧内容。
- 若未选中任何文字（剪贴板仍为空），则显示 **「No text detected」** 提示（约 2.5 秒后自动恢复）。

#### 1.3 改写热键（默认 `Shift+Ctrl+Alt`）

- 独立的热键触发改写流程：读取剪贴板 → LLM 改写 → 自动粘贴替换。
- 文本长度上限 2000 字符，超出则截断。

### 2. 剪贴板处理

- 仅处理纯文本；非文本（如图片）静默忽略。
- **翻译文本长度上限 800 字符**：若超过则**截断到 800**，并在发给 LLM 的文本末尾追加 `(Text truncated for performance)`。
- 剪贴板为空或不可读时显示「No text detected」，不崩溃。
- 日志：错误/警告用 `logging` 输出到 stderr，无弹窗。

### 3. LLM 接入与流式输出

#### 3.1 配置与调用

- API 与模型等均来自 `config.json`。
- 使用 `openai` 官方 Python 客户端；模型由 `config.selected_model` 决定。
- 流式输出：`stream=True`，回复以流式形式逐字返回；悬浮窗用 **Markdown 实时渲染**。

#### 3.2 语言检测系统

- 自动检测输入文本的语言类型：
  - **母语输入**：翻译为目标语言，解释目标语词汇/语法
  - **目标语输入**：翻译为母语，解释目标语词汇/语法
  - **第三语言输入**：翻译为目标语言，用母语解释
- 支持的语言：韩语（한국어）、日语（日本語）、中文、英语、德语、法语、西班牙语等。
- 通过 Unicode 字符范围检测：韩文 Hangul (AC00-D7A3)、日文平假名/片假名 (3040-30FF)、CJK 汉字 (4E00-9FFF)、西里尔字母、阿拉伯字母等。

#### 3.3 语言特定的词汇格式

- **中文 → English**：IPA 音标 + 词源标注（L.=拉丁语, Gk.=希腊语, O.E.=古英语, O.F.=古法语）+ 词性 + 常见搭配
- **中文 → 한국어**：汉字词/固有词/外来语分类 + 准确汉字标注 + 词源说明
- **English → 中文**：中文翻译 + 英文释义 + 文言/白话/方言标注 + 近义词/反义词
- **한국어 → 中文**：中文翻译 + 汉字词标注 + 固有词/外来语标注
- **English → 한국어**：韩文罗马音 + 英文释义 + 词源分类 + 用法说明

#### 3.4 提示词结构

- **默认 3 段式**：翻译、关键词汇、语法拆解
- **小节标题**：强制使用解释语言（如中文：翻译、关键词汇、语法拆解），不会出现英文标题。
- **输出格式**：强制纯文本格式，避免 Markdown 列表（使用 • 符号），确保 PyQt6 正确渲染。
- **Domain Context**：若在 Settings 中填写「Industry / Domain Context」，会在系统提示中注入专业术语要求。
- **自定义系统提示**：Settings 底部可填写 Custom System Prompt；支持占位符 `{native_language}`、`{target_language}`、`{domain_context}`。

### 4. 改写功能（Rewrite）

#### 4.1 RewriteWindow

- 独立浮动窗口，UI 与翻译窗口保持一致的深色 Notion 风格。
- 流式显示改写结果，Markdown 实时渲染。
- 包含操作按钮：**Copy & Replace**（复制并自动粘贴替换）和 **Cancel**。
- 自动去除 Markdown 格式符号，确保粘贴为纯文本。

#### 4.2 Markdown 清理

- 预编译正则表达式，高效去除所有 Markdown 格式：
  - 粗体、斜体、下划线、行内代码、删除线
  - 标题、列表、链接、图片、分割线、引用、代码块
- 保留纯文本内容用于粘贴。

#### 4.3 自动粘贴流程

1. 将清理后的纯文本复制到剪贴板
2. 隐藏改写窗口
3. 等待 200ms 确保窗口已完全隐藏
4. 释放所有修饰键（Ctrl/Alt/Shift/Win）
5. 模拟 `Ctrl+V` 粘贴

#### 4.4 改写提示词

- 默认提示词要求：保持原意、维持篇幅 (±10%)、保留原文格式和数据
- 专业词汇替换：口语词→商务表达、正式连接词（furthermore/therefore/consequently）
- 特殊处理：代码/术语不变、已正式文本保守修改、极短文本保护
- 支持自定义改写系统提示词

### 5. GUI 与桌面集成

#### 5.1 应用形态

- **PyQt6 主循环**：`QApplication` 作为事件循环，不再依赖终端交互。
- **系统托盘**：
  - 使用 `QSystemTrayIcon` 在系统托盘常驻图标；
  - 托盘右键菜单包含：**显示窗口**、**设置...**、**退出**；
  - 菜单文案随界面语言切换中/英；
  - 单击/双击托盘图标可重新唤起悬浮窗口。
- **退出路径**：通过托盘菜单 `Exit` 触发 `app.quit()`，干净退出所有线程。

#### 5.2 翻译悬浮窗 UI

- **窗口与视觉**：
  - 顶层为 QWidget，`WA_TranslucentBackground`，`FramelessWindowHint` + `WindowStaysOnTopHint` + `Tool`；
  - 内容放在内层 QFrame（central_widget）：背景 `#191919`、圆角 8px、边框 `#333333`；
  - **QGraphicsDropShadowEffect**（模糊 20、偏移 0,4、颜色 rgba(0,0,0,160)）实现柔和阴影。
- **布局与控件**：
  - 顶行：头部图标 +「LingoDrop」品牌标签 + 最小化按钮（−）；
  - 主体：只读 **QTextEdit**，流式输出以 **Markdown** 渲染。
- **位置与拖拽**：主屏右侧偏中放置；内层 CentralFrame 将鼠标事件转发给顶层，实现整窗拖拽。

#### 5.3 改写悬浮窗 UI

- 与翻译窗口一致的视觉风格，但独立窗口。
- 顶行显示「Rewrite」品牌标签 + 最小化按钮。
- 主体为只读 QTextEdit 显示流式改写结果。
- 底部按钮区：「Copy & Replace」主操作按钮（蓝色）+「Cancel」按钮。
- 完成后按钮变为可点击状态。

#### 5.4 多线程与信号/槽

- **LLMWorker / RewriteWorker（QThread）**：
  - 封装为单独的 Worker 线程，只负责调用 API 流式输出；
  - 通过信号暴露：`chunk_received(str)`、`finished_signal()`、`error_signal(str)`；
  - 对 API 异常进行捕获并通过 `error_signal` 上报，不让异常穿透到 GUI 线程。
- **流式回传**：
  - `stream_llm_chunks()` 把每个 LLM 流式片段作为 `str` 逐个 `yield`；
  - Worker 在 `run()` 中遍历生成器并发出 `chunk_received` 信号；
  - 悬浮窗在 `append_chunk()` 中将新片段追加到 `_current_full_response`，再对整段调用 `setMarkdown()` 实现实时渲染。
- **生命周期管理**：防止多个并发请求互相抢占 UI。

#### 5.5 Apple 式交互

- **点击窗外自动隐藏**：
  - `focusOutEvent` 仅在宽限期（350ms）结束后才启动 200ms 隐藏定时器；
  - 热键触发时调用 `reset_auto_hide_grace()` 重新给宽限；
  - LLM/Rewrite 运行期间不触发自动隐藏。
- **show() 逻辑**：仅当窗口当前隐藏时才触发淡入；若窗口已可见则只置顶/激活。
- **淡入淡出**：`QPropertyAnimation` 对 `windowOpacity` 做 150ms 淡入/淡出。

#### 5.6 Markdown 渲染节流优化

- 问题：流式输出时每个 chunk 都调用 `setMarkdown()` 重新渲染，高频输出时性能消耗严重。
- 方案：添加 80ms 节流机制，将多个 chunk 批量处理后再渲染。
- 效果：即使 LLM 高频输出，渲染次数被限制在每秒约 12 次，大幅降低 CPU 消耗。

---

## 6. 用户配置与设置界面

### 6.1 配置管理（config.json + ConfigManager）

- **配置文件**：`~/.lingodrop/config.json`（用户主目录），UTF-8 JSON。
- **ConfigManager 字段**：
  - `api_key`、`base_url`、`hotkey`（默认 `ctrl+space`）
  - `native_language`、`target_language`（解释语言与目标语言）
  - `selected_model`、`model_list`
  - `custom_system_prompt`、`domain_context`
  - `ui_language`：界面语言（中文/English），默认中文
  - `rewrite_hotkey`：改写热键（默认 `shift+ctrl+alt`）
  - `rewrite_system_prompt`：自定义改写提示词

### 6.2 设置窗口 SettingsDialog（QDialog）

- **两页 Tab 布局**：
  - **翻译页**：UI Language、API Key、Base URL、Model（下拉 + Add/Delete）、Global Hotkey、母语、目标语、Domain Context
  - **改写页**：Rewrite Hotkey、改写系统提示词（多行编辑器 + 重置按钮）
- **UI Language 切换**：最顶部下拉选择「中文」或「English」，切换后即时刷新本窗口内所有标签与按钮文案。
- **字段要点**：
  - **Model**：`QComboBox` 从 `model_list` 填充，Add 通过 `QInputDialog` 添加，Delete 删除当前项
  - **Rewrite System Prompt**：多行 QPlainTextEdit；留空则使用默认商务英语改写提示词
- **Notion 风格 QSS**：#252525 背景、#444444 边框、自定义下拉箭头等。
- **Save/Cancel**：校验 API Key 非空后写入 `config.json` 并触发热键/配置更新。

### 6.3 动态热键更新

- `HotkeyBridge` 作为 Qt 信号桥，对外提供 `hotkey_triggered` 和 `rewrite_triggered` 信号。
- `update_hotkey_registration()`：先卸载旧热键，再注册新热键，无需重启应用即可生效。

### 6.4 首次启动检查

- 应用启动后，先显示欢迎指南窗口（展示热键说明和功能介绍）。
- 若 `api_key` 为空，则自动弹出设置窗口，强制用户先完成配置。
- 若用户取消且仍未填 `api_key`，程序会安全退出并记录日志。

### 6.5 LLM 客户端与配置解耦

- 通过 `get_openai_client(config)` 按需创建客户端，不再依赖环境变量。
- 每次调用时使用当前配置创建客户端，修改 API Key 或 Base URL 后**下一次调用立即生效**。
- 若配置缺失，Worker 会通过 `error_signal` 把错误信息反馈到 UI。

---

## 技术栈与依赖

- **语言**：Python 3
- **依赖**：`keyboard`（全局热键）、`pyperclip`（剪贴板）、`openai`（API 客户端）、`PyQt6`（GUI 与托盘）
- **安装**：`pip install -r requirements.txt` 或
  `pip install keyboard pyperclip openai PyQt6`

---

## 当前使用方式

1. 安装依赖：`pip install -r requirements.txt`
2. 运行：`python main.py` 或 `pythonw main.py`（无控制台）
3. 首次运行若未配置 API Key，会弹出 Settings；填好 API Key、Base URL、热键等后保存。
4. **翻译使用**：先复制文本，再按翻译热键（默认 Ctrl+Space）；或直接选中文字后按热键（Direct Selection）。
5. **改写使用**：选中英文内容，按改写热键（默认 Shift+Ctrl+Alt）；改写完成后点击「Copy & Replace」复制并自动粘贴替换原文。
6. 可选：在 Settings 中填写 **Industry / Domain Context** 使翻译更专业；或使用 **Custom System Prompt** 自定义指令。
7. 点击窗口外可自动隐藏；托盘「设置...」修改设置、「退出」退出。

---

## 尚未实现（可作下一步方向）

- **历史/收藏**：不保存查询记录；可加本地历史或收藏（如 SQLite / JSON）
- **高级配置化**：窗口大小/位置记忆、字体大小等仍可在代码中改或未来做成图形设置
- **安装包/常驻**：可考虑 PyInstaller 打包 exe、开机自启或安装式常驻
- **多语言检测增强**：可引入字符频率分析或机器学习模型提高检测准确率
- **改写预览模式**：在自动粘贴前允许用户编辑/确认改写结果
- **TTS 语音朗读**：朗读翻译结果或目标语输入（需集成 edge-tts 等 TTS 引擎）
