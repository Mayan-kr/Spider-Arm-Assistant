import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import threading
import time
from controller.tools import (
    screenshot, launch_app, get_system_info, 
    type_text, terminate_process, delete_file, 
    confirm_action, control_media, create_file, create_folder,
    press_key, submit_text, hotkey, open_url, set_volume,
    lock_screen, sleep_pc, get_battery
)

# NOTE: The user will need to provide their own serviceAccountKey.json
# For now, we'll implement the logic to handle incoming requests.

import re

# Expand tool aliases to cover common model hallucinations
TOOL_ALIASES = {
    "get_system_telemetry": "get_system_info",
    "get_telemetry": "get_system_info",
    "capture_screenshot": "screenshot",
    "take_screenshot": "screenshot",
    "close_app": "terminate_process",
    "terminate_app": "terminate_process",
    "open_app": "launch_app",
    "play_music": "control_media",
    "media_control": "control_media",
    "music_control": "control_media",
    "skip_song": "control_media",
    "change_song": "control_media",
    "mute_audio": "control_media",
    "mute_sound": "control_media",
    "unmute": "control_media",
    "increase_volume": "control_media",
    "decrease_volume": "control_media",
    "raise_volume": "control_media",
    "lower_volume": "control_media",
    "boost_volume": "control_media",
    "open_file": "launch_app",
    "search_for": "submit_text",
    "search_text": "submit_text",
}

TOOLS_MAP = {
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

def start_heartbeat(db_client):
    """Updates the 'system_status' document every 30 seconds."""
    def heartbeat_loop():
        print("[SPIDER-ARM] Heartbeat pulse started.")
        while True:
            try:
                db_client.collection('system_status').document('agent').set({
                    'status': 'online',
                    'last_seen': firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"[DEBUG] Heartbeat error: {e}")
            time.sleep(30)
            
    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using the Unified Vault.
    Returns a Firestore client instance if successful, else None.
    """
    try:
        cred_path = "credentials.json"
        if not os.path.exists(cred_path):
            print(f"[ERROR] Unified Vault (credentials.json) not found. Run setup_wizard.py first.")
            return None
        
        with open(cred_path, "r") as f:
            vault = json.load(f)
            sa_data = vault.get("service_account")
        
        if not sa_data:
            print("[ERROR] Service Account data missing from vault.")
            return None

        cred = credentials.Certificate(sa_data)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"[ERROR] Failed to initialize Firebase: {e}")
        return None

def _apply_intent_intercepts(tool_name, params, instruction):
    """
    Catch predictable 1.5B model mis-mappings using explicit instruction parsing.
    Returns potentially modified (tool_name, params).
    """
    # 1. Volume relative intent: model calls set_volume(0) or set_volume(100)
    #    but user said something relative like "decrease the volume" (no number).
    #    If the instruction has no digit, the model guessed the extreme — redirect.
    if tool_name == "set_volume":
        level = params.get("level", 50)
        instr_lower = instruction.lower()
        has_explicit_number = bool(re.search(r'\d', instruction))
        relative_down = any(w in instr_lower for w in ("decrease", "reduce", "lower", "turn down", "quieter"))
        relative_up   = any(w in instr_lower for w in ("increase", "raise", "boost", "turn up", "louder"))
        if not has_explicit_number:
            if relative_down or level == 0:
                print("[INTERCEPT] set_volume(0) redirected → control_media(volume_down)")
                return "control_media", {"action": "volume_down"}
            elif relative_up or level == 100:
                print("[INTERCEPT] set_volume(100) redirected → control_media(volume_up)")
                return "control_media", {"action": "volume_up"}
        else:
            # Model heavily biased towards 40 and 70 from prompt examples.
            # Extract exact digit explicitly.
            match = re.search(r'\b(\d+)\b', instruction)
            if match:
                exact_level = int(match.group(1))
                if exact_level != level:
                    print(f"[INTERCEPT] Corrected set_volume level: {level} → {exact_level}")
                    params["level"] = exact_level

    # 2. Delete intent: model calls terminate_process when the user said "delete".
    #    Redirect to delete_file so files/folders are handled correctly.
    if tool_name == "terminate_process":
        instr_lower = instruction.lower()
        delete_verbs = ("delete", "remove", "erase", "wipe", "get rid of")
        if any(v in instr_lower for v in delete_verbs):
            name = params.get("name", "")
            print(f"[INTERCEPT] terminate_process('{name}') redirected → delete_file for delete intent")
            return "delete_file", {"path": name}
            
    # 3. Create File intent: 1.5B model heavily overfits to "Hello World" and "say goodbye".
    #    We extract the true filename and content directly from the user's prompt.
    if tool_name == "create_file":
        # Extract filename (e.g., ends in .txt, .py, etc)
        name_match = re.search(r'\b([\w-]+\.[a-zA-Z0-9]+)\b', instruction)
        if name_match:
            params["name"] = name_match.group(1)
            
        # Extract content
        quote_match = re.search(r'["\'](.*?)["\']', instruction)
        if quote_match:
            params["content"] = quote_match.group(1)
        else:
            m = re.search(r'\b(?:write|add|saying|say)\s+(.*?)$', instruction, re.IGNORECASE)
            if m:
                raw = m.group(1)
                raw = re.split(r'\s+(?:in|to|inside)\b', raw)[0]
                    params["content"] = raw.strip()
                    
        print(f"[INTERCEPT] create_file corrected to name='{params.get('name')}', content='{params.get('content')}'")

    # 4. URL Search intent: if the model tries to type/submit a domain name (e.g. "search weather.com"),
    #    redirect it to open the URL in a browser instead of blindly typing it.
    if tool_name == "submit_text":
        text = params.get("text", "").strip().lower()
        if any(text.endswith(tld) for tld in (".com", ".org", ".net", ".io", ".co", ".edu", ".gov", ".tv")) or text.startswith("http"):
            print(f"[INTERCEPT] submit_text('{text}') redirected → open_url")
            return "open_url", {"url": text}

    return tool_name, params

def process_command(command_data, instruction=""):
    """
    command_data: {
        "tool": "tool_name",
        "parameters": {...},
        "id": "optional_request_id"
    }
    instruction: original natural-language string from the user (used for intent intercepts)
    """
    tool_name = command_data.get("tool")
    params = command_data.get("parameters", {})
    
    if tool_name in TOOL_ALIASES:
        aliased = TOOL_ALIASES[tool_name]

        # Parameter shims
        if tool_name == "search_for" and "query" in params and "text" not in params:
            params["text"] = params["query"]

        # For media shim aliases that need a default action injected
        if aliased == "control_media" and not params.get("action"):
            if tool_name in ("mute_audio", "mute_sound"):
                params["action"] = "mute"
            elif tool_name == "unmute":
                params["action"] = "unmute"
            elif tool_name in ("increase_volume", "raise_volume", "boost_volume"):
                params["action"] = "volume_up"
            elif tool_name in ("decrease_volume", "lower_volume"):
                params["action"] = "volume_down"
            elif tool_name in ("play_music", "music_control"):
                params["action"] = "play_pause"
            else:
                params["action"] = "next"
        tool_name = aliased

    tool_name, params = _apply_intent_intercepts(tool_name, params, instruction)

    if tool_name in TOOLS_MAP:
        print(f"[AGENT] Executing {tool_name} with {params}")
        result = TOOLS_MAP[tool_name](params) if tool_name != "screenshot" else TOOLS_MAP[tool_name]()
        return result
    else:
        return {"status": "error", "message": f"Tool {tool_name} not found"}

def listen_for_remote_commands(db_client, model, tokenizer):
    if not db_client:
        return

    from inference import get_agent_response

    # Tracks IDs being processed — prevents duplicate execution when
    # Firestore MODIFIED events fire during our own status updates.
    _processing_ids = set()

    print("[SPIDER-ARM] Listening for commands in 'commands' collection...")

    def on_snapshot(col_snapshot, changes, read_time):
        print(f"[DEBUG] Received snapshot with {len(changes)} changes.")
        for change in changes:
            doc = change.document
            data = doc.to_dict()
            change_type = change.type.name if hasattr(change.type, 'name') else str(change.type)
            doc_id = doc.id
            current_status = str(data.get("status", "")).lower().strip()

            # Suppress console spam from initial Firestore sync of old documents
            if not (change_type == 'ADDED' and current_status in ['completed', 'error']):
                print(f"[DEBUG] Change detected! Type: {change_type} | ID: {doc_id} | Status: {current_status}")

            if change_type not in ['ADDED', 'MODIFIED']:
                continue

            # --- PENDING: Run inference and execute ---
            if current_status == "pending" and doc_id not in _processing_ids:
                _processing_ids.add(doc_id)
                instruction = data.get("instruction")
                print(f"[REMOTE] >>> Processing command: {instruction}")
                try:
                    doc.reference.update({"status": "processing"})
                    action = get_agent_response(model, tokenizer, instruction)
                    if action:
                        result = process_command(action, instruction=instruction)
                        if isinstance(result, dict) and result.get("status") == "request_confirmation":
                            doc.reference.update({
                                "status": "request_confirmation",
                                "action_id": result.get("action_id"),
                                "message": result.get("message", f"Spider-ARM wants to execute {action.get('tool')}. Approve?")
                            })
                            print(f"[SECURITY] Approval required for: {instruction}")
                        else:
                            doc.reference.update({
                                "status": "completed",
                                "result": result,
                                "executed_action": action
                            })
                            print(f"[SPIDER-ARM] √ Completed: {instruction}")
                    else:
                        print(f"[SPIDER-ARM] ! Model failed for: {instruction}")
                        doc.reference.update({
                            "status": "error",
                            "message": "Model could not determine an action"
                        })
                except Exception as e:
                    print(f"[ERROR] Execution error: {e}")
                    doc.reference.update({"status": "error", "message": str(e)})
                finally:
                    _processing_ids.discard(doc_id)  # Always release the ID

            # --- APPROVED: Execute held action after user taps Approve ---
            elif current_status == "approved":
                action_id = data.get("action_id")
                print(f"[SECURITY] >>> User APPROVED action: {action_id}")
                doc.reference.update({"status": "processing"})
                result = process_command({"tool": "confirm_action", "parameters": {"action_id": action_id}})
                doc.reference.update({"status": "completed", "result": result})
                print(f"[SPIDER-ARM] √ Confirmed action executed: {action_id}")

            # --- DENIED: Mark complete with denial message ---
            elif current_status == "denied":
                print("[SECURITY] >>> User DENIED action.")
                doc.reference.update({
                    "status": "completed",
                    "result": {"status": "error", "message": "User denied the security request."}
                })

    commands_ref = db_client.collection('commands')
    commands_ref.on_snapshot(on_snapshot)

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[FIREBASE] Listener stopped.")

if __name__ == "__main__":
    from inference import load_agent_model

    print("[INIT] Loading model for remote bridge...")
    model, tokenizer = load_agent_model()

    db_client = initialize_firebase()
    if db_client:
        start_heartbeat(db_client)
        listen_for_remote_commands(db_client, model, tokenizer)
    else:
        print("[ERROR] Could not start bridge without Firebase credentials.")
