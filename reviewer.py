import json

from pydantic import BaseModel

from llm import generate

SYSTEM_PROMPT = """
تو ویراستار و بازبین علمی یک پیج اینستاگرام روانشناسی فارسی‌زبان هستی.
یک ایده‌ی تأییدشده و متن کاروسلی که بر اساس آن نوشته شده را می‌گیری.
کل پست را با هم بخوان و فقط ایرادهای واقعی را گزارش کن.

چک‌لیست:
1. تناقض: آیا دو اسلاید حرف هم را نقض می‌کنند؟
2. قطعیت: آیا جایی قطعیت بیشتر از «میزان اطمینان» و «نکته‌ی احتیاط» ایده است؟
   کلمه‌هایی مثل «کاملاً»، «همیشه»، «قطعاً»، «ثابت شده» و «معجزه» را با دقت بررسی کن.
3. ادعای تازه: آیا ادعا یا نام فردی آمده که در ایده نیست؟
4. وعده‌ی هوک: آیا اسلایدها دقیقاً همان چیزی را که هوک وعده داده تحویل می‌دهند؟
5. لحن: آیا همه‌ی تیترها، متن‌ها و کپشن محاوره‌ای و خطاب به «تو» هستند؟
6. ایمنی: برچسب تشخیصی، توصیه‌ی دارویی یا لحن سرزنش‌آمیز نباشد.
   اگر موضوع حساس است (مثل اعتیاد، افسردگی، آسیب به خود یا سوگ)،
   یکی از اسلایدهای آخر باید به کمک تخصصی اشاره کند.
7. وضوح: هر اصطلاح اولین بار که می‌آید، با زبان ساده توضیح داده شده باشد.

برای هر ایراد:اسلاید ۱ هوکی است که کاربر خودش انتخاب کرده؛ درباره‌ی متن آن ایراد نگیر. 
 شماره‌ی اسلاید (برای کپشن عدد 0)، مشکل، و پیشنهاد اصلاح مشخص.
ایرادهای سلیقه‌ای یا خیلی جزئی را گزارش نکن.
اگر ایرادی نیست، فهرست خالی برگردان.
"""


class Issue(BaseModel):
    slide: int
    problem: str
    fix: str


class Review(BaseModel):
    issues: list[Issue]


def code_checks(carousel, hook):
    issues = []
    slides = carousel["slides"]
    if slides and slides[0]["body"].strip() != hook.strip():
        issues.append({"slide": 1, "problem": "اسلاید اول دقیقاً همان هوک انتخاب‌شده نیست",
                       "fix": f"متن اسلاید ۱ را دقیقاً این بگذار: {hook}"})
    if not 7 <= len(slides) <= 10:
        issues.append({"slide": 0, "problem": f"تعداد اسلایدها {len(slides)} است",
                       "fix": "بین ۷ تا ۱۰ اسلاید بنویس"})
    if slides and slides[0]["title"] != "":
        issues.append({"slide": 1, "problem": "اسلاید اول تیتر دارد",
                       "fix": "تیتر اسلاید ۱ را خالی بگذار"})
    for i, s in enumerate(slides, start=1):
        if len(s["body"].split()) > 40:
            issues.append({"slide": i, "problem": "متن بیشتر از ۴۰ کلمه است",
                           "fix": "متن را کوتاه‌تر کن"})
        if len(s["title"].split()) > 8:
            issues.append({"slide": i, "problem": "تیتر بیشتر از ۸ کلمه است",
                           "fix": "تیتر را کوتاه‌تر کن"})
    return issues


def review(idea, carousel, hook):
    issues = code_checks(carousel, hook)
    request = (
        f"ایده:\n{json.dumps(idea, ensure_ascii=False, indent=2)}\n\n"
        f"کاروسل:\n{json.dumps(carousel, ensure_ascii=False, indent=2)}"
    )
    response = generate(request, SYSTEM_PROMPT, schema=Review)
    issues += [issue.model_dump() for issue in response.parsed.issues]
    return issues, response.model_version
