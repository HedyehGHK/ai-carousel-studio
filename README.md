# AI Carousel Studio — Multi-Agent Content Pipeline

A multi-agent LLM application that turns a psychology topic into a ready-to-publish **Persian Instagram carousel** (7–10 slide images plus a caption), with a human in the loop at every key step.

Built with **Python, Google Gemini, Pydantic, Streamlit, and Pillow**.

---

## How it works

The app walks the user through four steps in a Persian, right-to-left (RTL) Streamlit interface:

| Step | Agent | What happens |
|---|---|---|
| 1. Ideas | **Planner** | Suggests three different ideas for the topic (a theory, a psychological concept, a therapy method, or a research finding), each with a confidence level and an uncertainty note. Concepts already used in earlier posts are avoided. The user can edit any idea before choosing one. |
| 2. Hooks | **Hook writer** | Writes five opening lines, one of each type: a feeling, a shared experience, a common mistake, a number-and-promise, and a surprising statement. The user picks one and can edit it. |
| 3. Text | **Writer + Reviewer** | The writer drafts the slides and caption. A revision loop then checks the draft and sends issues back to the writer (up to three rounds). The user can edit every slide afterwards. |
| 4. Images | **Designer** | Renders branded 1080×1350 slide images and offers them as a single ZIP download. |

### The writer–reviewer loop

Each draft is checked in two ways:

- **Code checks** (deterministic): slide 1 must be exactly the chosen hook, 7–10 slides, no title on slide 1, at most 40 words per slide and 8 words per title.
- **LLM review**: contradictions between slides, overstated certainty compared with the idea's confidence level, new claims or names not in the idea, whether the hook's promise is delivered, tone, safety (no diagnostic labels or medication advice, and a pointer to professional help on sensitive topics), and plain-language explanations of terms.

Any remaining issues are shown to the user instead of being hidden.

### Reliability

- **Structured output:** every agent that returns data uses a Pydantic schema, so Gemini responses are validated JSON rather than free text.
- **Model fallback:** `llm.py` tries a list of Gemini models in order. If a model is busy or rate-limited, it moves to the next one, and waits and retries if all of them fail.

### Persian text rendering

Pillow does not shape Persian text on its own. The designer uses `arabic-reshaper` and `python-bidi` to join letters correctly and lay them out right-to-left, with custom word wrapping and the Vazirmatn font.

---

## Project structure

```
app.py            Streamlit interface (4-step flow, editing, settings sidebar)
llm.py            Gemini client with multi-model fallback
planner.py        Planner agent: three ideas per topic (Pydantic schema)
hook_writer.py    Hook writer agent: five hooks of five types
writer.py         Writer agent + revision loop
reviewer.py       Code checks + LLM reviewer
designer.py       Slide image renderer (Pillow, RTL shaping)
fonts/            Vazirmatn font files (SIL Open Font License)
.streamlit/       Streamlit theme settings
practice/         Early learning exercises
```

## Running locally

Prerequisite: Python 3.10+ and a [Gemini API key](https://aistudio.google.com/apikey).

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a file named `.env` in the project folder:

```
GEMINI_API_KEY=your-key-here
```

Then run:

```
streamlit run app.py
```

or double-click `start_app.bat` on Windows.

The `.env` file and all generated output (slides, plans, hooks) are excluded from Git.

## Limitations

- The content and interface are in Persian only.
- The quality of the ideas depends on the model; the confidence level and uncertainty notes are there so a human reviews them before publishing.
- Slide design uses one fixed template.
