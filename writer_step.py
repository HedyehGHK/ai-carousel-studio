import json
from pathlib import Path

from writer import write_carousel

data = json.loads(Path("hooks.json").read_text(encoding="utf-8"))

if data["chosen_hook"] is None:
    print("First open hooks.json and set 'chosen_hook'.")
    raise SystemExit

idea = data["idea"]
hook = data["hooks"][data["chosen_hook"] - 1]

carousel, issues, models = write_carousel(idea, hook)

output = {
    "idea": idea,
    "hook": hook,
    **carousel,
    "remaining_issues": issues,
    "models": models,
}
Path("carousel.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
)

if issues:
    print("Not fully approved - check 'remaining_issues' in carousel.json")
else:
    print("Approved! Saved to carousel.json")
