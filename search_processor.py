"""
Módulo xử lý tìm kiếm sách thông minh
Kết hợp speech-to-text, text correction, SQL generation và database query
"""

import os
import sqlite3
import torch
import torchaudio
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import re
import logging
from config import (
    DATABASE_PATH, 
    WHISPER_MODEL_NAME, 
    WHISPER_MODEL_PATH,
    OPENAI_API_KEY,
    MAX_SEARCH_RESULTS,
    LOG_LEVEL
)

# Try to import OpenAI, with fallback
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OpenAI not available: {e}")
    OPENAI_AVAILABLE = False
    OpenAI = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchProcessor:
    """Lớp xử lý tìm kiếm sách thông minh"""
    
    def __init__(self, database_path=None, model_path=None, openai_api_key=None):
        """
        Khởi tạo SearchProcessor
        
        Args:
            database_path (str): Đường dẫn đến database SQLite
            model_path (str): Đường dẫn đến Whisper model
            openai_api_key (str): API key cho OpenAI
        """
        # Database connection
        self.database_path = database_path or DATABASE_PATH
        self.conn = None
        self.init_database()
        
        # Whisper model
        self.model_path = model_path or WHISPER_MODEL_PATH
        self.processor = None
        self.model = None
        self.init_whisper_model()
        
        # OpenAI client
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def init_database(self):
        """Khởi tạo kết nối database"""
        try:
            self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            logger.info(f"Đã kết nối database: {self.database_path}")
        except Exception as e:
            logger.error(f"Lỗi kết nối database: {e}")
            self.conn = None
    
    def init_whisper_model(self):
        """Khởi tạo Whisper model"""
        try:
            model_name = WHISPER_MODEL_NAME
            self.processor = WhisperProcessor.from_pretrained(model_name)
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = WhisperForConditionalGeneration.from_pretrained(self.model_path)
                logger.info(f"Đã tải model từ: {self.model_path}")
            else:
                self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
                logger.info(f"Đã tải model mặc định: {model_name}")
            
            self.model.generation_config.language = "vi"
            self.model.generation_config.task = "transcribe"
            self.model.generation_config.forced_decoder_ids = None
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Whisper model: {e}")
            self.processor = None
            self.model = None
    
    def load_audio(self, audio_path):
        """
        Load và preprocessing audio file
        
        Args:
            audio_path (str): Đường dẫn đến file audio
            
        Returns:
            torch.Tensor: Audio waveform đã được xử lý
        """
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                waveform = resampler(waveform)
            
            return waveform.squeeze()
        except Exception as e:
            logger.error(f"Lỗi load audio: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """
        Chuyển đổi audio thành text sử dụng Whisper
        
        Args:
            audio_path (str): Đường dẫn đến file audio
            
        Returns:
            str: Text đã được chuyển đổi
        """
        try:
            if not self.processor or not self.model:
                return "Lỗi: Model chưa được khởi tạo"
            
            # Load audio
            audio = self.load_audio(audio_path)
            if audio is None:
                return "Lỗi: Không thể load audio"
            
            # Process audio
            inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.model.generate(inputs["input_features"])
            
            # Decode
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            logger.info(f"Transcription: {transcription}")
            return transcription.strip()
            
        except Exception as e:
            logger.error(f"Lỗi transcribe audio: {e}")
            return f"Lỗi nhận diện: {str(e)}"
    
    def correct_text(self, text):
        """
        Sửa lỗi chính tả và ngữ pháp sử dụng OpenAI
        
        Args:
            text (str): Văn bản cần sửa
            
        Returns:
            str: Văn bản đã được sửa lỗi
        """
        try:
            if not text or text.strip() == "":
                return text
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Hãy sửa lỗi chính tả, ngữ pháp nếu có của từng từ trong văn bản tiếng Việt đầu vào mà người dùng cung cấp. Chỉ trả về văn bản đã được chỉnh sửa, không thêm dấu câu, không loại bỏ từ, nếu nhận diện từ đầu vào không hợp ngữ cảnh và không tìm được từ thay thế, giữ nguyên từ đó, và không thêm bất kỳ thông tin nào khác."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=150,
                temperature=0.1
            )
            
            corrected_text = response.choices[0].message.content.strip()
            logger.info(f"Text correction: '{text}' -> '{corrected_text}'")
            return corrected_text
            
        except Exception as e:
            logger.error(f"Lỗi correct text: {e}")
            return text  # Trả về text gốc nếu có lỗi
    
    def text_to_sql(self, text):
        """
        Chuyển đổi văn bản thành SQL query sử dụng OpenAI
        
        Args:
            text (str): Văn bản yêu cầu tìm kiếm
            
        Returns:
            str: SQL query
        """
        try:
            system_prompt = """Hãy chuyển văn bản tiếng Việt đầu vào mà người dùng cung cấp thành dạng SQL query để truy xuất dữ liệu của sách, với các thuộc tính của database:
            
            Tên bảng: books
            Các cột: ['id', 'title', 'author', 'publisher', 'publication_year', 'pages', 'dimensions', 'registration_number', 'price', 'storage_location', 'document_type', 'availability', 'keywords', 'subject', 'department', 'summary', 'url']
            
            Ví dụ về dữ liệu: [1, 'Quán văn 110 : chuyên đề văn học nghệ thuật', 'Nguyên Minh (ch.b)', 'Hội Nhà văn', 2024, '333 tr.', '21 cm.', 56245, 200000, '03 Quang Trung', 'Sách Tham Khảo', '10/10', 'quán văn', 'Văn học nghệ thuật', 'Bao gồm các bài viết...', 'https...']
            
            Lưu ý: 
            - Chỉ được phép trả lời SQL query
            - Sử dụng LIKE '%keyword%' cho tìm kiếm từ khóa
            - Sử dụng LOWER() để không phân biệt hoa thường
            - Giới hạn kết quả bằng LIMIT {MAX_SEARCH_RESULTS}"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            logger.info(f"Generated SQL: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Lỗi text to SQL: {e}")
            return "SELECT * FROM books LIMIT 10;"  # Default query
    
    def query_database(self, sql_query):
        """
        Thực hiện truy vấn database
        
        Args:
            sql_query (str): SQL query
            
        Returns:
            tuple: (success: bool, results: list hoặc error_message: str)
        """
        try:
            if not self.conn:
                return False, "Không có kết nối database"
            
            cursor = self.conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            if len(rows) == 0:
                return True, []
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                result_dict = dict(zip(column_names, row))
                results.append(result_dict)
            
            logger.info(f"Database query returned {len(results)} results")
            return True, results
            
        except Exception as e:
            error_msg = f"Lỗi truy vấn database: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def format_search_results(self, results):
        """
        Format kết quả tìm kiếm để hiển thị
        
        Args:
            results (list): Danh sách kết quả từ database
            
        Returns:
            str: Kết quả đã được format
        """
        if not results:
            return "❌ KHÔNG TÌM THẤY SÁCH PHÙ HỢP\n\nVui lòng thử lại với từ khóa khác."
        
        formatted_text = f"📚 TÌM THẤY {len(results)} CUỐN SÁCH:\n\n"
        
        for i, book in enumerate(results, 1):
            formatted_text += f"🔹 SÁCH {i}:\n"
            formatted_text += f"   📖 Tên: {book.get('title', 'N/A')}\n"
            formatted_text += f"   ✍️ Tác giả: {book.get('author', 'N/A')}\n"
            formatted_text += f"   🏢 NXB: {book.get('publisher', 'N/A')}\n"
            formatted_text += f"   📅 Năm: {book.get('publication_year', 'N/A')}\n"
            formatted_text += f"   📄 Trang: {book.get('pages', 'N/A')}\n"
            formatted_text += f"   💰 Giá: {book.get('price', 'N/A')} VNĐ\n"
            formatted_text += f"   📍 Vị trí: {book.get('storage_location', 'N/A')}\n"
            formatted_text += f"   🏷️ Loại: {book.get('document_type', 'N/A')}\n"
            formatted_text += f"   ✅ Tình trạng: {book.get('availability', 'N/A')}\n"
            
            if book.get('keywords'):
                formatted_text += f"   🔍 Từ khóa: {book.get('keywords')}\n"
            
            formatted_text += "\n" + "─" * 50 + "\n"
        
        return formatted_text
    
    def process_search_request(self, audio_path):
        """
        Xử lý toàn bộ request tìm kiếm từ audio
        
        Args:
            audio_path (str): Đường dẫn đến file audio
            
        Returns:
            tuple: (transcribed_text: str, formatted_results: str)
        """
        try:
            # Step 1: Transcribe audio
            transcribed_text = self.transcribe_audio(audio_path)
            if "Lỗi" in transcribed_text:
                return transcribed_text, "❌ Không thể xử lý audio"
            
            # Step 2: Correct text
            corrected_text = self.correct_text(transcribed_text)
            
            # Step 3: Convert to SQL
            sql_query = self.text_to_sql(corrected_text)
            
            # Step 4: Query database
            success, results = self.query_database(sql_query)
            
            if not success:
                return transcribed_text, f"❌ LỖI TÌM KIẾM:\n{results}"
            
            # Step 5: Format results
            formatted_results = self.format_search_results(results)
            
            return transcribed_text, formatted_results
            
        except Exception as e:
            error_msg = f"❌ LỖI XỬ LÝ: {str(e)}"
            logger.error(error_msg)
            return "Lỗi xử lý", error_msg
    
    def test_connection(self):
        """Test tất cả các kết nối"""
        status = {
            "database": False,
            "whisper": False,
            "openai": False
        }
        
        # Test database
        try:
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM books LIMIT 1")
                status["database"] = True
        except:
            pass
        
        # Test Whisper
        status["whisper"] = self.processor is not None and self.model is not None
        
        # Test OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            status["openai"] = True
        except:
            pass
        
        return status
    
    def close(self):
        """Đóng kết nối"""
        if self.conn:
            self.conn.close()
            logger.info("Đã đóng kết nối database")

# Example usage
if __name__ == "__main__":
    # Test the SearchProcessor
    processor = SearchProcessor()
    
    # Test connections
    status = processor.test_connection()
    print("Connection status:", status)
    
    # Test text processing
    test_text = "Tìm sách Python"
    corrected = processor.correct_text(test_text)
    sql = processor.text_to_sql(corrected)
    success, results = processor.query_database(sql)
    
    print(f"Original: {test_text}")
    print(f"Corrected: {corrected}")
    print(f"SQL: {sql}")
    print(f"Results: {len(results) if success else 'Error'}")
    
    processor.close()
