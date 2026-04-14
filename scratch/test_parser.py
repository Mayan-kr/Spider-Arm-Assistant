import json

def test_parse(response):
    clean_response = response.replace("<|endoftext|>", "").strip()
    if "### Action:" in clean_response:
        try:
            action_section = clean_response.split("### Action:")[1].strip()
            print(f"Action Section: '{action_section}'")
            start = action_section.find("{")
            end = action_section.rfind("}") + 1
            if start != -1 and end != -1:
                action_str = action_section[start:end]
                print(f"Action Str: '{action_str}'")
                action_data = json.loads(action_str)
                if "args" in action_data and "parameters" not in action_data:
                    action_data["parameters"] = action_data["args"]
                return action_data
        except Exception as e:
            print(f"Error: {e}")
            return None
    return None

raw_resp = """### Instruction:
Check my disk space

### Thought:
I need to query the system for disk usage.

### Action:
{"tool": "get_system_info", "args": {}}<|endoftext|>"""

print(f"Result: {test_parse(raw_resp)}")
