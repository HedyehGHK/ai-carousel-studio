"""
استودیوی کاروسل روانشناسی
اپ گرافیکی برای اجرای کل خط تولید: برنامه‌ریز ← هوک‌نویس ← نویسنده + بازبین ← طراح

اجرا:  streamlit run app.py   (یا دوبار کلیک روی start_app.bat)
"""
import base64
import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import designer
from hook_writer import write_hooks
from planner import load_used, plan_ideas, save_used
from writer import write_carousel

SETTINGS_FILE = Path("settings.json")
OUTPUT_DIR = Path("output")
STEPS = ["ایده", "هوک", "متن اسلایدها", "تصویر نهایی"]
CONFIDENCE_COLORS = {"بالا": "#4E7A57", "متوسط": "#B07D2B", "پایین": "#A8483E"}


# ---------- تنظیمات ----------
def load_settings():
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return {"page_name": designer.PAGE_NAME}


def save_settings(settings):
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------- ظاهر ----------
def font_face(name, path, weight):
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return (
        f"@font-face {{font-family: '{name}'; font-weight: {weight};"
        f"src: url(data:font/ttf;base64,{data}) format('truetype');}}"
    )


def inject_style():
    fonts = font_face("Vazirmatn", designer.FONT_REGULAR, 400) + font_face(
        "Vazirmatn", designer.FONT_BOLD, 700
    )
    st.markdown(
        f"""
        <style>
        {fonts}
        html, body, .stApp, .stApp * {{ font-family: 'Vazirmatn', sans-serif; }}
        .stApp [data-testid="stIconMaterial"], .stApp .material-symbols-rounded {{
            font-family: 'Material Symbols Rounded' !important;
        }}
        .stApp {{ direction: rtl; }}
        .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp li {{ text-align: right; }}
        .stApp input, .stApp textarea {{ direction: rtl; text-align: right; }}
        section[data-testid="stSidebar"] {{ direction: rtl; }}
        .block-container {{ max-width: 920px; padding-top: 2.2rem; }}
        h1 {{ font-weight: 700 !important; }}

        .stepper {{ display: flex; gap: 8px; margin: 4px 0 28px; }}
        .step {{ flex: 1; text-align: center; padding: 10px 6px; border-radius: 12px;
                 background: #EAE4D9; color: #8A857C; font-size: 0.92rem; }}
        .step b {{ display: block; font-size: 1.05rem; }}
        .step.done {{ background: #DDE7DF; color: #4E7A57; }}
        .step.active {{ background: #6B8F71; color: #FFFFFF; }}

        .badge {{ display: inline-block; padding: 2px 12px; border-radius: 999px;
                  font-size: 0.82rem; color: white; margin-left: 6px; }}
        .badge.type {{ background: #8A857C; }}
        .muted {{ color: #7A756C; font-size: 0.9rem; }}
        [data-testid="stImage"] img {{ border-radius: 10px; border: 1px solid #DDD5C7;
                                        box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        .hookbox {{ background: #FFFFFF; border-radius: 14px; padding: 18px 22px;
                    font-size: 1.25rem; font-weight: 700; border-right: 6px solid #6B8F71; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def stepper(current):
    parts = []
    for i, name in enumerate(STEPS, start=1):
        state = "done" if i < current else "active" if i == current else ""
        parts.append(f'<div class="step {state}"><b>{i}</b>{name}</div>')
    st.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


def badge(text, color=None, css_class=""):
    style = f' style="background:{color}"' if color else ""
    return f'<span class="badge {css_class}"{style}>{text}</span>'


# ---------- وضعیت ----------
def init_state():
    defaults = {
        "step": 1, "topic": "", "ideas": [], "idea": None, "hooks": [],
        "carousel": None, "issues": [], "models": {}, "run_dir": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def go(step):
    st.session_state.step = step
    st.rerun()


def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def show_error(error):
    st.error("ارتباط با Gemini برقرار نشد. چند دقیقه‌ی دیگر دوباره امتحان کن.")
    with st.expander("جزئیات فنی خطا"):
        st.code(str(error))


# ---------- مرحله ۱: ایده ----------
def collect_idea(i, idea):
    edited = dict(idea)
    for field in ["title", "concept", "related_figures", "why_curious",
                  "daily_life", "uncertainty_note"]:
        edited[field] = st.session_state.get(f"idea{i}_{field}", idea[field])
    return edited


def step_ideas():
    st.markdown("### موضوع امروز چیه؟")
    col_input, col_button = st.columns([3, 1], vertical_alignment="bottom")
    with col_input:
        topic = st.text_input("موضوع", value=st.session_state.topic,
                              placeholder="مثلاً: اهمال‌کاری، تنهایی، حسادت...")
    with col_button:
        clicked = st.button("پیشنهاد ایده", type="primary", use_container_width=True)

    if clicked:
        if not topic.strip():
            st.warning("اول یک موضوع بنویس.")
        else:
            with st.spinner("برنامه‌ریز دارد مفاهیم مرتبط را بررسی می‌کند..."):
                try:
                    ideas = plan_ideas(topic.strip())
                    st.session_state.topic = topic.strip()
                    st.session_state.ideas = [idea.model_dump() for idea in ideas]
                    for key in [k for k in st.session_state if k.startswith("idea") and "_" in k]:
                        del st.session_state[key]
                except Exception as error:
                    show_error(error)

    if not st.session_state.ideas:
        return

    st.markdown(
        '<p class="muted">هر متنی را که لازم است اصلاح کن (مثلاً نام‌ها را چک کن)، '
        "بعد ایده‌ای را که می‌خواهی انتخاب کن.</p>",
        unsafe_allow_html=True,
    )
    for i, idea in enumerate(st.session_state.ideas):
        with st.container(border=True):
            color = CONFIDENCE_COLORS.get(idea["confidence"], "#8A857C")
            st.markdown(
                badge(idea["concept_type"], css_class="type")
                + badge(f"اطمینان علمی: {idea['confidence']}", color),
                unsafe_allow_html=True,
            )
            st.text_input("عنوان", idea["title"], key=f"idea{i}_title")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("مفهوم اصلی", idea["concept"], key=f"idea{i}_concept")
            with c2:
                st.text_input("نظریه‌پرداز / مکتب", idea["related_figures"],
                              key=f"idea{i}_related_figures")
            st.text_area("چرا کنجکاوکننده است", idea["why_curious"],
                         key=f"idea{i}_why_curious", height=90)
            st.text_area("کاربرد روزمره", idea["daily_life"],
                         key=f"idea{i}_daily_life", height=90)
            st.text_area("نکته‌ی احتیاط", idea["uncertainty_note"],
                         key=f"idea{i}_uncertainty_note", height=80)
            if st.button("انتخاب این ایده", key=f"choose{i}", type="primary"):
                chosen = collect_idea(i, idea)
                with st.spinner("هوک‌نویس دارد هوک می‌نویسد..."):
                    try:
                        hooks = write_hooks(f"{chosen['title']}: {chosen['concept']}")
                    except Exception as error:
                        show_error(error)
                        return
                save_used(chosen["concept"])
                st.session_state.idea = chosen
                st.session_state.hooks = hooks
                st.session_state.pop("hook_choice", None)
                st.session_state.pop("hook_text", None)
                go(2)


# ---------- مرحله ۲: هوک ----------
def sync_hook_text():
    st.session_state.hook_text = st.session_state.hook_choice


def step_hooks():
    idea = st.session_state.idea
    st.markdown(f"### {idea['title']}")
    st.markdown(f'<p class="muted">{idea["concept"]} · {idea["related_figures"]}</p>',
                unsafe_allow_html=True)

    hooks = st.session_state.hooks
    st.session_state.setdefault("hook_choice", hooks[0])
    st.session_state.setdefault("hook_text", hooks[0])

    st.radio("یک هوک انتخاب کن", hooks, key="hook_choice", on_change=sync_hook_text)
    st.text_area("متن نهایی هوک (اگر خواستی ویرایشش کن)", key="hook_text", height=80)

    c1, c2, c3 = st.columns([2, 1.3, 1])
    with c1:
        write_clicked = st.button("نوشتن اسلایدها", type="primary", use_container_width=True)
    with c2:
        if st.button("هوک‌های تازه", use_container_width=True):
            with st.spinner("هوک‌نویس دارد دوباره می‌نویسد..."):
                try:
                    st.session_state.hooks = write_hooks(
                        f"{idea['title']}: {idea['concept']}")
                    st.session_state.pop("hook_choice", None)
                    st.session_state.pop("hook_text", None)
                    st.rerun()
                except Exception as error:
                    show_error(error)
    with c3:
        if st.button("بازگشت", use_container_width=True):
            go(1)

    if write_clicked:
        hook = st.session_state.hook_text.strip()
        with st.status("نویسنده و بازبین مشغول کارند...", expanded=True) as status:
            try:
                carousel, issues, models = write_carousel(
                    idea, hook, on_progress=lambda msg: status.write(msg))
            except Exception as error:
                status.update(label="خطا", state="error")
                show_error(error)
                return
            status.update(label="متن اسلایدها آماده شد", state="complete")
        st.session_state.hook = hook
        st.session_state.carousel = carousel
        st.session_state.issues = issues
        st.session_state.models = models
        for key in [k for k in st.session_state if k.startswith("slide") or k == "caption"]:
            del st.session_state[key]
        go(3)


# ---------- مرحله ۳: متن اسلایدها ----------
def collect_carousel():
    slides = []
    for i, slide in enumerate(st.session_state.carousel["slides"]):
        slides.append({
            "title": st.session_state.get(f"slide{i}_title", slide["title"]),
            "body": st.session_state.get(f"slide{i}_body", slide["body"]),
        })
    caption = st.session_state.get("caption", st.session_state.carousel["caption"])
    return {"slides": slides, "caption": caption}


def step_text():
    carousel = st.session_state.carousel
    issues = st.session_state.issues
    models = st.session_state.models

    if issues:
        st.warning(f"بازبین بعد از ۳ دور هنوز {len(issues)} ایراد دارد. قبل از ادامه نگاهشان کن:")
        for issue in issues:
            where = "کپشن" if issue["slide"] == 0 else f"اسلاید {issue['slide']}"
            st.markdown(f"- **{where}:** {issue['problem']} ← {issue['fix']}")
    else:
        st.success("بازبین ایراد واضحی پیدا نکرد. خواندن نهایی با توست.")

    if "lite" in str(models.get("reviewer", "")):
        st.info("بازبینی با مدل سبک (lite) انجام شد. با دقت بیشتری خودت بخوان.")

    st.markdown('<p class="muted">هر اسلاید را می‌توانی همین‌جا ویرایش کنی.</p>',
                unsafe_allow_html=True)
    for i, slide in enumerate(carousel["slides"]):
        with st.container(border=True):
            st.markdown(f"**اسلاید {i + 1}**" + (" · هوک" if i == 0 else ""))
            if i > 0:
                st.text_input("تیتر", slide["title"], key=f"slide{i}_title")
            st.text_area("متن", slide["body"], key=f"slide{i}_body", height=100)

    st.text_area("کپشن پست", carousel["caption"], key="caption", height=120)

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("ساخت تصویر اسلایدها", type="primary", use_container_width=True):
            st.session_state.carousel = collect_carousel()
            st.session_state.run_dir = None
            go(4)
    with c2:
        if st.button("بازگشت به هوک", use_container_width=True):
            go(2)


# ---------- مرحله ۴: تصویر نهایی ----------
def safe_name(text):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", text).strip("_")[:40]


def render_slides(page_name):
    carousel = st.session_state.carousel
    designer.PAGE_NAME = page_name
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    run_dir = OUTPUT_DIR / f"{stamp}_{safe_name(st.session_state.topic)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    slides = carousel["slides"]
    for i, slide in enumerate(slides, start=1):
        image = designer.make_slide(slide, i, len(slides))
        image.save(run_dir / f"slide_{i:02d}.png")

    (run_dir / "caption.txt").write_text(carousel["caption"], encoding="utf-8")
    record = {
        "topic": st.session_state.topic,
        "idea": st.session_state.idea,
        "hook": st.session_state.hook,
        **carousel,
        "remaining_issues": st.session_state.issues,
        "models": st.session_state.models,
    }
    (run_dir / "carousel.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    st.session_state.run_dir = str(run_dir)


def zip_folder(folder):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in sorted(Path(folder).iterdir()):
            archive.write(path, path.name)
    return buffer.getvalue()


def step_images(page_name):
    if st.session_state.run_dir is None:
        with st.spinner("طراح دارد اسلایدها را می‌سازد..."):
            render_slides(page_name)

    run_dir = Path(st.session_state.run_dir)
    images = sorted(run_dir.glob("slide_*.png"))
    st.success(f"{len(images)} اسلاید ساخته شد.")
    st.markdown(f'<p class="muted">ذخیره شد در پوشه‌ی: <span dir="ltr">{run_dir.resolve()}</span></p>',
                unsafe_allow_html=True)

    st.download_button("دانلود همه‌ی اسلایدها (zip)", zip_folder(run_dir),
                       file_name=f"{run_dir.name}.zip", type="primary",
                       use_container_width=True)

    columns = st.columns(3)
    for i, path in enumerate(images):
        with columns[i % 3]:
            st.image(str(path), use_container_width=True)

    st.markdown("#### کپشن (برای کپی، روی آیکون گوشه‌ی کادر بزن)")
    st.code(st.session_state.carousel["caption"], language=None, wrap_lines=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("بازگشت به ویرایش متن", use_container_width=True):
            go(3)
    with c2:
        if st.button("شروع پست جدید", use_container_width=True):
            reset_all()


# ---------- نوار کناری ----------
def sidebar(settings):
    with st.sidebar:
        st.markdown("### تنظیمات")
        page_name = st.text_input("آیدی پیج (پایین اسلایدها)", settings["page_name"])
        if page_name != settings["page_name"]:
            settings["page_name"] = page_name
            save_settings(settings)

        used = load_used()
        with st.expander(f"مفاهیم استفاده‌شده ({len(used)})"):
            if used:
                for concept in reversed(used):
                    st.markdown(f"- {concept}")
            else:
                st.markdown("هنوز چیزی ثبت نشده.")

        st.divider()
        if st.button("شروع از اول", use_container_width=True):
            reset_all()
    return page_name


# ---------- اجرا ----------
def main():
    st.set_page_config(page_title="استودیوی کاروسل", page_icon="🧠", layout="centered")
    inject_style()
    init_state()
    settings = load_settings()
    page_name = sidebar(settings)

    st.title("استودیوی کاروسل روانشناسی")
    stepper(st.session_state.step)

    step = st.session_state.step
    if step == 1:
        step_ideas()
    elif step == 2:
        step_hooks()
    elif step == 3:
        step_text()
    else:
        step_images(page_name)


main()
