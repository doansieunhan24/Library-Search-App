import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTextEdit, QLabel, QMessageBox, 
                            QProgressBar, QFrame, QGridLayout, QGroupBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QFont
from audio_workers import RecordingWorker, AudioWorker

class PipelineWorker(QThread):
    """Worker tối ưu để chạy pipeline tuần tự"""
    progress_update = pyqtSignal(str, int)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    
    def __init__(self, recorded_text):
        super().__init__()
        self.recorded_text = recorded_text
        self.is_running = True
    
    def run(self):
        processor = None
        try:
            print(f"🔄 Starting optimized pipeline: '{self.recorded_text}'")
            
            # Khởi tạo processor
            from search_processor import SearchProcessor
            processor = SearchProcessor()
            
            # Pipeline steps với error handling tốt hơn
            steps = [
                (20, "🔍 CHỈNH SỬA VĂN BẢN...", self._correct_text),
                (40, "⚙️ TẠO TRUY VẤN SQL...", self._generate_sql),
                (60, "✅ KIỂM TRA TRUY VẤN...", self._validate_sql),
                (80, "📚 TÌM KIẾM DATABASE...", self._query_database),
                (90, "📝 FORMAT KẾT QUẢ...", self._format_results)
            ]
            
            context = {'processor': processor, 'text': self.recorded_text}
            
            for progress, message, step_func in steps:
                if not self.is_running:
                    return
                    
                self.progress_update.emit(message, progress)
                context = step_func(context)
                
                if context.get('error'):
                    raise Exception(context['error'])
            
            # Hoàn thành
            self.progress_update.emit("✅ HOÀN THÀNH!", 100)
            self.finished.emit(
                context.get('corrected_text', self.recorded_text),
                context.get('formatted_results', 'Không có kết quả')
            )
            
        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            self.error.emit(str(e))
        finally:
            if processor:
                try:
                    processor.close()
                except:
                    pass
    
    def _correct_text(self, context):
        """Bước 1: Sửa văn bản"""
        try:
            corrected = context['processor'].correct_text(context['text'])
            context['corrected_text'] = corrected
            print(f"✓ Text: '{context['text']}' → '{corrected}'")
            return context
        except Exception as e:
            context['error'] = f"Lỗi chỉnh sửa văn bản: {str(e)}"
            return context
    
    def _generate_sql(self, context):
        """Bước 2: Tạo SQL"""
        try:
            sql = context['processor'].text_to_sql(context['corrected_text'])
            context['sql_query'] = sql
            print(f"✓ SQL: {sql}")
            return context
        except Exception as e:
            context['error'] = f"Lỗi tạo truy vấn: {str(e)}"
            return context
    
    def _validate_sql(self, context):
        """Bước 3: Kiểm tra SQL"""
        sql = context.get('sql_query', '')
        if not sql or not sql.strip():
            context['error'] = "Không thể tạo câu truy vấn từ văn bản"
        return context
    
    def _query_database(self, context):
        """Bước 4: Truy vấn database"""
        try:
            results = context['processor'].query_database(context['sql_query'])
            
            # Debug: In ra cấu trúc dữ liệu để hiểu rõ hơn
            print(f"🔍 Debug - Raw results type: {type(results)}")
            print(f"🔍 Debug - Raw results: {results}")
            
            # Xử lý kết quả - có thể là tuple (success, data) hoặc chỉ là data
            if isinstance(results, tuple) and len(results) == 2:
                success, data = results
                if success:
                    context['results'] = data
                    count = len(data) if isinstance(data, list) else 'N/A'
                    print(f"✓ Found: {count} results")
                else:
                    context['error'] = f"Lỗi truy vấn database: {data}"
            else:
                # Trường hợp trả về trực tiếp data
                context['results'] = results
                count = len(results) if isinstance(results, list) else 'N/A'
                print(f"✓ Found: {count} results")
            
            return context
        except Exception as e:
            context['error'] = f"Lỗi truy vấn database: {str(e)}"
            return context
    
    def _format_results(self, context):
        """Bước 5: Format kết quả"""
        try:
            formatted = self.format_results(context['results'])
            context['formatted_results'] = formatted
            return context
        except Exception as e:
            context['error'] = f"Lỗi format kết quả: {str(e)}"
            return context
    
    def format_results(self, results):
        """Format kết quả thành string đẹp và tối ưu"""
        # Xử lý trường hợp results là tuple (success, data)
        if isinstance(results, tuple) and len(results) == 2:
            success, data = results
            if not success:
                return f"❌ Lỗi truy vấn: {data}"
            results = data
        
        if isinstance(results, list) and results:
            formatted_results = ""
            
            for i, item in enumerate(results, 1):
                if isinstance(item, dict):
                    formatted_results += f"📖 Kết quả {i}:\n"
                    
                    # Format theo thứ tự ưu tiên
                    priority_fields = [
                        ('title', '📚 Tiêu đề'),
                        ('author', '✍️ Tác giả'),
                        ('category', '📂 Thể loại'),
                        ('description', '📝 Mô tả'),
                        ('price', '💰 Giá'),
                        ('publication_year', '📅 Năm xuất bản'),
                        ('year', '📅 Năm xuất bản'),
                        ('isbn', '🔢 ISBN')
                    ]
                    
                    for field, icon_label in priority_fields:
                        if field in item and item[field]:
                            value = item[field]
                            if field == 'price' and isinstance(value, (int, float)):
                                formatted_results += f"   {icon_label}: {value:,.0f} VND\n"
                            else:
                                formatted_results += f"   {icon_label}: {value}\n"
                    
                    # Thêm các field khác nếu có
                    displayed_fields = [field for field, _ in priority_fields]
                    for key, value in item.items():
                        if key not in displayed_fields and value:
                            formatted_results += f"   • {key}: {value}\n"
                    
                    formatted_results += "\n"
                else:
                    formatted_results += f"📖 Kết quả {i}: {str(item)}\n\n"
            
            return formatted_results
        elif isinstance(results, list) and not results:
            return "❌ Không tìm thấy kết quả nào phù hợp với yêu cầu tìm kiếm.\n\n💡 Gợi ý:\n• Thử từ khóa khác\n• Kiểm tra chính tả\n• Sử dụng từ khóa đơn giản hơn"
        else:
            return f"📄 Kết quả: {str(results)}"
    
    def stop(self):
        """Dừng pipeline một cách an toàn"""
        self.is_running = False
        self.quit()
        self.wait()

class LibrarySearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.temp_recording = None
        self.recorded_text = ""
        self.recording_time = 0
        self.current_stage = 1
        
        # Worker instances
        self.recording_worker = None
        self.transcription_worker = None
        self.pipeline_worker = None
        
        # Timer for recording
        self.recording_timer_obj = QTimer()
        self.recording_timer_obj.timeout.connect(self.update_recording_time_tick)
        self.recording_seconds = 0
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("📚 Tìm Kiếm Thư Viện Bằng Giọng Nói")
        self.setGeometry(200, 100, 800, 600)
        self.setFixedSize(800, 600)
        
        # Style chung
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                border: 2px solid #2c3e50;
                border-radius: 10px;
                background-color: #ffffff;
                margin: 10px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        
        # Ô lớn phía trên - Hướng dẫn/Hiển thị nội dung
        self.create_main_display_box(main_layout)
        
        # Layout cho 2 ô nhỏ phía dưới
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Ô nhỏ trái - Nút chính (Ghi âm/Xác nhận/Tìm kiếm mới)
        self.create_main_action_box(bottom_layout)
        
        # Ô nhỏ phải - Nút phụ (Dừng/Ghi lại)
        self.create_secondary_action_box(bottom_layout)
        
        main_layout.addLayout(bottom_layout)
        
        # Progress bar và status (ẩn ban đầu)
        self.create_status_section(main_layout)
        
        # Khởi tạo stage 1
        self.update_ui_for_stage(1)
    
    def create_main_display_box(self, layout):
        """Tạo ô lớn phía trên - Hiển thị nội dung chính"""
        self.main_display_frame = QFrame()
        self.main_display_frame.setMinimumHeight(300)
        self.main_display_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #3498db;
                border-radius: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e8f4fd, stop:1 #d4edda);
                margin: 5px;
            }
        """)
        
        self.main_display_layout = QVBoxLayout(self.main_display_frame)
        self.main_display_layout.setContentsMargins(30, 30, 30, 30)
        self.main_display_layout.setSpacing(20)
        
        # Title - luôn hiển thị
        self.title_label = QLabel("📚 HỆ THỐNG TÌM KIẾM THÔNG MINH")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        
        # Content area - thay đổi theo stage
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        # Stage 1: Instruction
        self.instruction_label = QLabel("HÃY NÓI RÕ RÀNG YÊU CẦU TÌM KIẾM SÁCH CỦA BẠN\n\n🎹 Phím tắt: SPACE để ghi âm, ESC để dừng, ENTER để xác nhận")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 15px;
            }
        """)
        
        self.examples_label = QLabel("💡 Ví dụ: \"Tìm sách Python\", \"Sách giá 50.000\", \"Java programming năm 2023\"")
        self.examples_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.examples_label.setWordWrap(True)
        self.examples_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                font-style: italic;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        
        # Stage 2: Text verification
        self.verification_label = QLabel("✅ KIỂM TRA VĂN BẢN NHẬN DIỆN")
        self.verification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verification_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        self.verification_label.setVisible(False)
        
        self.transcription_display = QTextEdit()
        self.transcription_display.setMinimumHeight(150)
        self.transcription_display.setReadOnly(True)
        self.transcription_display.setPlaceholderText("Văn bản nhận diện sẽ hiển thị ở đây...")
        self.transcription_display.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                color: #2c3e50;
                line-height: 1.5;
            }
        """)
        self.transcription_display.setVisible(False)
        
        # Stage 3: Results
        self.results_label = QLabel("📚 KẾT QUẢ TÌM KIẾM")
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        self.results_label.setVisible(False)
        
        self.result_output = QTextEdit()
        self.result_output.setMinimumHeight(200)
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Kết quả tìm kiếm sách sẽ hiển thị ở đây...")
        self.result_output.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 2px solid #2ecc71;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                color: #2c3e50;
                line-height: 1.5;
            }
        """)
        self.result_output.setVisible(False)
        
        # Add all content to layout
        self.content_layout.addWidget(self.instruction_label)
        self.content_layout.addWidget(self.examples_label)
        self.content_layout.addWidget(self.verification_label)
        self.content_layout.addWidget(self.transcription_display)
        self.content_layout.addWidget(self.results_label)
        self.content_layout.addWidget(self.result_output)
        self.content_layout.addStretch()
        
        self.main_display_layout.addWidget(self.title_label)
        self.main_display_layout.addWidget(self.content_widget)
        
        layout.addWidget(self.main_display_frame, 2)  # Chiếm 2/3 không gian
    
    def create_main_action_box(self, layout):
        """Tạo ô nhỏ trái - Nút hành động chính"""
        self.main_action_frame = QFrame()
        self.main_action_frame.setMinimumHeight(120)
        self.main_action_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #27ae60;
                border-radius: 10px;
                background-color: #ffffff;
                margin: 5px;
            }
        """)
        
        main_action_layout = QVBoxLayout(self.main_action_frame)
        main_action_layout.setContentsMargins(20, 20, 20, 20)
        main_action_layout.setSpacing(15)
        
        # Main action button - thay đổi theo stage
        self.main_action_button = QPushButton("🎤 GHI ÂM")
        self.main_action_button.clicked.connect(self.main_action_clicked)
        self.main_action_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px 20px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
            }
            QPushButton:pressed {
                background: #1e8449;
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        main_action_layout.addWidget(self.main_action_button)
        layout.addWidget(self.main_action_frame, 1)
    
    def create_secondary_action_box(self, layout):
        """Tạo ô nhỏ phải - Nút hành động phụ"""
        self.secondary_action_frame = QFrame()
        self.secondary_action_frame.setMinimumHeight(120)
        self.secondary_action_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #e74c3c;
                border-radius: 10px;
                background-color: #ffffff;
                margin: 5px;
            }
        """)
        
        secondary_action_layout = QVBoxLayout(self.secondary_action_frame)
        secondary_action_layout.setContentsMargins(20, 20, 20, 20)
        secondary_action_layout.setSpacing(15)
        
        # Secondary action button - thay đổi theo stage
        self.secondary_action_button = QPushButton("⏹️ DỪNG")
        self.secondary_action_button.clicked.connect(self.secondary_action_clicked)
        self.secondary_action_button.setEnabled(False)
        self.secondary_action_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px 20px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }
            QPushButton:pressed {
                background: #922b21;
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        secondary_action_layout.addWidget(self.secondary_action_button)
        layout.addWidget(self.secondary_action_frame, 1)
    
    def create_status_section(self, layout):
        """Tạo phần status và progress bar"""
        self.status_frame = QFrame()
        self.status_frame.setVisible(False)
        self.status_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: #ffffff;
                margin: 5px;
            }
        """)
        
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(20, 15, 20, 15)
        status_layout.setSpacing(10)
        
        # Status label
        self.recording_status = QLabel("🟢 Sẵn sàng ghi âm")
        self.recording_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_status.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)
        
        # Timer
        self.recording_timer = QLabel("⏱️ 00:00")
        self.recording_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_timer.setVisible(False)
        self.recording_timer.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                background: transparent;
                border: none;
                padding: 5px;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3498db;
                border-radius: 5px;
                background: #ecf0f1;
                text-align: center;
                font-size: 12px;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 4px;
            }
        """)
        
        status_layout.addWidget(self.recording_status)
        status_layout.addWidget(self.recording_timer)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.status_frame)
    
    def update_ui_for_stage(self, stage):
        """Cập nhật UI theo stage"""
        self.current_stage = stage
        
        # Ẩn tất cả content
        self.instruction_label.setVisible(False)
        self.examples_label.setVisible(False)
        self.verification_label.setVisible(False)
        self.transcription_display.setVisible(False)
        self.results_label.setVisible(False)
        self.result_output.setVisible(False)
        
        if stage == 1:  # Stage ghi âm
            self.instruction_label.setVisible(True)
            self.examples_label.setVisible(True)
            self.main_action_button.setText("🎤 GHI ÂM")
            self.main_action_button.setEnabled(True)
            self.secondary_action_button.setText("⏹️ DỪNG")
            self.secondary_action_button.setEnabled(False)
            self.status_frame.setVisible(False)
            
        elif stage == 2:  # Stage kiểm tra văn bản
            self.verification_label.setVisible(True)
            self.transcription_display.setVisible(True)
            self.main_action_button.setText("✅ XÁC NHẬN")
            self.main_action_button.setEnabled(True)
            self.secondary_action_button.setText("🔄 GHI LẠI")
            self.secondary_action_button.setEnabled(True)
            self.status_frame.setVisible(False)
            
        elif stage == 3:  # Stage kết quả
            self.results_label.setVisible(True)
            self.result_output.setVisible(True)
            self.main_action_button.setText("🔄 TÌM KIẾM MỚI")
            self.main_action_button.setEnabled(True)
            self.secondary_action_button.setText("📋 COPY")
            self.secondary_action_button.setEnabled(True)
            self.status_frame.setVisible(False)
    
    def main_action_clicked(self):
        """Xử lý click nút chính"""
        if self.current_stage == 1:
            self.start_recording()
        elif self.current_stage == 2:
            self.confirm_and_search()
        elif self.current_stage == 3:
            self.start_new_search()
    
    def secondary_action_clicked(self):
        """Xử lý click nút phụ"""
        if self.current_stage == 1:
            self.stop_recording()
        elif self.current_stage == 2:
            self.retry_recording()
        elif self.current_stage == 3:
            self.copy_results()
    
    def start_recording(self):
        """Bắt đầu ghi âm"""
        # Dừng tất cả workers trước khi bắt đầu
        self.stop_all_workers()
        
        self.main_action_button.setEnabled(False)
        self.secondary_action_button.setEnabled(True)
        self.recording_status.setText("🔴 ĐANG GHI ÂM - Hãy nói rõ yêu cầu của bạn...")
        self.recording_timer.setVisible(True)
        self.recording_timer.setText("⏱️ 00:00")
        self.status_frame.setVisible(True)
        
        # Reset timer
        self.recording_seconds = 0
        self.recording_timer_obj.start(1000)
        
        # Start recording worker
        self.recording_worker = RecordingWorker()
        self.recording_worker.recording_finished.connect(self.on_recording_finished)
        self.recording_worker.error.connect(self.on_recording_error)
        self.recording_worker.start()
    
    def stop_recording(self):
        """Dừng ghi âm"""
        if self.recording_worker and self.recording_worker.isRunning():
            self.recording_worker.stop_recording()
        
        self.recording_timer_obj.stop()
        self.main_action_button.setEnabled(True)
        self.secondary_action_button.setEnabled(False)
        self.recording_status.setText("⏳ ĐANG XỬ LÝ ÂM THANH - Vui lòng đợi...")
        self.recording_timer.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def update_recording_time_tick(self):
        """Cập nhật thời gian ghi âm mỗi giây"""
        self.recording_seconds += 1
        minutes = self.recording_seconds // 60
        secs = self.recording_seconds % 60
        self.recording_timer.setText(f"⏱️ {minutes:02d}:{secs:02d}")
    
    def stop_all_workers(self):
        """Dừng tất cả các worker đang chạy một cách an toàn"""
        workers = [
            ('recording_worker', lambda w: w.stop_recording()),
            ('transcription_worker', lambda w: w.quit()),
            ('pipeline_worker', lambda w: w.stop())
        ]
        
        for worker_name, stop_func in workers:
            if hasattr(self, worker_name):
                worker = getattr(self, worker_name)
                if worker and worker.isRunning():
                    try:
                        stop_func(worker)
                        worker.wait(1000)  # Wait max 1 second
                    except:
                        worker.terminate()  # Force terminate if needed
        
        self.recording_timer_obj.stop()
    
    def update_recording_time(self, seconds):
        """Cập nhật thời gian ghi âm"""
        minutes = seconds // 60
        secs = seconds % 60
        self.recording_timer.setText(f"⏱️ {minutes:02d}:{secs:02d}")
    
    def on_recording_finished(self, audio_file):
        """Xử lý khi ghi âm hoàn thành"""
        self.temp_recording = audio_file
        self.recording_timer_obj.stop()
        
        print(f"🎤 Recording completed: {audio_file}")
        
        # Bắt đầu transcription
        self.transcription_worker = AudioWorker(audio_file)
        self.transcription_worker.finished.connect(self.on_transcription_finished)
        self.transcription_worker.error.connect(self.on_transcription_error)
        self.transcription_worker.start()
    
    def on_recording_error(self, error_msg):
        """Xử lý lỗi ghi âm"""
        self.stop_all_workers()
        QMessageBox.critical(self, "Lỗi ghi âm", error_msg)
        self.update_ui_for_stage(1)
    
    def on_transcription_finished(self, text, results):
        """Xử lý khi nhận diện hoàn thành"""
        self.progress_bar.setVisible(False)
        
        print(f"🎤 Transcription: '{text}'")
        
        if "Không nhận diện" in text or "Lỗi" in text or len(text.strip()) < 3:
            QMessageBox.warning(self, "Không nhận diện được", 
                              "Không thể nhận diện giọng nói rõ ràng.\nVui lòng thử lại và nói to, rõ hơn.")
            self.update_ui_for_stage(1)
        else:
            self.recorded_text = text
            self.transcription_display.setText(text)
            self.update_ui_for_stage(2)
    
    def on_transcription_error(self, error_msg):
        """Xử lý lỗi nhận diện"""
        self.stop_all_workers()
        QMessageBox.critical(self, "Lỗi", error_msg)
        self.update_ui_for_stage(1)
    
    def confirm_and_search(self):
        """Xác nhận văn bản và bắt đầu pipeline tìm kiếm"""
        if not self.recorded_text:
            return
        
        # Dừng tất cả workers trước khi bắt đầu pipeline
        self.stop_all_workers()
        
        self.update_ui_for_stage(3)
        self.result_output.setText("🔍 ĐANG KHỞI ĐỘNG PIPELINE TÌM KIẾM...\n\nVui lòng đợi...")
        
        # Hiển thị progress bar
        self.status_frame.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.recording_timer.setVisible(False)
        
        # Vô hiệu hóa buttons
        self.main_action_button.setEnabled(False)
        self.secondary_action_button.setEnabled(False)
        
        # Bắt đầu pipeline worker
        self.pipeline_worker = PipelineWorker(self.recorded_text)
        self.pipeline_worker.progress_update.connect(self.on_pipeline_progress)
        self.pipeline_worker.finished.connect(self.on_pipeline_finished)
        self.pipeline_worker.error.connect(self.on_pipeline_error)
        self.pipeline_worker.start()
    
    def on_pipeline_progress(self, message, percentage):
        """Cập nhật tiến trình pipeline"""
        self.recording_status.setText(message)
        self.progress_bar.setValue(percentage)
        
        # Cập nhật kết quả hiển thị
        if percentage < 100:
            self.result_output.setText(f"{message}\n\n🔄 Tiến trình: {percentage}%")
    
    def on_pipeline_finished(self, corrected_text, results):
        """Hoàn thành pipeline"""
        self.progress_bar.setVisible(False)
        self.status_frame.setVisible(False)
        
        # Kích hoạt lại buttons
        self.main_action_button.setEnabled(True)
        self.secondary_action_button.setEnabled(True)
        
        # Hiển thị kết quả với format tối ưu
        result_text = f"🎯 VĂN BẢN NHẬN DIỆN:\n   \"{self.recorded_text}\"\n\n"
        
        if corrected_text != self.recorded_text:
            result_text += f"✅ VĂN BẢN ĐÃ CHỈNH SỬA:\n   \"{corrected_text}\"\n\n"
        
        result_text += f"📚 KẾT QUẢ TÌM KIẾM:\n\n{results}"
        
        self.result_output.setText(result_text)
        
        # Log tối ưu
        print(f"✅ Pipeline completed successfully")
    
    def on_pipeline_error(self, error_msg):
        """Xử lý lỗi pipeline"""
        self.progress_bar.setVisible(False)
        self.status_frame.setVisible(False)
        
        # Kích hoạt lại buttons
        self.main_action_button.setEnabled(True)
        self.secondary_action_button.setEnabled(True)
        
        print(f"❌ Pipeline error: {error_msg}")
        
        # Phân loại lỗi và hiển thị thông báo thân thiện
        if "database" in error_msg.lower() or "kết nối" in error_msg.lower():
            self.result_output.setText(
                "❌ LỖI CƠ SỞ DỮ LIỆU\n\n"
                "Không thể kết nối hoặc truy vấn database.\n"
                "Vui lòng kiểm tra kết nối database.\n\n"
                "💡 Thử lại sau hoặc liên hệ hỗ trợ kỹ thuật."
            )
            QMessageBox.critical(self, "Lỗi Database", 
                               "Lỗi kết nối database. Vui lòng thử lại!")
            
        elif "truy vấn" in error_msg.lower() or "sql" in error_msg.lower():
            self.result_output.setText(
                "❌ LỖI TẠO TRUY VẤN\n\n"
                "Không thể hiểu yêu cầu tìm kiếm của bạn.\n"
                "Vui lòng nói rõ ràng hơn.\n\n"
                "💡 Ví dụ:\n"
                "• 'Tìm sách Python'\n"
                "• 'Sách giá dưới 100.000'\n"
                "• 'Sách về AI năm 2023'"
            )
            
        elif "chỉnh sửa" in error_msg.lower() or "correct" in error_msg.lower():
            self.result_output.setText(
                "❌ LỖI XỬ LÝ VĂN BẢN\n\n"
                "Không thể xử lý văn bản nhận diện.\n"
                "Văn bản có thể quá ngắn hoặc không rõ ràng.\n\n"
                "💡 Vui lòng thử lại với câu dài hơn và rõ ràng hơn."
            )
        else:
            self.result_output.setText(
                f"❌ LỖI HỆ THỐNG\n\n"
                f"Có lỗi xảy ra trong quá trình xử lý:\n"
                f"{error_msg}\n\n"
                f"💡 Vui lòng thử lại hoặc liên hệ hỗ trợ."
            )
    
    def retry_recording(self):
        """Quay lại ghi âm"""
        self.stop_all_workers()
        self.cleanup_temp_files()
        self.update_ui_for_stage(1)
    
    def start_new_search(self):
        """Bắt đầu tìm kiếm mới"""
        self.stop_all_workers()
        self.cleanup_temp_files()
        self.update_ui_for_stage(1)
    
    def cleanup_temp_files(self):
        """Dọn dẹp các file tạm"""
        self.transcription_display.clear()
        self.result_output.clear()
        self.recorded_text = ""
        
        if self.temp_recording and os.path.exists(self.temp_recording):
            try:
                os.remove(self.temp_recording)
            except:
                pass
            self.temp_recording = None
    
    def copy_results(self):
        """Copy kết quả"""
        if self.result_output.toPlainText():
            QApplication.clipboard().setText(self.result_output.toPlainText())
            QMessageBox.information(self, "Đã copy", "Kết quả đã được copy vào clipboard!")
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        self.stop_all_workers()
        self.cleanup_temp_files()
        event.accept()
    
    def showEvent(self, event):
        """Optimize khi hiển thị window"""
        super().showEvent(event)
        # Pre-load imports để tăng tốc pipeline
        try:
            import search_processor
            print("✓ Pre-loaded search_processor")
        except:
            pass
    
    def keyPressEvent(self, event):
        """Keyboard shortcuts"""
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Space and self.current_stage == 1:
            self.start_recording()
        elif event.key() == Qt.Key.Key_Escape:
            self.stop_all_workers()
        elif event.key() == Qt.Key.Key_Return and self.current_stage == 2:
            self.confirm_and_search()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LibrarySearchApp()
    window.show()
    sys.exit(app.exec())