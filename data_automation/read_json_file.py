import json
import sys
import os

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "리워드설정.json")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"Error reading or parsing JSON: {e}", file=sys.stderr)
    sys.exit(1)