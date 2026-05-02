from unsloth import FastLanguageModel
import torch
import json
from controller.tools import (
    screenshot, launch_app, get_system_info, 
    type_text, terminate_process, delete_file, 
    confirm_action, control_media,
    create_file, create_folder, press_key, submit_text,
    hotkey, open_url, set_volume, lock_screen, sleep_pc, get_battery
)

import re

# This script handles the local AI inference using Unsloth 4-bit quantization.

def load_agent_model(model_path="qwen_assistant_lora"):
    import os
    if not os.path.exists(model_path):
        print(f"\n[CRITICAL ERROR] The AI Brain ({model_path}) was not found.")
        print("This usually happens on a fresh install. Please run 'python setup_wizard.py' to generate it.")
        import sys
        sys.exit(1)
        
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
5. type_text(text): Types keyboard input WITHOUT pressing Enter. Use ONLY when the user does NOT want to submit.
6. submit_text(text): Types text AND immediately presses Enter. Use when user says 'type X and press enter', 'search for X', 'type X and submit'.
7. press_key(key): Presses a single key. Keys: 'enter', 'space', 'tab', 'esc', 'backspace', 'delete'. Use for 'press enter', 'hit enter', 'press escape', etc.
8. terminate_process(name): Closes an app by name.
9. delete_file(path): Deletes a file (Requires approval).
10. confirm_action(action_id): Approves a pending action.
11. create_file(name, content, append): Creates/Overwrites a file. Set append=True to add text to the end.
12. create_folder(name): Creates a folder (Default: Desktop).
13. hotkey(keys): Presses a keyboard shortcut. Format: 'ctrl+c', 'alt+tab', 'win+d'. Use for copy/paste/undo/switch window.
14. open_url(url): Opens any URL in the default browser. Auto-adds https:// if missing.
15. set_volume(level): Sets system volume to exact percentage. level is a number 0-100.
16. lock_screen(): Locks the Windows PC immediately.
17. sleep_pc(): Puts PC to sleep (Requires approval — bridge will disconnect).
18. get_battery(): Returns battery percentage and charging status.

CRITICAL RULES:
- 'press enter' / 'hit enter' -> press_key(enter). NEVER use type_text for this.
- 'type X and press enter' / 'search for X' -> submit_text(X). One call, not two.
- 'type X' alone -> type_text(X).
- 'copy' / 'paste' / 'undo' / 'select all' / 'switch window' -> hotkey with the correct shortcut.
- 'open X.com' / 'go to URL' -> open_url, NOT launch_app.

EXAMPLES:
- "Type turtle" -> ### Thought: Type only, no submit. ### Action: {"tool": "type_text", "parameters": {"text": "turtle"}}
- "Type turtle and press enter" -> ### Thought: Type and submit compound action. Use submit_text. ### Action: {"tool": "submit_text", "parameters": {"text": "turtle"}}
- "Search for turtle" -> ### Thought: Search means type and submit. Use submit_text. ### Action: {"tool": "submit_text", "parameters": {"text": "turtle"}}
- "Press enter" -> ### Thought: Key press only, no typing. Use press_key. ### Action: {"tool": "press_key", "parameters": {"key": "enter"}}
- "Hit enter" -> ### Thought: Key press only. Use press_key. ### Action: {"tool": "press_key", "parameters": {"key": "enter"}}
- "Press escape" -> ### Thought: Single key press. ### Action: {"tool": "press_key", "parameters": {"key": "esc"}}
- "Copy that" -> ### Thought: Keyboard shortcut for copy. ### Action: {"tool": "hotkey", "parameters": {"keys": "ctrl+c"}}
- "Paste" -> ### Thought: Keyboard shortcut for paste. ### Action: {"tool": "hotkey", "parameters": {"keys": "ctrl+v"}}
- "Undo" -> ### Thought: Keyboard shortcut for undo. ### Action: {"tool": "hotkey", "parameters": {"keys": "ctrl+z"}}
- "Switch window" / "alt tab" -> ### Thought: Switch active window. ### Action: {"tool": "hotkey", "parameters": {"keys": "alt+tab"}}
- "Show desktop" -> ### Thought: Win+D shortcut. ### Action: {"tool": "hotkey", "parameters": {"keys": "win+d"}}
- "Open youtube.com" -> ### Thought: Open a URL in browser. ### Action: {"tool": "open_url", "parameters": {"url": "youtube.com"}}
- "Go to google" -> ### Thought: Open URL. ### Action: {"tool": "open_url", "parameters": {"url": "google.com"}}
- "Set volume to 40" -> ### Thought: Set exact volume level. ### Action: {"tool": "set_volume", "parameters": {"level": 40}}
- "Volume at 70 percent" -> ### Thought: Set exact volume. ### Action: {"tool": "set_volume", "parameters": {"level": 70}}
- "Lock my PC" / "lock screen" -> ### Thought: Lock workstation. ### Action: {"tool": "lock_screen", "parameters": {}}
- "Sleep" / "put PC to sleep" -> ### Thought: Sleep requires approval. ### Action: {"tool": "sleep_pc", "parameters": {}}
- "Check battery" / "battery level" -> ### Thought: Get battery info. ### Action: {"tool": "get_battery", "parameters": {}}
- "Create a note called hello.txt saying hi" -> ### Thought: Writing a file. ### Action: {"tool": "create_file", "parameters": {"name": "hello.txt", "content": "hi", "append": false}}
- "Add 'Remember to buy milk' to notes.txt" -> ### Thought: Appending to file. ### Action: {"tool": "create_file", "parameters": {"name": "notes.txt", "content": "Remember to buy milk", "append": true}}
- "Open spotify" -> ### Thought: Need to open music player. ### Action: {"tool": "launch_app", "parameters": {"name": "spotify"}}
- "Resume the music" -> ### Thought: Toggle play/pause. ### Action: {"tool": "control_media", "parameters": {"action": "play_pause", "app_hint": "spotify"}}
- "Next song" -> ### Thought: Skip to next track. ### Action: {"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}
- "Change the song" -> ### Thought: Change means skip to next. ### Action: {"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}
- "Skip this song" -> ### Thought: Skip to next track. ### Action: {"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}
- "Previous song" -> ### Thought: Go back to previous track. ### Action: {"tool": "control_media", "parameters": {"action": "previous", "app_hint": "spotify"}}
- "Volume up" -> ### Thought: Increase PC audio. ### Action: {"tool": "control_media", "parameters": {"action": "volume_up"}}
- "Silence the PC" -> ### Thought: Mute audio. ### Action: {"tool": "control_media", "parameters": {"action": "mute"}}
- "Check battery/heat" -> ### Thought: Telemetry check. ### Action: {"tool": "get_system_info", "parameters": {"metric": "all"}}
"""

def get_agent_response(model, tokenizer, instruction, history="", max_retries=2):
    """Generate a tool-call action from the model. Retries up to max_retries times on parse failure."""
    prompt = f"{SYSTEM_PROMPT}\n### Instruction:\n{instruction}\n\n### Thought:\n"
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    input_ids = inputs.input_ids

    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"[DEBUG] Retry {attempt}/{max_retries} for: '{instruction}'")

        # Use greedy decoding (do_sample=False) for maximum tool-calling precision
        outputs = model.generate(input_ids, max_new_tokens=256, use_cache=True, do_sample=False)

        # Only decode the NEW tokens (ignoring the prompt)
        generated_text = tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
        print(f"[DEBUG] Model Output (attempt {attempt+1}): {generated_text}")

        # --- FLEXIBLE PARSING LOGIC ---
        action_str = None

        # 1. Try strict Action header first
        if "### Action:" in generated_text:
            parts = generated_text.split("### Action:")
            action_section = parts[-1].strip()
            start = action_section.find("{")
            end = action_section.rfind("}") + 1
            if start != -1 and end > start:
                action_str = action_section[start:end]

        # 2. Fallback: search the whole response for any JSON block
        if not action_str:
            start = generated_text.find("{")
            end = generated_text.rfind("}") + 1
            if start != -1 and end > start:
                action_str = generated_text[start:end]

        if action_str:
            try:
                repaired_str = repair_json_string(action_str)
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
                    "open_app": "launch_app",
                    # Media tool name hallucinations
                    "play_music": "control_media",
                    "media_control": "control_media",
                    "music_control": "control_media",
                    "skip_song": "control_media",
                    "change_song": "control_media",
                }

                if "tool" in action_data:
                    current_tool = action_data["tool"]
                    if current_tool in tool_aliases:
                        print(f"[DEBUG] Aliasing tool '{current_tool}' -> '{tool_aliases[current_tool]}'")
                        action_data["tool"] = tool_aliases[current_tool]
                        # For media shim aliases, inject a sensible default action if missing
                        if action_data["tool"] == "control_media" and not action_data["parameters"].get("action"):
                            action_data["parameters"]["action"] = "next"

                return action_data

            except Exception as e:
                print(f"[DEBUG] Parse failed (attempt {attempt+1}): {e}")
                # Continue to retry

        else:
            print(f"[DEBUG] No JSON found in output (attempt {attempt+1}).")

    print("[DEBUG] All retry attempts exhausted. Could not parse action.")
    return None

def agent_loop():
    print("[INIT] Loading Personal Assistant Agent...")
    model, tokenizer = load_agent_model()
    
    tools_map = {
        "screenshot": screenshot,
        "launch_app": lambda p: launch_app(p.get("name")),
        "get_system_info": lambda p: get_system_info(p.get("metric", "all")),
        "type_text": lambda p: type_text(p.get("text")),
        "submit_text": lambda p: submit_text(p.get("text")),
        "terminate_process": lambda p: terminate_process(p.get("name")),
        "delete_file": lambda p: delete_file(p.get("path")),
        "confirm_action": lambda p: confirm_action(p.get("action_id")),
        "control_media": lambda p: control_media(p.get("action"), p.get("app_hint")),
        "create_file": lambda p: create_file(p.get("name"), p.get("content", ""), p.get("append", False)),
        "create_folder": lambda p: create_folder(p.get("name")),
        "press_key": lambda p: press_key(p.get("key")),
        "hotkey": lambda p: hotkey(p.get("keys", "")),
        "open_url": lambda p: open_url(p.get("url", "")),
        "set_volume": lambda p: set_volume(p.get("level", 50)),
        "lock_screen": lambda p: lock_screen(),
        "sleep_pc": lambda p: sleep_pc(),
        "get_battery": lambda p: get_battery(),
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
