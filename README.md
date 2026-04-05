# LingoDrop

> 桌面沉浸式翻译学习与商务改写助手 | Desktop Immersive Translation & Business Rewriting Assistant

---

## 简介 | Introduction

**LingoDrop** 是一款优雅的桌面工具，将沉浸式翻译学习与专业商务改写功能完美融合。

**LingoDrop** is an elegant desktop tool that seamlessly combines immersive translation learning with professional business rewriting capabilities.

---

## 功能亮点 | Key Features

### 翻译学习 | Translation Learning

| 功能 | Feature | 说明 | Description |
|------|---------|------|-------------|
| 🎯 智能翻译 | Smart Translation | 自动检测源语言，提供精准翻译 | Automatically detects source language for accurate translations |
| 📚 词汇解析 | Vocabulary Analysis | 详细的词汇/语法解释 | Detailed vocabulary and grammar explanations |
| ✨ Markdown 渲染 | Markdown Rendering | 优雅的格式化输出 | Beautifully formatted output |
| ⚡ 直接选取 | Direct Selection | 选中文字后按热键，无需复制 | Select text and press hotkey, no copy needed |

### 商务改写 | Business Rewriting

| 功能 | Feature | 说明 | Description |
|------|---------|------|-------------|
| 📝 一键改写 | One-Click Rewrite | 快速转换为专业商务英语 | Instantly convert to professional business English |
| 📋 自动粘贴 | Auto-Paste | 改写后自动替换原文 | Automatically replace original text after rewriting |
| 🎨 格式保留 | Format Preservation | 保持原文结构和数据 | Preserves original structure and data |

---

## 快捷键 | Hotkeys

| 操作 | Operation | 默认快捷键 | Default Hotkey |
|------|-----------|-----------|----------------|
| 翻译 | Translate | `Ctrl + Space` | 全局热键，可在设置中修改 |
| 改写 | Rewrite | `Shift + Ctrl + Alt` | 全局热键，可在设置中修改 |

---

## 使用方法 | How to Use

### 首次运行 | First Launch

1. 运行应用 | Run the application: `python main.py`
2. 若未配置 API Key，将自动弹出设置窗口 | If API Key is not configured, settings window will appear automatically
3. 填写必要的配置信息 | Fill in the required configuration:
   - **API Key**: 你的 API 密钥 | Your API key
   - **Base URL**: API 地址（根据你的服务提供商） | API URL (according to your provider)
   - **模型 | Model**: 选择使用的 LLM 模型 | Choose the LLM model to use

### 翻译使用 | Translation Usage

**方式一 | Method 1: 直接选取**
1. 选中目标文字
2. 按翻译热键（默认 `Ctrl+Space`）
3. 翻译结果将以 Markdown 格式实时显示

1. Select the target text
2. Press translation hotkey (default `Ctrl+Space`)
3. Translation results display in real-time with Markdown formatting

**方式二 | Method 2: 先复制**
1. 复制需要翻译的文本
2. 按翻译热键
3. 查看翻译结果

1. Copy the text to translate
2. Press translation hotkey
3. View the translation results

### 改写使用 | Rewrite Usage

1. 选中需要改写的英文内容
2. 按改写热键（默认 `Shift+Ctrl+Alt`）
3. 等待流式改写完成
4. 点击「Copy & Replace」自动复制并粘贴替换原文

1. Select the English text to rewrite
2. Press rewrite hotkey (default `Shift+Ctrl+Alt`)
3. Wait for streaming rewrite to complete
4. Click "Copy & Replace" to copy and auto-paste

---

## 设置选项 | Settings Options

### 翻译设置 | Translation Settings

| 选项 | Option | 说明 | Description |
|------|--------|------|-------------|
| 母语 | Native Language | 你的母语（用于解释翻译） | Your native language (for explanations) |
| 目标语 | Target Language | 学习的目标语言 | Target language for learning |
| 领域上下文 | Domain Context | 可选的专业领域提示 | Optional professional domain context |
| 自定义提示词 | Custom System Prompt | 自定义 LLM 行为指令 | Customize LLM behavior instructions |

### 界面语言 | UI Language

支持切换界面语言 | Supports switching interface language:
- 中文
- English

---

## 支持的语言 | Supported Languages

| 语言 | Language | 说明 | Description |
|------|----------|------|-------------|
| 🇨🇳 中文 | Chinese | 简体/繁体 | Simplified/Traditional |
| 🇬🇧 英语 | English | - | - |
| 🇰🇷 韩语 | Korean | 한국어 | - |
| 🇯🇵 日语 | Japanese | 日本語 | - |
| 🇩🇪 德语 | German | Deutsch | - |
| 🇫🇷 法语 | French | Français | - |
| 🇪🇸 西班牙语 | Spanish | Español | - |
| 以及更多... | And more... | 通过字符范围检测 | Via character range detection |

---

## 技术栈 | Tech Stack

| 组件 | Component | 用途 | Purpose |
|------|-----------|------|---------|
| Python 3 | Python 3 | 编程语言 | Programming Language |
| PyQt6 | PyQt6 | 图形界面与系统托盘 | GUI and System Tray |
| OpenAI SDK | OpenAI SDK | LLM API 接入 | LLM API Integration |
| keyboard | keyboard | 全局热键 | Global Hotkeys |
| pyperclip | pyperclip | 剪贴板操作 | Clipboard Operations |

---

## 安装 | Installation

### 方式一 | Method 1: 使用 requirements.txt

```bash
pip install -r requirements.txt
```

### 方式二 | Method 2: 手动安装依赖

```bash
pip install keyboard pyperclip openai PyQt6
```

---

## 运行 | Running

```bash
# 普通模式（有控制台）
python main.py

# 无控制台模式（Windows）
pythonw main.py
```

---

## 项目结构 | Project Structure

```
LingoDrop/
├── main.py              # 应用入口 | Application entry point
├── config_manager.py    # 配置管理 | Configuration management
├── ui/
│   ├── translation_window.py  # 翻译悬浮窗 | Translation floating window
│   ├── rewrite_window.py      # 改写窗口 | Rewrite window
│   ├── settings_dialog.py     # 设置对话框 | Settings dialog
│   └── welcome_guide.py       # 欢迎指南 | Welcome guide
├── services/
│   ├── llm_service.py    # LLM 服务 | LLM service
│   ├── hotkey_service.py  # 热键服务 | Hotkey service
│   └── clipboard_service.py # 剪贴板服务 | Clipboard service
├── utils/
│   └── language_detector.py # 语言检测 | Language detection
└── assets/               # 资源文件 | Assets
```

---

## 配置说明 | Configuration

配置文件位置 | Configuration file location: `~/.lingodrop/config.json`

### 配置文件示例 | Config File Example

```json
{
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "selected_model": "gpt-4o-mini",
    "model_list": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "hotkey": "ctrl+space",
    "rewrite_hotkey": "shift+ctrl+alt",
    "native_language": "Chinese",
    "target_language": "English",
    "ui_language": "Chinese",
    "domain_context": "",
    "custom_system_prompt": "",
    "rewrite_system_prompt": ""
}
```

---

## 高级功能 | Advanced Features

### 语言特定词汇格式 | Language-Specific Vocabulary Format

- **中文 → English**: IPA音标 + 词源标注 + 词性 + 常见搭配
- **中文 → 한국어**: 汉字词/固有词/外来语分类 + 汉字标注
- **English → 中文**: 中文翻译 + 英文释义 + 文言/白话标注
- **한국어 → 中文**: 中文翻译 + 汉字词标注 + 词源分类

### Domain Context（领域上下文）

在设置中填写行业/领域信息，可获得更专业的翻译：

Fill in industry/domain context in settings for more professional translations:

```
例如 | For example:
- 医学: Medical terminology and drug names
- 法律: Legal terminology and case references  
- 科技: Technical jargon and abbreviations
- 金融: Financial terms and market terminology
```

---

## 常见问题 | FAQ

### Q: 热键不生效怎么办？ | Q: Hotkey not working?

**Windows**: 尝试以管理员权限运行 | Try running as administrator

### Q: 翻译结果不准确？ | Q: Translation not accurate?

调整设置中的「领域上下文」或「自定义提示词」以获得更好的结果。

Adjust "Domain Context" or "Custom System Prompt" in settings for better results.

### Q: 如何更改界面语言？ | Q: How to change UI language?

在设置窗口顶部选择「界面语言」下拉框即可切换。

Select "UI Language" dropdown at the top of the settings window.

---

## 未来计划 | Roadmap

- [ ] 历史记录与收藏功能 | History and favorites
- [ ] 窗口位置记忆 | Window position memory
- [ ] 安装包打包 | Installer packaging
- [ ] 改写预览模式 | Rewrite preview mode
- [ ] 语音朗读 (TTS) | Text-to-Speech
- [ ] 多语言检测增强 | Enhanced language detection

---

## 许可证 | License

本项目仅供个人学习使用。

This project is for personal learning use only.

---

## 联系方式 | Contact

如有问题或建议，欢迎提交 Issue。

For questions or suggestions, feel free to submit an Issue.

---

<p align="center">
  <strong>LingoDrop</strong> — 让语言学习更沉浸 | Making Language Learning More Immersive
</p>
