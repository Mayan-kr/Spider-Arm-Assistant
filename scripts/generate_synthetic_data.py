import json
import random

tools = ["screenshot", "launch_app", "get_system_info", "type_text", "terminate_process", "delete_file"]

templates = [
    {
        "instructions": ["Take a screenshot", "Capture the screen", "Save a picture of my desktop", "Snapshot the current window"],
        "thought": "The user wants a visual capture of their screen. I'll use the screenshot tool.",
        "action": {"tool": "screenshot", "parameters": {}}
    },
    {
        "instructions": ["Open {app}", "Launch {app}", "Start the {app} application", "Run {app}"],
        "thought": "I need to open a specific application for the user.",
        "action": {"tool": "launch_app", "parameters": {"name": "{app}"}}
    },
    {
        "instructions": ["What is the {metric} usage?", "Check {metric} status", "Show me my {metric} level", "How much {metric} am I using?"],
        "thought": "The user is asking for system telemetry regarding {metric}.",
        "action": {"tool": "get_system_info", "parameters": {"metric": "{m_key}"}}
    },
    {
        "instructions": ["Type '{text}'", "Enter the text '{text}'", "Write out '{text}' for me"],
        "thought": "I'll simulate keyboard input to type the requested text.",
        "action": {"tool": "type_text", "parameters": {"text": "{text}"}}
    },
    {
        "instructions": ["Close {app}", "Kill the {app} process", "Terminate {app}"],
        "thought": "I need to stop the {app} process.",
        "action": {"tool": "terminate_process", "parameters": {"name": "{app}"}}
    },
    {
        "instructions": ["Delete {file}", "Remove the file at {file}", "Get rid of {file}"],
        "thought": "Deleting a file requires caution. I will call the delete_file tool which triggers confirmation.",
        "action": {"tool": "delete_file", "parameters": {"path": "{file}"}}
    }
]

apps = ["chrome", "notepad", "calculator", "spotify", "vscode", "discord", "slack", "excel"]
metrics = [("cpu", "cpu"), ("memory", "mem"), ("ram", "mem"), ("disk", "disk"), ("hard drive", "disk")]
texts = ["Hello World", "Welcome to Qwen", "Testing 123", "Search for AI news", "Best coding assistant"]
files = ["C:/temp/test.log", "D:/downloads/old_report.pdf", "C:/Users/kumar/Documents/temp.txt", "E:/backup.zip"]

dataset = []

for _ in range(60):
    tpl = random.choice(templates)
    instr = random.choice(tpl["instructions"])
    
    # Fill placeholders
    app = random.choice(apps)
    metric_label, metric_key = random.choice(metrics)
    text = random.choice(texts)
    file = random.choice(files)
    
    instr = instr.replace("{app}", app).replace("{metric}", metric_label).replace("{text}", text).replace("{file}", file)
    thought = tpl["thought"].replace("{app}", app).replace("{metric}", metric_label)
    
    action = json.loads(json.dumps(tpl["action"]))
    params = action.get("parameters", {})
    if "name" in params: params["name"] = app
    if "metric" in params: params["metric"] = metric_key
    if "text" in params: params["text"] = text
    if "path" in params: params["path"] = file
    
    dataset.append({
        "instruction": instr,
        "thought": thought,
        "action": json.dumps(action)
    })

# Add the original hand-crafted ones (already standardized)
try:
    with open("data/pc_control_dataset.jsonl", "r") as f:
        original = [json.loads(l) for l in f if l.strip()]
    dataset = original + dataset
except:
    pass

with open("data/pc_control_dataset_expanded.jsonl", "w") as f:
    for entry in dataset:
        f.write(json.dumps(entry) + "\n")

print(f"Generated {len(dataset)} examples in data/pc_control_dataset_expanded.jsonl")
