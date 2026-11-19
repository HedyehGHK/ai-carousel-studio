from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

response = client.models.generate_content(
     model="gemini-3.8-flash",
    contents="یک جمله‌ی کوتاه درباره‌ی اهمیت خواب برای سلامت روان بنویس.",
)

print(response.text)