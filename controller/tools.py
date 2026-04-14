import os
import pyautogui
import psutil
import platform
import subprocess
from functools import wraps

# State for the confirmation logic
pending_actions = {}

def requires_confirmation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # We generate a unique ID for this pending action
        action_id = f"act_{len(pending_actions) + 1}"
        entry = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "status": "pending_approval",
            "action_name": func.__name__
        }
        pending_actions[action_id] = entry
        
        # In a real environment with Firebase, we would write this to a 'requests' collection
        # For now, we print it so the bridge/agent knows it needs approval.
        print(f"[SAFETY] Action '{func.__name__}' blocked. Waiting for approval of ID: {action_id}")
        
        return {
            "status": "request_confirmation", 
            "action_id": action_id, 
            "message": f"Security: Approval required for {func.__name__}"
        }
    return wrapper

def screenshot():
    os.makedirs("outputs", exist_ok=True)
    path = "outputs/screenshot.png"
    pyautogui.screenshot(path)
    return {"status": "success", "message": f"Screenshot saved to {path}"}

def launch_app(name):
    try:
        if platform.system() == "Windows":
            # Simple start command for Windows
            subprocess.Popen(["start", name], shell=True)
        else:
            # Fallback for other OS (if applicable)
            subprocess.Popen([name])
        return {"status": "success", "message": f"Launched {name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_system_info(metric="all"):
    info = {}
    if metric in ["cpu", "all"]:
        info["cpu_usage"] = f"{psutil.cpu_percent()}%"
    if metric in ["mem", "all"]:
        info["memory_usage"] = f"{psutil.virtual_memory().percent}%"
    if metric in ["disk", "all"]:
        info["disk_usage"] = f"{psutil.disk_usage('/').percent}%"
    return {"status": "success", "data": info}

def type_text(text):
    pyautogui.write(text, interval=0.1)
    return {"status": "success", "message": f"Typed: {text}"}

def terminate_process(name):
    count = 0
    for proc in psutil.process_iter(['name']):
        if name.lower() in proc.info['name'].lower():
            proc.terminate()
            count += 1
    return {"status": "success", "message": f"Terminated {count} process(es) matching {name}"}

@requires_confirmation
def delete_file(path):
    if os.path.exists(path):
        os.remove(path)
        return {"status": "success", "message": f"Deleted {path}"}
    else:
        return {"status": "error", "message": "File not found"}

# Helper to execute a pending action after approval
def confirm_action(action_id):
    if action_id in pending_actions:
        action = pending_actions.pop(action_id)
        return action["func"](*action["args"], **action["kwargs"])
    return {"status": "error", "message": "Invalid action ID"}
