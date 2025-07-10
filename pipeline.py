import random
import numpy as np
import torch
from openai import OpenAI

# model_name = "openai/whisper-small"
# processor = WhisperProcessor.from_pretrained(model_name)

# model_path = "/content/drive/MyDrive/Colab Notebooks/Phenikaa/ASR/finalterm/STT/checkpoint-2000"
# model = WhisperForConditionalGeneration.from_pretrained(model_path)
# model.generation_config.language = "vi"
# model.generation_config.task = "transcribe"
# model.generation_config.forced_decoder_ids = None


api_key = ""  # Replace with your OpenAI API key
client = OpenAI(api_key=api_key)

def correct_text(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Hãy sửa lỗi chính tả, ngữ pháp nếu có của từng từ trong văn bản tiếng Việt đầu vào mà người dùng cung cấp.Chỉ trả về văn bản đã được chỉnh sửa, không thêm dấu câu, không loại bỏ từ, nếu nhận diện từ đầu vào không hợp ngữ cảnh và không tìm được từ thay thế, giữ nguyên từ đó, và không thêm bất kỳ thông tin nào khác."},
            {"role": "user", "content": text}
        ]
    )
    new_text = response.choices[0].message.content
    return new_text

def text_to_SQL(text):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": "Hãy chuyển văn bản tiếng Việt đầu vào mà người dùng cung cấp thành dạng SQL query để truy xuất dữ liệu của sách, với các thuộc tính của database ['id', 'title', 'author', 'publisher', 'publication_year', 'pages', 'dimensions', 'registration_number', 'price', 'storage_location', 'document_type', 'availability', keywords', 'subject', 'department', 'summary', 'url'], ví dụ: [1, Quán văn 110 : chuyên đề văn học nghệ thuật, Nguyên Minh (ch.b), Hội Nhà văn, 2024, 333 tr., 21 cm., 56245, 200000, 03 Quang Trung, Sách Tham Khảo, 10/10, quán văn, Văn học nghệ thuật, Bao gồm các bài viết..., https...]. Lưu ý chỉ được phép trả lời SQL query"},
            {"role": "user", "content": text}
        ]
    )
    SQL_query = response.choices[0].message.content
    return SQL_query

import sqlite3

conn = sqlite3.connect("C:/Users/LOQ/OneDrive/Tài liệu/Visual Studio 2022/NewUI/data_fix")
def query_database(sql_query):
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        print("No results matched")
    else:
        for row in rows:
            print(row)

    return rows
