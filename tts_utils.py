import os
import time
import pygame
import threading
from gtts import gTTS

# Initialize pygame mixer
pygame.mixer.init()

class TTSManager:
    @staticmethod
    def play_text(text, lang="vi", filename_prefix="temp"):
        """Play text as speech"""
        def play_audio():
            try:
                tts = gTTS(text=text, lang=lang)
                filename = f"{filename_prefix}.mp3"
                tts.save(filename)
                
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"Could not play audio: {e}")
        
        threading.Thread(target=play_audio, daemon=True).start()
    
    @staticmethod
    def play_greeting():
        """Play greeting message"""
        greeting_text = "Đây là hệ thống tìm sách trong thư viện, bạn muốn tìm sách nào?"
        TTSManager.play_text(greeting_text, filename_prefix="greeting")