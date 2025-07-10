from better_profanity import profanity
from langdetect import detect, detect_langs
from googletrans import Translator
from textblob import TextBlob  # Thay đổi từ pyspellchecker sang textblob
import re

class SmartTextFilter:
    """Bộ lọc văn bản thông minh sử dụng TextBlob"""
    
    def __init__(self):
        # Khởi tạo bộ lọc từ tục tĩu
        profanity.load_censor_words()
        
        # Thêm từ tục tĩu tiếng Việt
        vietnamese_bad_words = [
            'đồ chó', 'thằng chó', 'con chó', 'đồ khốn', 'thằng khốn',
            'đồ ngu', 'thằng ngu', 'đồ đần', 'đồ ngốc', 'con điên',
            'đồ điên', 'thằng điên', 'cút', 'mẹ kiếp', 'con mẹ'
        ]
        profanity.add_censor_words(vietnamese_bad_words)
        
        # Khởi tạo translator
        self.translator = Translator()
        
        # Kiểm tra TextBlob
        try:
            # Test TextBlob
            test_blob = TextBlob("test")
            test_blob.correct()
            print("[SMART FILTER] TextBlob initialized successfully ✓")
            self.textblob_available = True
        except Exception as e:
            print(f"[SMART FILTER] TextBlob error: {e}")
            self.textblob_available = False
        
        # Từ điển sửa lỗi nhận diện giọng nói (thêm trước khi spell check)
        self.speech_corrections = {
            # "sách" bị nhận diện sai
            'sex': 'sách',
            'sexy': 'sách', 
            'six': 'sách',
            'sick': 'sách',
            'seek': 'sách',
            'sock': 'sách',
            'suck': 'sách',
            'such': 'sách',
            'sake': 'sách',
            'sack': 'sách',
            'stack': 'sách',
            'shark': 'sách',
            'shack': 'sách',
            
            # Các từ khác
            'tim': 'tìm',
            'team': 'tìm',
            'tem': 'tìm',
            'tom': 'tìm',
            'tam': 'tìm',
            
            'muon': 'muốn',
            'mun': 'muốn',
            'mon': 'muốn',
            'man': 'muốn',
            
            'can': 'cần',
            'ken': 'cần',
            'gen': 'cần',
        }
        
        # Từ điển ánh xạ chính xác cho domain cụ thể (thư viện)
        self.domain_mapping = {
            # Chỉ những từ thực sự cần thiết và chắc chắn
            'book': 'sách',
            'books': 'sách',
            'find': 'tìm',
            'want': 'muốn',
            'need': 'cần',
            'about': 'về',
            'learn': 'học',
            'study': 'học tập',
            'read': 'đọc',
        }
        
        # Từ khóa kỹ thuật (GIỮ NGUYÊN - KHÔNG spell check)
        self.tech_keywords = {
            'python', 'java', 'javascript', 'html', 'css', 'react', 'nodejs',
            'machine learning', 'ai', 'data science', 'database', 'sql',
            'programming', 'algorithm', 'web development', 'mobile app',
            'search', 'engine', 'optimization', 'seo', 'google', 'bing',
            'mongodb', 'mysql', 'postgresql', 'firebase', 'aws', 'azure',
            'github', 'docker', 'kubernetes', 'tensorflow', 'pytorch'
        }
        
        # Patterns để phát hiện ngữ cảnh thư viện
        self.library_patterns = [
            r'\b(find|search|look for)\s+(book|books)\b',
            r'\b(book|books)\s+(about|on|for)\b',
            r'\b(library|thư viện)\b',
            r'\b(want|need)\s+.*(book|learn|study)\b',
            r'\b(borrow|mượn|thuê)\b',
        ]
        
        # Từ điển spell check thủ công (fallback)
        self.manual_corrections = {
            'programing': 'programming',
            'developement': 'development',
            'langauge': 'language',
            'machien': 'machine',
            'lern': 'learn',
            'studie': 'study',
            'boks': 'books',
            'boook': 'book',
            'databse': 'database',
            'algoritm': 'algorithm',
            'scince': 'science',
            'enginer': 'engineer',
            'sofware': 'software',
            'compuer': 'computer',
            'beginer': 'beginner',
            'advaced': 'advanced',
            'practic': 'practice',
            'tutoral': 'tutorial',
            'refernce': 'reference',
            'libary': 'library',
            'informaton': 'information',
            'techology': 'technology',
        }
    
    def clean_text(self, text):
        """Làm sạch văn bản một cách thông minh"""
        if not text:
            return text
        
        original_text = text
        print(f"[SMART FILTER] Input: '{original_text}'")
        
        # Bước 1: Sửa lỗi nhận diện giọng nói trước
        cleaned_text = self._fix_speech_recognition(text)
        print(f"[SMART FILTER] After speech fix: '{cleaned_text}'")
        
        # Bước 2: Phát hiện ngôn ngữ
        detected_lang = self._detect_language(cleaned_text)
        print(f"[SMART FILTER] Detected language: {detected_lang}")
        
        # Bước 3: Lọc từ tục tĩu
        cleaned_text = self._filter_profanity(cleaned_text)
        print(f"[SMART FILTER] After profanity filter: '{cleaned_text}'")
        
        # Bước 4: Sửa lỗi chính tả nếu là tiếng Anh
        if detected_lang == 'en':
            cleaned_text = self._spell_check_with_textblob(cleaned_text)
            print(f"[SMART FILTER] After spell check: '{cleaned_text}'")
        
        # Bước 5: Ánh xạ domain-specific (chỉ khi chắc chắn)
        if detected_lang == 'en' and self._is_library_context(cleaned_text):
            cleaned_text = self._domain_mapping_func(cleaned_text)
            print(f"[SMART FILTER] After domain mapping: '{cleaned_text}'")
        
        # Bước 6: Chuẩn hóa cuối
        final_text = self._normalize(cleaned_text)
        print(f"[SMART FILTER] Final result: '{final_text}'")
        
        return final_text
    
    def _fix_speech_recognition(self, text):
        """Sửa lỗi nhận diện giọng nói phổ biến"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            word_lower = word.lower().strip('.,!?')
            
            # Sửa lỗi nhận diện giọng nói
            if word_lower in self.speech_corrections:
                corrected_words.append(self.speech_corrections[word_lower])
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _detect_language(self, text):
        """Phát hiện ngôn ngữ"""
        try:
            return detect(text)
        except:
            # Fallback: kiểm tra theo từ khóa
            text_lower = text.lower()
            english_indicators = ['the', 'and', 'or', 'is', 'are', 'book', 'search', 'find', 'want', 'need']
            english_count = sum(1 for word in english_indicators if f' {word} ' in f' {text_lower} ')
            return 'en' if english_count >= 1 else 'vi'
    
    def _filter_profanity(self, text):
        """Lọc từ tục tĩu bằng thư viện"""
        try:
            return profanity.censor(text, '***')
        except Exception as e:
            print(f"[SMART FILTER] Profanity filter error: {e}")
            return text
    
    def _spell_check_with_textblob(self, text):
        """Sửa lỗi chính tả cho tiếng Anh bằng TextBlob"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Giữ nguyên từ kỹ thuật
            word_lower = word.lower().strip('.,!?')
            if word_lower in self.tech_keywords:
                corrected_words.append(word)
                continue
            
            # Giữ nguyên từ ngắn (có thể là viết tắt)
            if len(word_lower) <= 2:
                corrected_words.append(word)
                continue
            
            # Kiểm tra manual corrections trước
            if word_lower in self.manual_corrections:
                corrected = self.manual_corrections[word_lower]
                corrected_words.append(self._preserve_case(word, corrected))
                print(f"[MANUAL SPELL] '{word}' -> '{corrected}'")
                continue
            
            # Sử dụng TextBlob
            if self.textblob_available:
                try:
                    # Tách dấu câu
                    clean_word = re.sub(r'[^\w]', '', word)
                    if len(clean_word) > 2:  # Chỉ spell check từ dài hơn 2 ký tự
                        blob = TextBlob(clean_word.lower())
                        corrected = str(blob.correct())
                        
                        if corrected != clean_word.lower() and corrected.isalpha():
                            # Giữ nguyên case gốc và thêm lại dấu câu
                            final_corrected = self._preserve_case(word, corrected)
                            
                            # Thêm lại dấu câu nếu có
                            if word.endswith(('.', ',', '!', '?', ':', ';')):
                                final_corrected += word[-1]
                            
                            corrected_words.append(final_corrected)
                            print(f"[TEXTBLOB] '{word}' -> '{final_corrected}'")
                        else:
                            corrected_words.append(word)
                    else:
                        corrected_words.append(word)
                        
                except Exception as e:
                    print(f"[TEXTBLOB] Error with '{word}': {e}")
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _preserve_case(self, original, corrected):
        """Giữ nguyên case của từ gốc"""
        if original.isupper():
            return corrected.upper()
        elif original.istitle():
            return corrected.title()
        elif original.islower():
            return corrected.lower()
        return corrected
    
    def _domain_mapping_func(self, text):
        """Ánh xạ từ theo domain thư viện"""
        words = text.split()
        mapped_words = []
        
        for word in words:
            word_lower = word.lower().strip('.,!?')
            
            # Giữ nguyên từ kỹ thuật
            if word_lower in self.tech_keywords:
                mapped_words.append(word)
            # Ánh xạ từ cơ bản
            elif word_lower in self.domain_mapping:
                mapped_words.append(self.domain_mapping[word_lower])
            else:
                mapped_words.append(word)
        
        return ' '.join(mapped_words)
    
    def _is_library_context(self, text):
        """Kiểm tra có phải ngữ cảnh thư viện không"""
        text_lower = text.lower()
        
        # Kiểm tra các pattern thư viện
        for pattern in self.library_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Kiểm tra từ khóa thư viện
        library_keywords = ['book', 'library', 'sách', 'thư viện', 'tìm', 'find']
        book_context_count = sum(1 for keyword in library_keywords if keyword in text_lower)
        
        return book_context_count >= 2  # Cần ít nhất 2 từ khóa để chắc chắn
    
    def _normalize(self, text):
        """Chuẩn hóa văn bản cuối"""
        # Xóa khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Viết hoa chữ cái đầu
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        return text
    
    def translate_to_vietnamese(self, text):
        """Dịch sang tiếng Việt (khi cần thiết)"""
        try:
            if self._detect_language(text) == 'en':
                result = self.translator.translate(text, src='en', dest='vi')
                return result.text
        except Exception as e:
            print(f"[TRANSLATOR] Error: {e}")
            pass
        return text
    
    def is_appropriate(self, text):
        """Kiểm tra văn bản có phù hợp không"""
        return '***' not in self._filter_profanity(text)
    
    def get_spelling_suggestions(self, word):
        """Lấy gợi ý spell check cho một từ"""
        if self.textblob_available:
            try:
                blob = TextBlob(word.lower())
                corrected = str(blob.correct())
                if corrected != word.lower():
                    return [corrected]
            except:
                pass
        
        # Fallback với manual corrections
        word_lower = word.lower()
        if word_lower in self.manual_corrections:
            return [self.manual_corrections[word_lower]]
        
        return []

# Hàm tiện ích
def clean_speech_text(text):
    """Hàm tiện ích để làm sạch văn bản"""
    filter_instance = SmartTextFilter()
    return filter_instance.clean_text(text)

# Test
if __name__ == "__main__":
    test_cases = [
        "sex python",                       # Sửa speech -> spell check -> context
        "find books about java",            # Context mapping
        "python programing",                # Spell check: programing -> programming
        "search engine optimization",       # Không ánh xạ (không phải ngữ cảnh sách)
        "I want to lern machine learning",  # Spell check: lern -> learn
        "tim sex about machine learning",   # Speech fix + context
        "book about python developement",   # Spell check: developement -> development
        "sách về lập trình",               # Tiếng Việt - giữ nguyên
        "find boks on java programming",   # Spell check: boks -> books + context
        "I need informaton about databse", # Multiple spell errors
        "python tutoral for beginer",      # Multiple corrections
    ]
    
    filter_obj = SmartTextFilter()
    
    print("=== TEST SMART FILTER WITH TEXTBLOB ===")
    print(f"TextBlob available: {filter_obj.textblob_available}")
    print()
    
    for test in test_cases:
        print(f"{'='*70}")
        print(f"Input: '{test}'")
        result = filter_obj.clean_text(test)
        print(f"Output: '{result}'")
        print(f"Language: {filter_obj._detect_language(test)}")
        print(f"Appropriate: {filter_obj.is_appropriate(test)}")
        print()