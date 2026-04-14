from unsloth import FastLanguageModel
import torch
import json
from controller.tools import (
    screenshot, launch_app, get_system_info, 
    type_text, terminate_process, delete_file, 
    confirm_action, control_media
)

import re

# NOTE: TurboQuant is a training-free KV cache compression technique.
# In a real-world integration, you'd wrap the model's attention layers.
# Here we simulate the inference optimized for context.

def load_agent_model(model_path="qwen_assistant_lora"):
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_path,
        max_seq_length = 2048,
        load_in_4bit = True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def repair_json_string(s):
    """Common fixes for small model JSON hallucinations"""
    # Fix missing "parameters" key: {"tool": "name", {}} -> {"tool": "name", "parameters": {}}
    s = re.sub(r'\",\s*{', '", "parameters": {', s)
    s = re.sub(r'\',\s*{', '", "parameters": {', s)
    
    # Ensure balanced braces
    if s.count('{') > s.count('}'):
        s += '}' * (s.count('{') - s.count('}'))
    
    # Clean up any trailing text after the last brace
    last_brace = s.rfind('}')
    if last_brace != -1:
        s = s[:last_brace+1]
        
    return s

def get_agent_response(model, tokenizer, instruction, history=""):
    # Clearer formatting hint for the model
    format_hint = ' (Format: {"tool": "name", "parameters": {}})'
    prompt = f"### Instruction:\n{instruction}{format_hint}\n\n### Thought:\n"
    inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
    
    outputs = model.generate(**inputs, max_new_tokens = 256, use_cache = True)
    response = tokenizer.batch_decode(outputs)[0]
    
    # DEBUG: Print raw response to see what's happening
    print(f"--- DEBUG RAW RESPONSE ---\n{response}\n--------------------------")

    # Clean special tokens and whitespace
    clean_response = response.replace("<|endoftext|>", "").strip()
    
    # Extract Action from response
    if "### Action:" in clean_response:
        try:
            # We split and take everything after the LAST '### Action:' if multiple exist
            parts = clean_response.split("### Action:")
            action_section = parts[-1].strip()
            
            # Find the first JSON-like block
            start = action_section.find("{")
            end = action_section.rfind("}") + 1
            
            if start != -1 and end != -1:
                action_str = action_section[start:end]
                print(f"[DEBUG] Raw JSON extracted: {action_str}")
                
                # Apply SMART REPAIR
                repaired_str = repair_json_string(action_str)
                if repaired_str != action_str:
                    print(f"[DEBUG] Smart Repaired JSON: {repaired_str}")
                
                action_data = json.loads(repaired_str)
                
                # Normalize keys: accept 'args', 'params', or 'parameters'
                params = action_data.get("parameters") or action_data.get("args") or action_data.get("params") or {}
                action_data["parameters"] = params
                
                # Standardize tool names (Aliasing)
                tool_aliases = {
                    "get_system_telemetry": "get_system_info",
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
            print(f"[DEBUG] Parse error: {e}")
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
        "control_media": lambda p: control_media(p.get("action"), p.get("app_hint"))
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
