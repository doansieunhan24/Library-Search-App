# 📚 Library Search App - Ứng Dụng Tìm Kiếm Thư Viện Bằng Giọng Nói

Ứng dụng tìm kiếm sách thông minh sử dụng công nghệ Speech-to-Text, AI và Natural Language Processing.

## ✨ Tính năng chính

- 🎤 **Ghi âm giọng nói**: Ghi âm yêu cầu tìm kiếm bằng giọng nói
- 🔤 **Speech-to-Text**: Chuyển đổi giọng nói thành văn bản sử dụng Whisper AI
- ✏️ **Sửa lỗi văn bản**: Tự động sửa lỗi chính tả và ngữ pháp bằng OpenAI GPT
- 🔍 **Tìm kiếm thông minh**: Chuyển đổi yêu cầu tự nhiên thành SQL query
- 📊 **Hiển thị kết quả**: Giao diện đẹp và dễ sử dụng với PyQt6

## 🛠️ Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Windows 10/11 (hoặc macOS/Linux)
- Microphone
- Kết nối Internet (cho OpenAI API)

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Cấu hình
1. Mở file `config.py`
2. Cập nhật các thông tin sau:
   - `DATABASE_PATH`: Đường dẫn đến database SQLite
   - `OPENAI_API_KEY`: API key của OpenAI
   - `WHISPER_MODEL_PATH`: Đường dẫn đến model Whisper (tùy chọn)

## 🚀 Chạy ứng dụng

### Cách 1: Chạy trực tiếp
```bash
python run_app.py
```

### Cách 2: Chạy từ main_app
```bash
python main_app.py
```

## 📱 Hướng dẫn sử dụng

### Bước 1: Ghi âm
1. Nhấn nút "🎤 GHI ÂM"
2. Nói rõ ràng yêu cầu tìm kiếm sách
3. Nhấn "⏹️ DỪNG" khi hoàn thành

### Bước 2: Kiểm tra văn bản
1. Kiểm tra văn bản được nhận diện
2. Nhấn "✅ XÁC NHẬN" nếu đúng
3. Hoặc nhấn "🔄 GHI LẠI" để ghi lại

### Bước 3: Xem kết quả
1. Xem kết quả tìm kiếm
2. Nhấn "📋 COPY" để copy kết quả
3. Nhấn "🔄 TÌM KIẾM MỚI" để bắt đầu lại

## 🎯 Ví dụ tìm kiếm

- "Tìm sách Python"
- "Sách về Machine Learning"
- "Java programming"
- "Sách được xuất bản từ năm 2020"
- "Tác giả Nguyễn Văn A"

## 📁 Cấu trúc dự án

```
NewUI/
├── main_app.py              # Giao diện chính
├── search_processor.py      # Xử lý tìm kiếm AI
├── audio_workers.py         # Worker threads cho audio
├── config.py                # Cấu hình
├── run_app.py              # Launcher
├── requirements.txt         # Dependencies
├── pipeline.py             # Code gốc (reference)
├── data_fix                # Database SQLite
├── temp_audio/             # Thư mục audio tạm
├── logs/                   # Log files
└── README.md               # Tài liệu này
```

## 🔧 Các thành phần chính

### SearchProcessor
- **Transcription**: Whisper AI cho speech-to-text
- **Text Correction**: OpenAI GPT để sửa lỗi văn bản
- **SQL Generation**: Chuyển đổi yêu cầu tự nhiên thành SQL
- **Database Query**: Truy vấn SQLite database

### LibrarySearchApp (UI)
- **Stage 1**: Ghi âm giọng nói
- **Stage 2**: Xác nhận văn bản
- **Stage 3**: Hiển thị kết quả

### AudioWorker
- **Recording**: Ghi âm realtime
- **Processing**: Xử lý audio và tìm kiếm

## 🐛 Xử lý lỗi

### Lỗi thường gặp
1. **Không nhận diện được giọng nói**
   - Kiểm tra microphone
   - Nói rõ ràng hơn
   - Kiểm tra kết nối mạng

2. **Lỗi OpenAI API**
   - Kiểm tra API key
   - Kiểm tra credits
   - Kiểm tra kết nối mạng

3. **Lỗi database**
   - Kiểm tra đường dẫn database
   - Kiểm tra quyền truy cập file

### Log files
Kiểm tra file `logs/app.log` để xem chi tiết lỗi.

## 🔄 Cập nhật

### Cập nhật model Whisper
1. Download model mới
2. Cập nhật `WHISPER_MODEL_PATH` trong `config.py`

### Cập nhật database
1. Thay thế file database
2. Cập nhật `DATABASE_PATH` trong `config.py`

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log files
2. Đọc FAQ trong README
3. Tạo issue trên GitHub

---

**Phát triển bởi**: LOQ Team  
**Phiên bản**: 1.0.0  
**Ngày cập nhật**: 2025
