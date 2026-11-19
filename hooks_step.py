import json
from pathlib import Path

from hook_writer import write_hooks
from planner import save_used

plan = json.loads(Path("plan.json").read_text(encoding="utf-8"))

if plan["chosen"] is None:
    print("First open plan.json and set 'chosen' to 1, 2 or 3.")
    raise SystemExit

idea = plan["ideas"][plan["chosen"] - 1]
save_used(idea["concept"])

hooks = write_hooks(f"{idea['title']}: {idea['concept']}")

data = {"idea": idea, "chosen_hook": None, "hooks": hooks}
Path("hooks.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("Saved to hooks.json - edit it, set 'chosen_hook', then run the writer.")