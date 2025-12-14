from pathlib import Path
import os

paths = [
    Path.home() / ".cache" / "gpt4all",
    Path(os.getenv("LOCALAPPDATA", "")) / "nomic.ai" / "GPT4All",
]

for p in paths:
    print("\n==", p)
    if p.exists():
        files = sorted(p.glob("*.gguf"))
        print("count:", len(files))
        for f in files[:30]:
            print(" -", f.name)
    else:
        print("NOT FOUND")
