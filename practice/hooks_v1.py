from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(http_options={"timeout": 60000})

topic = "اضطراب اجتماعی"

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=f"برای یک پست کاروسل اینستاگرام درباره‌ی {topic}، ۵ هوک بنویس.",
)

with open("output_v1.txt", "w", encoding="utf-8") as f:
    f.write(response.text)

print("ذخیره شد: output_v1.txt")
