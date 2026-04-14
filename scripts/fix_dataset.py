import json

input_file = "data/pc_control_dataset.jsonl"
output_file = "data/pc_control_dataset.jsonl"

def fix_line(line):
    if not line.strip():
        return line
    data = json.loads(line)
    
    # The 'action' field is a stringified JSON
    action_data = json.loads(data["action"])
    
    # Normalize keys
    if "args" in action_data:
        action_data["parameters"] = action_data.pop("args")
    
    params = action_data.get("parameters", {})
    if "app_name" in params:
        params["name"] = params.pop("app_name")
    if "file_path" in params:
        params["path"] = params.pop("file_path")
        
    # Standardize tool names
    tool_map = {
        "get_system_telemetry": "get_system_info",
        "close_app": "terminate_process",
        "open_app": "launch_app"
    }
    if action_data["tool"] in tool_map:
        action_data["tool"] = tool_map[action_data["tool"]]
        
    data["action"] = json.dumps(action_data)
    return json.dumps(data)

with open(input_file, "r") as f:
    lines = f.readlines()

fixed_lines = [fix_line(l) for l in lines]

with open(output_file, "w") as f:
    for l in fixed_lines:
        f.write(l + "\n")

print(f"Successfully standardized {len(fixed_lines)} lines in {output_file}")
