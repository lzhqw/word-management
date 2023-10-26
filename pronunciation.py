from gtts import gTTS
import pygame
import os
import threading
import queue

# 初始化 pygame 的 mixer
pygame.mixer.init()

# 创建一个队列来管理播放请求
play_queue = queue.Queue()


def audio_player():
    while True:
        filepath = play_queue.get()
        if filepath is None:
            break  # 结束线程

        # 停止当前音频（如果有）
        pygame.mixer.music.stop()

        # 加载音频文件
        pygame.mixer.music.load(filepath)

        # 播放音频
        pygame.mixer.music.play()

        # 等待音频播放完成
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(100)


def pronounce_word(word):
    filepath = f'temp/{word}.mp3'
    if not os.path.exists(filepath):
        tts = gTTS(text=word, lang='en')
        tts.save(filepath)

    # 将音频文件路径添加到播放队列
    play_queue.put(filepath)


def quit_prononciation():
    play_queue.put(None)
    pass


audio_thread = threading.Thread(target=audio_player)
audio_thread.start()
