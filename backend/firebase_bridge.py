import firebase_admin
from firebase_admin import credentials, firestore, db
import os
import json
from controller.tools import (
    screenshot, launch_app, get_system_info, 
    type_text, terminate_process, delete_file, confirm_action
)

# NOTE: The user will need to provide their own serviceAccountKey.json
# For now, we'll implement the logic to handle incoming requests.

def initialize_firebase():
    try:
        cred_path = os.getenv("FIREBASE_CRED_PATH", "serviceAccountKey.json")
        if not os.path.exists(cred_path):
            print(f"[ERROR] Firebase credentials not found at {cred_path}. Skipping real-time features.")
            return None
        
        cred = credentials.Certificate(cred_path)
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
    
    tools_map = {
        "screenshot": screenshot,
        "launch_app": lambda p: launch_app(p.get("name")),
        "get_system_info": lambda p: get_system_info(p.get("metric", "all")),
        "type_text": lambda p: type_text(p.get("text")),
        "terminate_process": lambda p: terminate_process(p.get("name")),
        "delete_file": lambda p: delete_file(p.get("path")),
        "confirm_action": lambda p: confirm_action(p.get("action_id"))
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
    
    print("[FIREBASE] Listening for commands in 'commands' collection...")
    
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
                            
                            # 4. Update with result
                            doc.reference.update({
                                "status": "completed",
                                "result": result,
                                "executed_action": action
                            })
                            print(f"[REMOTE] √ Successfully completed: {instruction}")
                        else:
                            print(f"[REMOTE] ! Model failed to determine action for: {instruction}")
                            doc.reference.update({
                                "status": "error",
                                "message": "Model could not determine an action"
                            })
                    except Exception as e:
                        print(f"[ERROR] Logic error during execution: {e}")
                        doc.reference.update({"status": "error", "message": str(e)})
    
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
        listen_for_remote_commands(db_client, model, tokenizer)
    else:
        print("[ERROR] Could not start bridge without Firebase credentials.")
