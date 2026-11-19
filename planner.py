import json
from pathlib import Path
from typing import Literal
from llm import generate

from pydantic import BaseModel, Field


LOG_FILE = Path("used_concepts.json")

SYSTEM_PROMPT = """
تو برنامه‌ریز محتوای یک پیج اینستاگرام روانشناسی برای مخاطب عمومی فارسی‌زبان هستی.

برای هر موضوع، با دید یک متخصص آشنا با تاریخ روانشناسی، نظریه‌های شخصیت، روان‌درمانی،
روانشناسی شناختی، اجتماعی، رشد، خانواده، زوج‌درمانی و یافته‌های معاصر فکر کن.
آزادانه مفاهیم، مکاتب، نظریه‌پردازان، مدل‌های روانشناختی، روش‌های درمانی و اصطلاحات
تخصصی مرتبط با موضوع را کشف کن.
مثال‌هایی مثل درمان‌های موج سوم، نظریه‌ی دلبستگی، طرحواره‌درمانی، روانشناسی تحلیلی و
درمان‌های انسان‌گرایانه فقط الهام‌بخش‌اند و انتخابت را محدود نمی‌کنند.

قوانین:
1. طیف متنوعی از مفاهیم مرتبط را بررسی کن و به یک فهرست ثابت یا چند نظریه‌پرداز
   معروف محدود نشو.
2. مفاهیم کمتر شناخته‌شده اما جالب و قابل توضیح را هم در نظر بگیر.
3. تفاوت میان مکتب نظری، مفهوم روانشناختی، روش درمانی و یافته‌ی پژوهشی را حفظ کن.
4. هیچ ارتباط علمی ساختگی یا ترکیب مصنوعی را فقط برای جذابیت نساز.
5. دقیقاً سه ایده‌ی متفاوت پیشنهاد کن، ترجیحاً از سه نوع مفهوم مختلف.
6. اگر درباره‌ی انتساب یک نظریه یا اعتبار علمی آن مطمئن نیستی، صریحاً بنویس
   و ادعای تأیید علمی نکن.
7. مفاهیمی که کاربر گفته قبلاً استفاده شده‌اند را تکرار نکن.
8. میزان اطمینان را برای «کاربرد این مفهوم در همین موضوع» بده، نه برای اعتبار کلی مفهوم.
   اطمینان «بالا» فقط وقتی است که پژوهش مستقیم روی همین موضوع وجود دارد.

9. اگر موضوع یک گروه یا شرایط مشخص را نام برده (مثلاً اتیسم، ADHD، نوجوانان، سالمندان،
   والدین)، هر سه ایده باید اختصاصاً درباره‌ی همان گروه باشد. مفهومی که برای همه صدق
   می‌کند فقط وقتی قابل قبول است که مشخصاً توضیح بدهد در این گروه چه فرقی دارد.
   نظریه‌پردازی را نام نبر که کارش مستقیماً به این گروه مربوط نیست.
10. اگر کاربر مخاطب را مشخص کرده (مثلاً والدین)، ایده‌ها را برای همان مخاطب بنویس.
11. درباره‌ی گروه‌های خاص، زبان محترمانه و غیرانگ‌زا به کار ببر؛ از کلماتی مثل «مبتلا»
    یا «درمان قطعی» پرهیز کن و تفاوت را لزوماً نقص معرفی نکن.

همه‌ی بخش‌ها را به فارسی و قابل فهم برای مخاطب عمومی بنویس.
"""


class Idea(BaseModel):
    title: str
    concept: str
    concept_type: Literal["مکتب نظری",
                          "مفهوم روانشناختی", "روش درمانی", "یافته‌ی پژوهشی"]
    related_figures: str
    why_curious: str
    daily_life: str
    confidence: Literal["بالا", "متوسط", "پایین"]
    uncertainty_note: str = Field(
        description="حداقل یک محدودیت، ساده‌سازی یا نکته‌ی نامطمئن. هرگز تعریف از مفهوم ننویس."
    )


class Plan(BaseModel):
    ideas: list[Idea]


def load_used():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return []


def save_used(concept):
    used = load_used()
    used.append(concept)
    LOG_FILE.write_text(json.dumps(
        used, ensure_ascii=False, indent=2), encoding="utf-8")


def plan_ideas(topic, details=""):
    used = load_used()
    avoid = "، ".join(used[-30:]) if used else "هیچ"
    extra = f"\nجزئیات و مخاطب: {details}" if details.strip() else ""
    response = generate(
        f"موضوع: {topic}{extra}\nمفاهیمی که قبلاً استفاده شده‌اند: {avoid}",
        SYSTEM_PROMPT,
        schema=Plan,
    )
    return response.parsed.ideas


def save_plan(topic, ideas):
    data = {
        "topic": topic,
        "chosen": None,
        "ideas": [idea.model_dump() for idea in ideas],
    }
    Path("plan.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    topic = "اهمال‌کاری"
    ideas = plan_ideas(topic)
    save_plan(topic, ideas)
    print("Saved to plan.json - edit it, set 'chosen', then run hooks_step.py")
