"""
LingoDrop Prompts Module
翻译和改写的提示词模板。
"""

# =============================================================================
# 翻译相关常量和提示词
# =============================================================================

MAX_TEXT_LENGTH = 800
CLIPBOARD_SYNC_DELAY_MS = 180
RENDER_THROTTLE_MS = 80
REWRITE_PASTE_DELAY_MS = 200

UI_LANG_OPTIONS = ["中文", "English"]

UI_TEXTS = {
    "English": {
        "window_title_settings": "Settings",
        "api_key": "API Key",
        "base_url": "Base URL",
        "model": "Model",
        "native_lang": "Explanation language (native)",
        "target_lang": "Target language (learn)",
        "hotkey": "Global Hotkey (e.g. ctrl+space)",
        "rewrite_hotkey": "Rewrite Hotkey (e.g. ctrl+shift+r)",
        "rewrite_prompt_label": "Rewrite System Prompt (optional)",
        "rewrite_prompt_placeholder": "Leave empty to use the default prompt for business English rewriting.",
        "reset_rewrite_prompt": "Reset to Default",
        "domain_context": "Industry / Domain Context (Optional)",
        "save": "Save",
        "cancel": "Cancel",
        "add": "Add",
        "delete": "Delete",
        "ui_lang_label": "UI Language",
        "tray_show": "Show window",
        "tray_settings": "Settings...",
        "tray_exit": "Exit",
        "tray_history": "History...",
        "placeholder_base_url": "e.g. https://api.openai.com/v1",
        "placeholder_domain": "e.g. Medical, Legal, Software development",
        "msg_api_key_required": "API Key cannot be empty.",
        "msg_model_last": "Cannot remove the last model. At least one model must remain.",
        "add_model_title": "Add Model",
        "add_model_prompt": "Model name (e.g. gpt-4o-mini):",
        "add_model_tooltip": "Add a model name",
        "remove_model_tooltip": "Remove selected model",
        "tab_translate": "Translation",
        "tab_rewrite": "Rewrite",
        "version_label": f"LingoDrop v1.0 | Standard Edition",
        "rewrite_title": "Rewrite",
        "rewrite_placeholder": "Rewrite with Ctrl+Shift+R...",
        "rewrite_waiting": "Rewriting...",
        "rewrite_success": "Done! Pasted.",
        "rewrite_no_selection": "No text selected.",
        "rewrite_error": "Rewrite failed.",
        "rewrite_only_copy": "Copy",
        "rewrite_paste_replace": "Replace",
        "rewrite_copy_success": "Copied!",
        "rewrite_paste_success": "Replaced!",
        "welcome_guide": """👋 **Welcome to LingoDrop!**

Your immersive learning assistant is running.

**⚙️ First Time Setup:**
1. Right-click the LingoDrop icon in your system tray.
2. Click **Settings...** to enter your API Key and Base URL.

----

**📖 Feature 1: Translation Learning**
Select any text (e.g., in a browser or PDF), press **[HOTKEY]** to translate with vocabulary & grammar explanations.

----

**✉️ Feature 2: Business Email Rewrite**
Select English email content, press **[REWRITE_HOTKEY]** to transform it into professional business English.

*(Click anywhere outside this window to hide it)*

— Nolan""",
    },
    "中文": {
        "window_title_settings": "设置",
        "api_key": "API 密钥",
        "base_url": "基础 URL / 代理地址",
        "model": "模型",
        "native_lang": "母语 (解释用)",
        "target_lang": "目标语 (学习用)",
        "hotkey": "全局快捷键",
        "rewrite_hotkey": "改写快捷键",
        "rewrite_prompt_label": "改写系统提示词 (可选)",
        "rewrite_prompt_placeholder": "留空则使用默认的商务英语改写提示词。",
        "reset_rewrite_prompt": "恢复默认",
        "domain_context": "行业 / 领域 (可选)",
        "save": "保存",
        "cancel": "取消",
        "add": "添加",
        "delete": "删除",
        "ui_lang_label": "界面语言",
        "tray_show": "显示窗口",
        "tray_settings": "设置...",
        "tray_exit": "退出",
        "tray_history": "历史记录...",
        "placeholder_base_url": "例如 https://api.openai.com/v1",
        "placeholder_domain": "例如 医学、法律、软件开发",
        "msg_api_key_required": "API 密钥不能为空。",
        "msg_model_last": "不能删除最后一个模型，至少保留一个。",
        "add_model_title": "添加模型",
        "add_model_prompt": "模型名称（如 gpt-4o-mini）：",
        "add_model_tooltip": "添加模型名称",
        "remove_model_tooltip": "删除当前选中的模型",
        "tab_translate": "翻译",
        "tab_rewrite": "改写",
        "version_label": f"LingoDrop v1.0 | 标准版",
        "rewrite_title": "改写",
        "rewrite_placeholder": "按 Ctrl+Shift+R 改写...",
        "rewrite_waiting": "改写中...",
        "rewrite_success": "完成！已替换。",
        "rewrite_no_selection": "未选中文字。",
        "rewrite_error": "改写失败。",
        "rewrite_only_copy": "复制",
        "rewrite_paste_replace": "替换",
        "rewrite_copy_success": "已复制！",
        "rewrite_paste_success": "已替换！",
        "welcome_guide": """👋 **欢迎使用 LingoDrop！**

您的沉浸式学习助手已启动。

**⚙️ 首次设置：**
1. 右键点击系统托盘中的 LingoDrop 图标。
2. 点击 **设置...** 输入 API 密钥与基础 URL。

----

**📖 功能一：翻译学习**
选中任意文字（如浏览器或 PDF 中），按 **[HOTKEY]** 翻译并解释词汇与语法。

----

**✉️ 功能二：商务邮件改写**
选中英文邮件内容，按 **[REWRITE_HOTKEY]** 将其转换为专业的商务英语表达。

*(点击窗外任意处可隐藏)*

— Nolan""",
    },
}


# =============================================================================
# 语言检测系统
# =============================================================================

# 语言类型枚举
class LangType:
    NATIVE = "native"      # 母语
    TARGET = "target"      # 目标语
    OTHER = "other"        # 第三语言


def _normalize_lang(lang: str) -> str:
    """统一语言名称到标准形式"""
    if not lang:
        return ""
    lang = lang.lower().strip()
    
    # 中文系列
    if lang in ["中文", "汉语", "中文简体", "中文繁体", "chinese", "mandarin"]:
        return "中文"
    
    # 英文系列
    if lang in ["英文", "英语", "english"]:
        return "English"
    
    # 韩文系列
    if lang in ["韩语", "韩文", "朝鲜语", "korean", "한국어", "ko"]:
        return "한국어"
    
    # 日语系列
    if lang in ["日语", "日文", "japanese", "日本語", "jp"]:
        return "日本語"
    
    # 德语系列
    if lang in ["德语", "德文", "german", "deutsch"]:
        return "Deutsch"
    
    # 法语系列
    if lang in ["法语", "法文", "french", "français"]:
        return "Français"
    
    # 西班牙语系列
    if lang in ["西班牙语", "西班牙文", "spanish", "español"]:
        return "Español"
    
    return lang


def detect_lang_type(text: str, native_lang: str, target_lang: str) -> str:
    """
    检测输入文本的语言类型
    
    Args:
        text: 用户输入的文本
        native_lang: 母语（如 "中文"）
        target_lang: 目标语（如 "English" 或 "한국어"）
    
    Returns:
        LangType.NATIVE: 文本是母语
        LangType.TARGET: 文本是目标语
        LangType.OTHER: 文本是第三语言
    """
    native = _normalize_lang(native_lang)
    target = _normalize_lang(target_lang)
    
    # 获取文本的语言特征
    text_lang = _detect_text_language(text)
    
    if text_lang == native:
        return LangType.NATIVE
    elif text_lang == target:
        return LangType.TARGET
    else:
        return LangType.OTHER


def _detect_text_language(text: str) -> str:
    """
    通过字符检测文本属于哪种语言
    
    Returns: 标准化后的语言名称
    """
    if not text:
        return ""
    
    # 统计字符类型
    has_korean = False
    has_japanese = False
    has_chinese = False
    has_cyrillic = False
    has_arabic = False
    latin_count = 0
    
    for char in text:
        code = ord(char)
        
        # 韩文 (Hangul)
        if 0xAC00 <= code <= 0xD7A3:
            has_korean = True
        
        # 日文平假名
        elif 0x3040 <= code <= 0x309F:
            has_japanese = True
        
        # 日文片假名
        elif 0x30A0 <= code <= 0x30FF:
            has_japanese = True
        
        # 日文汉字（扩展）
        elif 0x4E00 <= code <= 0x9FFF:
            # 中日朝共用汉字，先检查前后文
            has_chinese = True
        
        # 希腊字母
        elif 0x0370 <= code <= 0x03FF:
            pass  # 不常见，忽略
        
        # 西里尔字母（俄语等）
        elif 0x0400 <= code <= 0x04FF:
            has_cyrillic = True
        
        # 阿拉伯字母
        elif 0x0600 <= code <= 0x06FF:
            has_arabic = True
        
        # 拉丁字母（英文、德文、法文等）
        elif (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
            latin_count += 1
    
    # 优先级判断
    if has_korean:
        return "한국어"
    
    if has_japanese:
        return "日本語"
    
    # 只有当日文汉字占主导时才判断为日语
    # 如果有汉字但没有假名，可能是中文
    if has_chinese and not has_japanese:
        return "中文"
    
    if has_cyrillic:
        return "Русский"
    
    if has_arabic:
        return "العربية"
    
    # 拉丁字母为主
    if latin_count > len(text) * 0.5:
        # 进一步区分：检查是否包含英语特有词汇特征
        # 这里简化为返回英文
        return "English"
    
    return ""


# =============================================================================
# 语言特定的词汇格式定义
# =============================================================================

class VocabFormat:
    """词汇格式配置"""
    def __init__(
        self,
        format_template: str,           # 词汇展示格式
        source_type_note: str = "",     # 关于词源的额外说明
        additional_rules: str = "",     # 额外规则
        grammar_focus: str = ""          # 语法分析重点
    ):
        self.format_template = format_template
        self.source_type_note = source_type_note
        self.additional_rules = additional_rules
        self.grammar_focus = grammar_focus


# 语言特定的词汇格式表
# key: (翻译方向) -> VocabFormat
# 方向说明: "native_to_target" = 从母语译到目标语, "target_to_native" = 从目标语译到母语

LANG_SPECIFIC_FORMATS = {
    # =================================================================
    # 中文 -> English (英文需要IPA音标)
    # =================================================================
    ("中文", "English"): VocabFormat(
        format_template=(
            "• **[English Word]**: [IPA音标，如 /prəˌnʌnsiˈeɪʃən/] | 中文释义 | 词性 | "
            "[词源标注: L.=拉丁语, Gk.=希腊语, O.E.=古英语等] [常见搭配或用法提示]"
        ),
        source_type_note=(
            "标注词源以帮助记忆："
            "L. = 拉丁语来源（如 -tion, -ment, -able）；"
            "Gk. = 希腊语来源（如 psycho-, -ology）；"
            "O.E. = 古英语来源（原生词汇）；"
            "O.F. = 古法语来源（如 -ance, -ment）。"
        ),
        additional_rules=(
            "- 动词需标注及物/不及物 (vt./vi.)\n"
            "- 名词需标注可数/不可数 (C/U)\n"
            "- 注意英美拼写差异（如 -ize/-ise）"
        ),
        grammar_focus="时态/语态、主谓一致、虚拟语气、非谓语动词（不定式/分词/动名词）"
    ),
    
    # =================================================================
    # 中文 -> 한국어 (韩文需要汉字词/固有词/外来语标注)
    # =================================================================
    ("中文", "한국어"): VocabFormat(
        format_template=(
            "• **[한글 단어]**: [Romanization罗马音] | 中文释义 | "
            "[汉字词: 准确한한자] / [固有词: 순수한국어] / [外来语: 원어源的语种/원단어] | "
            "[派生说明：如汉字词可追溯的词根]"
        ),
        source_type_note=(
            "【重要】韩语词汇分类规则：\n"
            "1. 汉字词 (한자어): 由汉字组成的词，占韩语词汇60-70%\n"
            "   - 商务/法律/学术用语90%以上是汉字词\n"
            "   - 必须标注对应的准确汉字\n"
            "   - 如: 경제(經濟), 무역(貿易), 계약(契約)\n\n"
            "2. 固有词 (한국어 고유어): 韩国本土词汇\n"
            "   - 基本人称代词、数词、拟声词多为固有词\n"
            "   - 如: 나(我), 셋(三), 닭(鸡)\n\n"
            "3. 外来语 (외래어): 从其他语言直接音译\n"
            "   - 标注来源语种和原单词\n"
            "   - 如: 컴퓨터(computer, 英语), 바나나(banana, 英语→日语→韩语)"
        ),
        additional_rules=(
            "- 汉字词优先判断：遇到商务/学术词汇，先假设是汉字词\n"
            "- 注意汉字词的书写：完全用汉字/完全用韩文/混用三种形式\n"
            "- 外来语注意是直接来自英语还是经过日语中转\n"
            "- 复合词需拆分解释各组成部分"
        ),
        grammar_focus="敬语阶称(합쇼체/해체)、主客助词(은/는/이/가)、终结词尾、连接助词"
    ),
    
    # =================================================================
    # English -> 中文 (从英文翻译到中文)
    # =================================================================
    ("English", "中文"): VocabFormat(
        format_template=(
            "• **[中文词语]**: [对应英文单词] | 简要英文释义 | "
            "[文言词汇/白话/方言/网络用语标注] | [近义词/反义词]"
        ),
        source_type_note=(
            "根据语境选择合适的翻译："
            "口语/书面语、文言/白话、行业术语等。"
        ),
        additional_rules=(
            "- 中文翻译要符合现代汉语规范\n"
            "- 注意量词搭配\n"
            "- 成语/俗语要标注来源"
        ),
        grammar_focus="量词使用、动词搭配、主谓结构"
    ),
    
    # =================================================================
    # 한국어 -> 中文 (从韩文翻译到中文)
    # =================================================================
    ("한국어", "中文"): VocabFormat(
        format_template=(
            "• **[中文翻译]**: [对应韩文한글] | [汉字词则标出한자] | "
            "[固有词/外来语标注] | 中文释义"
        ),
        source_type_note=(
            "韩译中注意事项：\n"
            "- 汉字词需要写出对应汉字，便于理解词义\n"
            "- 固有词注意韩语特有的表达方式\n"
            "- 外来语注意翻译的自然度"
        ),
        additional_rules=(
            "- 汉字词标注汉字：경제→经济，계약→合同\n"
            "- 注意韩语敬语在中文中的表达\n"
            "- 外来语选择中文中已有的对应翻译"
        ),
        grammar_focus="韩语句子敬语分析、主语省略、终结词尾含义"
    ),
    
    # =================================================================
    # English -> 한국어 (从英文翻译到韩文)
    # =================================================================
    ("English", "한국어"): VocabFormat(
        format_template=(
            "• **[한글]**: [Romanization] | 英文释义 | "
            "[汉字词: 한자] / [固有词] / [外来语: 원어원단어] | "
            "[韩文用法说明]"
        ),
        source_type_note=(
            "英译韩注意事项：\n"
            "- 区分汉字词和固有词的使用场景\n"
            "- 商务英语常用汉字词表达\n"
            "- 注意韩语的敬语表达"
        ),
        additional_rules=(
            "- 汉字词优先用于正式/书面场合\n"
            "- 日常会话可用固有词更自然\n"
            "- 外来语在年轻群体中使用频繁"
        ),
        grammar_focus="敬语阶称选择、主客助词、终结词尾风格"
    ),
}


# =============================================================================
# 通用格式（用于未特殊定义的语言组合）
# =============================================================================

GENERIC_VOCAB_FORMAT = VocabFormat(
    format_template=(
        "• **[Target Word]**: [Pronunciation/音标] | [Native Lang Meaning/母语释义] | "
        "[Part of Speech/词性] | [Etymology/词源 if known] [Usage notes/用法说明]"
    ),
    source_type_note=(
        "词源标注参考：L.=Latin, Gk.=Greek, O.E.=Old English, O.F.=Old French, "
        "G.=German, etc. 标注词源有助于记忆。"
    ),
    additional_rules=(
        "- 使用目标语言标注词性\n"
        "- 提供至少一个使用例句或搭配\n"
        "- 注意正式/非正式语体区别"
    ),
    grammar_focus="句子结构、基本语法规则、常见错误提醒"
)


def get_vocab_format(native_lang: str, target_lang: str) -> VocabFormat:
    """获取指定语言对的词汇格式配置"""
    native = _normalize_lang(native_lang)
    target = _normalize_lang(target_lang)
    
    key = (native, target)
    if key in LANG_SPECIFIC_FORMATS:
        return LANG_SPECIFIC_FORMATS[key]
    
    # 反向查找（如 English->中文 和 中文->English 都定义了）
    reverse_key = (target, native)
    if reverse_key in LANG_SPECIFIC_FORMATS:
        return LANG_SPECIFIC_FORMATS[reverse_key]
    
    # 都找不到，返回通用格式
    return GENERIC_VOCAB_FORMAT


# =============================================================================
# 场景提示词构建
# =============================================================================

def _build_native_input_prompt(
    vocab_fmt: VocabFormat,
    native_lang: str,
    target_lang: str,
    domain_context: str
) -> str:
    """
    场景一：用户输入的是母语
    → 翻译为目标语言，用母语解释目标语言的词汇
    """
    domain_instruction = ""
    if (domain_context or "").strip():
        domain_instruction = (
            f"\n【专业领域】用户从事领域: {domain_context.strip()}\n"
            f"必须使用该领域的标准术语，保持专业性。\n"
        )
    
    return f"""你是一位精通{native_lang}和{target_lang}的双语语言专家，专注于精准翻译和词汇学习。

{domain_instruction}## 你的任务

用户输入的是 {native_lang}，你需要：

**一、翻译**
将 {native_lang} 准确、地道地翻译为 {target_lang}。

**二、关键词汇解析**
从翻译后的 {target_lang} 文本中提取关键词汇，用 {native_lang} 进行详细解析。

【词汇格式要求 - 请严格遵循】
{vocab_fmt.format_template}

【词源说明】
{vocab_fmt.source_type_note}

【额外规则】
{vocab_fmt.additional_rules}

**三、语法拆解**
分析 {target_lang} 句子的语法结构。

【语法分析重点】
{vocab_fmt.grammar_focus}

【语法格式要求】
- 使用 • 符号，不要使用 - 或数字编号
- 保持简洁，每点一行
- {native_lang} 解释

## 输出格式（纯文本，无Markdown格式）
- 标题使用全大写或分隔线
- 词汇列表使用规定的 • 格式
- 避免使用粗体、斜体、# 号等Markdown标记
- 用纯文本分隔各部分
"""


def _build_target_input_prompt(
    vocab_fmt: VocabFormat,
    native_lang: str,
    target_lang: str,
    domain_context: str
) -> str:
    """
    场景二：用户输入的是目标语言
    → 翻译为母语，用母语解释目标语言的词汇
    """
    domain_instruction = ""
    if (domain_context or "").strip():
        domain_instruction = (
            f"\n【专业领域】用户从事领域: {domain_context.strip()}\n"
            f"必须使用该领域的标准术语，保持专业性。\n"
        )
    
    return f"""你是一位精通{native_lang}和{target_lang}的双语语言专家，专注于精准翻译和词汇学习。

{domain_instruction}## 你的任务

用户输入的是 {target_lang}，你需要：

**一、翻译**
将 {target_lang} 准确、地道地翻译为 {native_lang}。

**二、关键词汇解析**
从 {target_lang} 原文中提取关键词汇，用 {native_lang} 进行详细解析。

【词汇格式要求 - 请严格遵循】
{vocab_fmt.format_template}

【词源说明】
{vocab_fmt.source_type_note}

【额外规则】
{vocab_fmt.additional_rules}

**三、语法拆解**
分析 {target_lang} 句子的语法结构。

【语法分析重点】
{vocab_fmt.grammar_focus}

【语法格式要求】
- 使用 • 符号，不要使用 - 或数字编号
- 保持简洁，每点一行
- {native_lang} 解释

## 输出格式（纯文本，无Markdown格式）
- 标题使用全大写或分隔线
- 词汇列表使用规定的 • 格式
- 避免使用粗体、斜体、# 号等Markdown标记
- 用纯文本分隔各部分
"""


def _build_other_input_prompt(
    vocab_fmt: VocabFormat,
    native_lang: str,
    target_lang: str,
    domain_context: str
) -> str:
    """
    场景三：用户输入的是第三语言
    → 翻译为目标语言，用母语解释目标语言的词汇
    """
    domain_instruction = ""
    if (domain_context or "").strip():
        domain_instruction = (
            f"\n【专业领域】用户从事领域: {domain_context.strip()}\n"
            f"必须使用该领域的标准术语，保持专业性。\n"
        )
    
    return f"""你是一位多语言专家，精通{native_lang}、{target_lang}以及其他多种语言。

{domain_instruction}## 重要说明
用户输入的可能是第三种语言（如日语、俄语、德语等），不是 {native_lang} 也不是 {target_lang}。

## 你的任务

**一、语言识别**
首先判断输入文本属于哪种语言（如果能判断的话）。

**二、翻译**
将输入文本翻译为 {target_lang}（用户的目标语言）。

**三、关键词汇解析**
从翻译后的 {target_lang} 文本中提取关键词汇，用 {native_lang} 进行详细解析。

【词汇格式要求 - 请严格遵循】
{vocab_fmt.format_template}

【词源说明】
{vocab_fmt.source_type_note}

【额外规则】
{vocab_fmt.additional_rules}

**四、语法拆解**
分析 {target_lang} 句子的语法结构。

【语法分析重点】
{vocab_fmt.grammar_focus}

【语法格式要求】
- 使用 • 符号，不要使用 - 或数字编号
- 保持简洁，每点一行
- {native_lang} 解释

## 输出格式（纯文本，无Markdown格式）
- 标题使用全大写或分隔线
- 词汇列表使用规定的 • 格式
- 避免使用粗体、斜体、# 号等Markdown标记
- 用纯文本分隔各部分
"""


# =============================================================================
# 主提示词构建函数
# =============================================================================

def build_system_prompt(
    native_language: str,
    target_language: str,
    input_text: str = "",
    domain_context: str = ""
) -> str:
    """
    构建翻译功能的系统提示词
    
    Args:
        native_language: 母语（用于解释）
        target_language: 目标语言（用户正在学习的语言）
        input_text: 用户的输入文本（可选，用于检测语言类型）
        domain_context: 领域上下文（可选）
    
    Returns:
        完整的系统提示词
    """
    # 获取语言特定的词汇格式
    vocab_fmt = get_vocab_format(native_language, target_language)
    
    # 检测输入语言类型
    if input_text:
        lang_type = detect_lang_type(input_text, native_language, target_language)
    else:
        # 默认假设输入是母语
        lang_type = LangType.NATIVE
    
    # 根据场景选择对应的提示词模板
    if lang_type == LangType.NATIVE:
        return _build_native_input_prompt(vocab_fmt, native_language, target_language, domain_context)
    elif lang_type == LangType.TARGET:
        return _build_target_input_prompt(vocab_fmt, native_language, target_language, domain_context)
    else:
        return _build_other_input_prompt(vocab_fmt, native_language, target_language, domain_context)


def build_system_prompt_with_direction(
    native_language: str,
    target_language: str,
    direction: str,
    domain_context: str = ""
) -> str:
    """
    根据明确的翻译方向构建提示词（兼容旧接口）
    
    Args:
        native_language: 母语
        target_language: 目标语言
        direction: 翻译方向 "to_target" / "to_native"
        domain_context: 领域上下文
    """
    vocab_fmt = get_vocab_format(native_language, target_language)
    
    if direction == "to_target":
        return _build_native_input_prompt(vocab_fmt, native_language, target_language, domain_context)
    elif direction == "to_native":
        return _build_target_input_prompt(vocab_fmt, native_language, target_language, domain_context)
    else:
        # 默认行为
        return _build_native_input_prompt(vocab_fmt, native_language, target_language, domain_context)


def get_system_prompt(config, input_text: str = "") -> str:
    """
    返回系统提示词：使用默认构建逻辑。
    
    Args:
        config: 配置对象
        input_text: 用户的输入文本（用于自动检测语言类型）
    """
    return build_system_prompt(
        native_language=config.native_language,
        target_language=config.target_language,
        input_text=input_text,
        domain_context=config.domain_context or ""
    )


# =============================================================================
# 改写相关提示词
# =============================================================================

def build_rewrite_prompt(simple_mode: bool = True) -> str:
    """
    改写提示词：将普通英文转换为商务英语格式。
    保持原文长度相当，只优化表达的专业度和商务感。
    
    Args:
        simple_mode: True = 简单词汇模式（默认），False = 标准商务模式
    """
    if simple_mode:
        return """You are a professional business English writer.

## TASK
Rewrite the user's text into a professional business English email.
- Output MUST be in English
- Keep ALL content - every paragraph, every line, no skipping
- Preserve original structure and formatting
- Use simple, clear English words
- Dates in M/D format (4/3, not April 3rd)
- Bullet format:
-.
 Item 1
-.
 Item 2
- Plain text only, no markdown

## EXAMPLES

Input: Hi, can you send me the report?
Output: Hi, could you please send me the report?

Input: 
The project is done.
Here are the results:
1. Sales up 20%
2. Costs down 15%
Output: 
The project has been completed.
Here are the results:
-.
 Sales up 20%
-.
 Costs down 15%

TEXT TO TRANSFORM:

"""
    else:
        return """You are a professional business English editor.

## TASK
Rewrite into professional business English.
- Keep ALL content - preserve every paragraph and line
- Maintain original structure and formatting
- Use professional business vocabulary
- Plain text only

TEXT TO REWRITE:

"""


def get_rewrite_prompt(config, simple_mode: bool = True) -> str:
    """
    获取改写提示词。
    如果配置中有自定义改写提示词，则使用自定义提示词；否则使用默认提示词。
    
    Args:
        config: 配置对象
        simple_mode: True = 简单词汇模式（默认），False = 标准商务模式
    """
    custom_prompt = getattr(config, 'rewrite_system_prompt', None)
    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip()
    return build_rewrite_prompt(simple_mode=simple_mode)
