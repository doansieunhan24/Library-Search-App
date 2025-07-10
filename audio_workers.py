import os
import pyaudio
import wave
import speech_recognition as sr  
import threading
import time
from PyQt6.QtCore import QThread, pyqtSignal
from search_processor import SearchProcessor

class RecordingWorker(QThread):
    recording_finished = pyqtSignal(str)
    error = pyqtSignal(str)
    recording_time_update = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recording_time = 0
    
    def run(self):
        try:
            self.is_recording = True
            self.recording_time = 0
            
            # Audio recording parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            p = pyaudio.PyAudio()
            
            stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)
            
            frames = []
            
            # Start timer thread
            timer_thread = threading.Thread(target=self._update_timer)
            timer_thread.daemon = True
            timer_thread.start()
            
            # Record until stopped manually
            while self.is_recording:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    print(f"Recording chunk error: {e}")
                    continue
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save to temporary file
            temp_filename = "temp_recording.wav"
            wf = wave.open(temp_filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.recording_finished.emit(temp_filename)
            
        except Exception as e:
            self.error.emit(f"Lỗi khi ghi âm: {str(e)}")
    
    def _update_timer(self):
        """Cập nhật timer"""
        while self.is_recording:
            self.recording_time_update.emit(self.recording_time)
            time.sleep(1)
            self.recording_time += 1
    
    def stop_recording(self):
        self.is_recording = False

class AudioWorker(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    
    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        # Khởi tạo SearchProcessor
        self.search_processor = SearchProcessor()
    
    def run(self):
        try:
            # Sử dụng SearchProcessor để xử lý toàn bộ request
            transcribed_text, formatted_results = self.search_processor.process_search_request(self.audio_path)
            
            # Emit kết quả
            self.finished.emit(transcribed_text, formatted_results)
            
        except Exception as e:
            self.error.emit(f"Lỗi xử lý: {str(e)}")
        finally:
            # Đóng kết nối
            if hasattr(self, 'search_processor'):
                self.search_processor.close()
    
    def transcribe(self, audio_path):
        """Nhận diện giọng nói - fallback method"""
        if not audio_path:
            return "Không có file âm thanh"
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.5
        
        try:
            with sr.AudioFile(audio_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
            
            # Thử nhiều ngôn ngữ
            languages = [('vi-VN', 'Vietnamese'), ('en-US', 'English'), ('vi', 'Vietnamese (fallback)')]
            
            for lang_code, lang_name in languages:
                try:
                    text = recognizer.recognize_google(audio, language=lang_code)
                    if text and len(text.strip()) > 0:
                        print(f"[TRANSCRIBE] Success with {lang_name}: '{text}'")
                        return text
                except (sr.UnknownValueError, sr.RequestError):
                    continue
            
            return "Không nhận diện được giọng nói. Vui lòng thử lại với giọng rõ hơn."
            
        except Exception as e:
            return f"Lỗi xử lý âm thanh: {str(e)}"