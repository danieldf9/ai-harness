import json
path = r'C:\Users\Daniel\.gemini\antigravity-ide\brain\d1db64ac-92bd-4fd7-87a2-4f9a02930811\.system_generated\logs\transcript.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        if 'these cannot both be empty' in line:
            obj = json.loads(line)
            content = obj.get('content')
            if content and type(content) == str and not 'python' in content and not 'findstr' in content and not 'find_context.py' in content:
                print(f"Step {obj.get('step_index')}: {content[:500]}")
