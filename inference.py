from unsloth import FastLanguageModel
import torch
import json
from controller.tools import (
    screenshot, launch_app, get_system_info, 
    type_text, terminate_process, delete_file, 
    confirm_action, control_media
)

import re

# This script handles the local AI inference using Unsloth 4-bit quantization.

def load_agent_model(model_path="qwen_assistant_lora"):
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_path,
        max_seq_length = 2048,
        load_in_4bit = True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def repair_json_string(s):
    """Aggressive fixes for small model (1.5B) JSON hallucinations"""
    # 1. Standardize quotes
    s = s.replace("'", '"')
    
    # 2. Fix missing colons or quotes around keys (common 1.5B fail)
    # Fix {"tool" "name"} or {tool: "name"}
    s = re.sub(r'(\{|,)\s*"?(\w+)"?\s*(\s|:)\s*', r'\1"\2": ', s)
    
    # 3. Fix missing "parameters" key: {"tool": "name", {}} -> {"tool": "name", "parameters": {}}
    s = re.sub(r'("\w+"),?\s*\{', r'\1, "parameters": {', s)
    
    # 4. Ensure balanced braces
    if s.count('{') > s.count('}'):
        s += '}' * (s.count('{') - s.count('}'))
    
    # 5. Greedy clip: get the last valid JSON block
    last_brace = s.rfind('}')
    if last_brace != -1:
        s = s[:last_brace+1]
        
    return s

# Neural Blueprint: Spider-Arm v2.5 Capabilities
SYSTEM_PROMPT = """You are Spider-Arm v2.5, a professional PC assistant. 
Execute instructions using ONLY the tools below. NEVER invent or hallucinate new tools.
If a user is creative/informal, map their intent to the best possible available tool.

AVAILABLE TOOLS:
1. launch_app(name): Launches apps/shortcuts. Supports aliases: 'browser' (Brave), 'terminal', 'calculator', 'notepad'.
2. screenshot(): Captures the screen.
3. get_system_info(metric): stats like 'cpu', 'mem', 'disk', 'temp', or 'all'.
4. control_media(action, app_hint): actions: 'play_pause' (use for play/resume/pause), 'next', 'previous', 'volume_up', 'volume_down'. Use app_hint (e.g., 'Spotify', 'Chrome') to wake up the app.
5. type_text(text): Types keyboard input.
6. terminate_process(name): Closes an app by name.
7. delete_file(path): Deletes a file (Requires approval).
8. confirm_action(action_id): Approves a pending action.

9. create_file(name, content, append): Creates/Overwrites a file. Set append=True to add text to the end.
10. create_folder(name): Creates a folder (Default: Desktop).
11. press_key(key): Presses a single key (e.g., 'enter', 'space', 'tab', 'esc').

EXAMPLES:
- "Create a note called hello.txt saying hi" -> ### Thought: Writing a file. ### Action: {"tool": "create_file", "parameters": {"name": "hello.txt", "content": "hi", "append": false}}
- "Add 'Remember to buy milk' to notes.txt" -> ### Thought: Appending to file. ### Action: {"tool": "create_file", "parameters": {"name": "notes.txt", "content": "Remember to buy milk", "append": true}}
- "Write to my work.txt and say Done" -> ### Thought: Persistence request. Use create_file tool. ### Action: {"tool": "create_file", "parameters": {"name": "work.txt", "content": "Done", "append": false}}
- "Open spotify" -> ### Thought: Need to open music player. ### Action: {"tool": "launch_app", "parameters": {"name": "spotify"}}
- "Resume the music" -> ### Thought: Toggle play/pause. Use app_hint for reliability. ### Action: {"tool": "control_media", "parameters": {"action": "play_pause", "app_hint": "spotify"}}
- "Next song" -> ### Thought: Skip music. ### Action: {"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}
- "Volume up" -> ### Thought: Increase PC audio. ### Action: {"tool": "control_media", "parameters": {"action": "volume_up"}}
- "Silence the PC" -> ### Thought: Mute audio. ### Action: {"tool": "control_media", "parameters": {"action": "mute"}}
- "Check battery/heat" -> ### Thought: Telemetry check. ### Action: {"tool": "get_system_info", "parameters": {"metric": "all"}}
"""

def get_agent_response(model, tokenizer, instruction, history=""):
    # Unified Premium Prompt
    prompt = f"{SYSTEM_PROMPT}\n### Instruction:\n{instruction}\n\n### Thought:\n"
    inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
    input_ids = inputs.input_ids
    # Use greedy decoding (do_sample=False) for maximum tool-calling precision
    outputs = model.generate(input_ids, max_new_tokens = 256, use_cache = True, do_sample=False)
    
    # Only decode the NEW tokens (ignoring the instructions and examples in the prompt)
    generated_text = tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
    
    print(f"[DEBUG] Model Output: {generated_text}")
    clean_response = generated_text
    
    # --- FLEXIBLE PARSING LOGIC ---
    # We look for a JSON block anywhere in the response if it failed the strict header check
    action_str = None
    
    # 1. Try strict Action header first
    if "### Action:" in clean_response:
        parts = clean_response.split("### Action:")
        action_section = parts[-1].strip()
        start = action_section.find("{")
        end = action_section.rfind("}") + 1
        if start != -1 and end != -1:
            action_str = action_section[start:end]
            
    # 2. Fallback: Search the whole response for any JSON block
    if not action_str:
        start = clean_response.find("{")
        end = clean_response.rfind("}") + 1
        if start != -1 and end != -1:
            action_str = clean_response[start:end]
            
    if action_str:
        try:
            # Apply SMART REPAIR to handle hallucinations
            repaired_str = repair_json_string(action_str)
            
            # Final check: Python's json loader is strict. 
            # If the model added text AFTER the JSON (Extra Data), rfind('}') + 1 already clipped it.
            action_data = json.loads(repaired_str)
            
            # Normalize keys: accept 'args', 'params', or 'parameters'
            params = action_data.get("parameters") or action_data.get("args") or action_data.get("params") or {}
            action_data["parameters"] = params
            
            # Standardize tool names (Aliasing)
            tool_aliases = {
                "get_system_telemetry": "get_system_info",
                "get_telemetry": "get_system_info",
                "capture_screenshot": "screenshot",
                "take_screenshot": "screenshot",
                "close_app": "terminate_process",
                "open_app": "launch_app"
            }
            
            if "tool" in action_data:
                current_tool = action_data["tool"]
                if current_tool in tool_aliases:
                    print(f"[DEBUG] Aliasing tool '{current_tool}' -> '{tool_aliases[current_tool]}'")
                    action_data["tool"] = tool_aliases[current_tool]
            
            return action_data
        except Exception as e:
            print(f"[DEBUG] Robust Parse failed: {e}")
            return None
            
    return None

def agent_loop():
    print("[INIT] Loading Personal Assistant Agent...")
    model, tokenizer = load_agent_model()
    
    tools_map = {
        "screenshot": screenshot,
        "launch_app": lambda p: launch_app(p.get("name")),
        "get_system_info": lambda p: get_system_info(p.get("metric", "all")),
        "type_text": lambda p: type_text(p.get("text")),
        "terminate_process": lambda p: terminate_process(p.get("name")),
        "delete_file": lambda p: delete_file(p.get("path")),
        "confirm_action": lambda p: confirm_action(p.get("action_id")),
        "control_media": lambda p: control_media(p.get("action"), p.get("app_hint")),
        "create_file": lambda p: create_file(p.get("name"), p.get("content", ""), p.get("append", False)),
        "create_folder": lambda p: create_folder(p.get("name")),
        "press_key": lambda p: press_key(p.get("key"))
    }

    print("[SPIDER-ARM] Ready! Waiting for input...")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        action = get_agent_response(model, tokenizer, user_input)
        
        if action and action.get("tool") in tools_map:
            tool_name = action["tool"]
            params = action.get("parameters", {})
            print(f"[SPIDER-ARM] Action: {tool_name}({params})")
            
            # Execute tool
            if tool_name == "screenshot":
                result = tools_map[tool_name]()
            else:
                result = tools_map[tool_name](params)
            
            print(f"[SYSTEM] Result: {result}")
        else:
            print("[SPIDER-ARM] I'm not sure how to help with that or no tool was called.")

if __name__ == "__main__":
    agent_loop()
