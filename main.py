from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import re

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

# دالة استخراج معرف الفيديو من الرابط
def extract_video_id(url):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

@app.post("/process-video")
def process_video(data: VideoRequest):
    video_id = extract_video_id(data.url)
    if not video_id:
        return {"error": "رابط يوتيوب غير صالح"}

    try:
        # 1. جلب النصوص الزمنية من يوتيوب
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
    except Exception as e:
        return {"error": "عذراً، الترجمة غير متوفرة لهذا الفيديو"}

    paragraphs = []
    
    # 2. تجميع كل 3 جمل في فقرة واحدة وترجمتها
    for i in range(0, len(transcript), 3):
        group = transcript[i:i+3]
        full_text = " ".join([item['text'] for item in group])
        
        # ترجمة النص للعربية
        translated_text = GoogleTranslator(source='auto', target='ar').translate(full_text)
        
        # حساب وقت المنتصف للفقرة لاستخراج صورة المصغرة أو لقطة
        start_time = group[0]['start']
        end_time = group[-1]['start'] + group[-1]['duration']
        mid_time = int((start_time + end_time) / 2)
        
        # استخدام صورة يوتيوب مع تحديد الطابع الزمني للفقرة كشكل تقريبي ممتاز
        image_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        
        # تنسيق الوقت (دقائق:ثواني)
        minutes = mid_time // 60
        seconds = mid_time % 60
        timestamp_str = f"{minutes:02d}:{seconds:02d}"

        paragraphs.append({
            "image": image_url,
            "text": translated_text,
            "timestamp": timestamp_str
        })

    return {"paragraphs": paragraphs}
