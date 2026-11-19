import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

client = genai.Client(
    http_options=types.HttpOptions(
        timeout=60000,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
)


def generate(contents, system_prompt, schema=None, rounds=3):
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json" if schema else None,
        response_schema=schema,
    )
    for round_no in range(rounds):
        for model in MODELS:
            try:
                print(f"Trying {model}...")
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except errors.ServerError as e:
                print(f"  {model} is busy ({e.code}), trying next...")
            except errors.ClientError as e:
                if e.code in (404, 429):
                    print(f"  {model} not available ({e.code}), trying next...")
                else:
                    raise
        wait = 10 * (round_no + 1)
        print(f"All models busy. Waiting {wait} seconds...")
        time.sleep(wait)
    raise RuntimeError("All models failed. Try again later.")