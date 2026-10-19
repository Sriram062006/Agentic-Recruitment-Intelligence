import json
import re

with open(r"C:/Users/srira/.gemini/antigravity/brain/b69e489c-4cfe-42cd-8956-d8bb70598924/.system_generated/steps/4002/output.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Match the json array
m = re.search(r"\[\{.*?\}\]", text, re.DOTALL)
if m:
    records = json.loads(m.group(0))
    print("Parsed records:", len(records))
    hashes = [r["file_hash"] for r in records if "file_hash" in r]
    with open("backend/temp_hashes.json", "w", encoding="utf-8") as out:
        json.dump(hashes, out)
    print("Saved", len(hashes), "hashes")
else:
    print("Regex match failed")
