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
    press_key
)

# NOTE: The user will need to provide their own serviceAccountKey.json
# For now, we'll implement the logic to handle incoming requests.

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

def process_command(command_data):
    """
    command_data: {
        "tool": "tool_name",
        "parameters": {...},
        "id": "optional_request_id"
    }
    """
    tool_name = command_data.get("tool")
    params = command_data.get("parameters", {})
    
    # 1. Aliasing (Normalize tool names)
    tool_aliases = {
        "get_system_telemetry": "get_system_info",
        "get_telemetry": "get_system_info",
        "capture_screenshot": "screenshot",
        "take_screenshot": "screenshot",
        "close_app": "terminate_process",
        "open_app": "launch_app"
    }
    if tool_name in tool_aliases:
        tool_name = tool_aliases[tool_name]

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
    
    if tool_name in tools_map:
        print(f"[AGENT] Executing {tool_name} with {params}")
        result = tools_map[tool_name](params) if tool_name != "screenshot" else tools_map[tool_name]()
        return result
    else:
        return {"status": "error", "message": f"Tool {tool_name} not found"}

def listen_for_remote_commands(db_client, model, tokenizer):
    if not db_client:
        return
    
    from inference import get_agent_response
    
    print("[SPIDER-ARM] Listening for commands in 'commands' collection...")
    
    def on_snapshot(col_snapshot, changes, read_time):
        print(f"[DEBUG] Received snapshot with {len(changes)} changes.")
        for change in changes:
            doc = change.document
            data = doc.to_dict()
            change_type = change.type.name if hasattr(change.type, 'name') else str(change.type)
            
            print(f"[DEBUG] Change detected! Type: {change_type} | ID: {doc.id} | Status: {data.get('status')}")
            
            # We process both ADDED and MODIFIED to ensure we catch everything
            if change_type in ['ADDED', 'MODIFIED']:
                # Ensure status is exactly 'pending' (check for case and whitespace)
                current_status = str(data.get("status", "")).lower().strip()
                
                if current_status == "pending":
                    instruction = data.get("instruction")
                    print(f"[REMOTE] >>> Processing command: {instruction}")
                    
                    try:
                        # 1. Update status to 'processing'
                        doc.reference.update({"status": "processing"})
                        
                        # 2. Run Inference
                        action = get_agent_response(model, tokenizer, instruction)
                        
                        if action:
                            # 3. Execute Tool
                            result = process_command(action)
                            
                            # 4. Handle Security Approvals vs Completion
                            if isinstance(result, dict) and result.get("status") == "request_confirmation":
                                doc.reference.update({
                                    "status": "request_confirmation",
                                    "action_id": result.get("action_id"), # Critical for confirmation
                                    "message": result.get("message", f"Spider-ARM wants to execute {action.get('tool')}. Do you approve?")
                                })
                                print(f"[SECURITY] Approval required for: {instruction}")
                            else:
                                doc.reference.update({
                                    "status": "completed",
                                    "result": result,
                                    "executed_action": action
                                })
                                print(f"[SPIDER-ARM] √ Successfully completed: {instruction}")
                        else:
                            print(f"[SPIDER-ARM] ! Model failed to determine action for: {instruction}")
                            doc.reference.update({
                                "status": "error",
                                "message": "Model could not determine an action"
                            })
                    except Exception as e:
                        print(f"[ERROR] Logic error during execution: {e}")
                        doc.reference.update({"status": "error", "message": str(e)})

                elif current_status == "approved":
                    action_id = data.get("action_id")
                    print(f"[SECURITY] >>> User APPROVED action: {action_id}")
                    doc.reference.update({"status": "processing"})
                    
                    # Execute the confirmed action
                    result = process_command({"tool": "confirm_action", "parameters": {"action_id": action_id}})
                    
                    doc.reference.update({
                        "status": "completed",
                        "result": result
                    })
                    print(f"[SPIDER-ARM] √ Confirmed action executed: {action_id}")

                elif current_status == "denied":
                    print(f"[SECURITY] >>> User DENIED action.")
                    doc.reference.update({
                        "status": "completed",
                        "result": {"status": "error", "message": "User denied the security request."}
                    })
    
    # Watch the 'commands' collection
    commands_ref = db_client.collection('commands')
    commands_ref.on_snapshot(on_snapshot)
    
    # Keep the script alive
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
