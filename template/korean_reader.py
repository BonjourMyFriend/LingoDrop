import time
import re
import pyperclip
import asyncio
import edge_tts
import pygame
import os

# --- 配置 ---
# 微软韩语女声 (SunHi) 或男声 (InJoon)
VOICE = "ko-KR-SunHiNeural"
# 语速 (默认 +0%)
RATE = "+0%"
TEMP_FILE = "temp_korean.mp3"

# --- 核心逻辑 ---
async def play_audio_fast(text):
    print(f"⚡ 正在获取发音: {text[:10]}...")
    start = time.time()
    
    try:
        # 1. 生成音频 (使用 Edge 免费接口)
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(TEMP_FILE)
        
        network_time = time.time() - start
        
        # 2. 播放音频
        # 只有在还没播放时才加载，防止报错
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        pygame.mixer.music.load(TEMP_FILE)
        pygame.mixer.music.play()
        
        print(f"✅ 播放成功 (耗时: {network_time:.2f}s)")
        
        # 等待播放结束，期间不阻塞主线程太久
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
        pygame.mixer.music.unload()
        
    except Exception as e:
        print(f"❌ 播放出错: {e}")
        print("可能是网络波动，请检查网络是否通畅。")

def is_contains_korean(text):
    """检测是否包含韩语字符"""
    if not text: return False
    return bool(re.search(r'[\uac00-\ud7a3]', text))

async def main():
    print("\n--- 🎧 韩语极速朗读助手 (云端加速版) ---")
    print("--- 💡 提示：按 Ctrl+C 复制韩语即可朗读 ---")
    
    # 预先初始化音频引擎，减少后续延迟
    try:
        pygame.mixer.init()
        print("--- 🔊 音频引擎已就绪 ---")
    except Exception as e:
        print(f"音频引擎初始化失败: {e}")

    last_text = pyperclip.paste()

    while True:
        try:
            current_text = pyperclip.paste()
            
            # 只有内容变了，且包含韩语才读
            if current_text != last_text and current_text:
                last_text = current_text
                
                if is_contains_korean(current_text):
                    await play_audio_fast(current_text)
            
            # 缩短检测间隔
            await asyncio.sleep(0.2)
            
        except KeyboardInterrupt:
            print("\n🛑 程序已停止")
            break
        except Exception as e:
            print(f"发生未知错误: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    # 清理旧的临时文件
    if os.path.exists(TEMP_FILE):
        try: os.remove(TEMP_FILE)
        except: pass
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass