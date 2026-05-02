import os
import pyautogui
import psutil
import platform
import subprocess
import glob
import shutil
from functools import wraps

# Common Windows App Aliases
APP_ALIASES = {
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "editor": "notepad",
    "chrome": "chrome",
    "browser": "brave",
    "brave": "brave",
    "settings": "ms-settings:",
    "terminal": "wt",
    "command prompt": "cmd",
    "task manager": "taskmgr"
}

# Optional hardware/window libraries
try:
    import GPUtil
except ImportError:
    GPUtil = None
try:
    import wmi
except ImportError:
    wmi = None
try:
    import pygetwindow as gw
except ImportError:
    gw = None

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
            # 1. Alias Resolution
            target = APP_ALIASES.get(name.lower(), name)

            # 2. Search for Shortcuts (Brave Apps, Desktop, etc) - PRIORITY
            search_paths = [
                os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Brave Apps"),
                os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Chrome Apps"),
                os.path.join(os.environ["USERPROFILE"], "Desktop"),
                os.path.join(os.environ["USERPROFILE"], "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs")
            ]
            
            for path in search_paths:
                if os.path.exists(path):
                    # Try exact match or starting with
                    pattern = os.path.join(path, f"*{target}*.lnk")
                    matches = glob.glob(pattern)
                    if matches:
                        os.startfile(matches[0])
                        return {"status": "success", "message": f"Launched shortcut: {os.path.basename(matches[0])}"}

            # 3. Check if it's a known system command (avoiding the shell popup)
            if shutil.which(target) or target.startswith("ms-settings:"):
                subprocess.Popen(["start", target], shell=True)
                return {"status": "success", "message": f"Launched system app: {target}"}

            return {"status": "error", "message": f"Could not find app or shortcut for '{name}'"}

        # Fallback for non-Windows
        subprocess.Popen([name])
        return {"status": "success", "message": f"Launched {name}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

def get_system_info(metric="all"):
    try:
        info = {}
        if metric in ["cpu", "all"]:
            info["cpu_usage"] = f"{psutil.cpu_percent()}%"
        if metric in ["mem", "all"]:
            info["memory_usage"] = f"{psutil.virtual_memory().percent}%"
        if metric in ["disk", "all"]:
            info["disk_usage"] = f"{psutil.disk_usage('/').percent}%"
        
        # Safe Temp/Heat checks (highly prone to hardware/permission errors)
        if metric in ["temp", "heat", "all"]:
            # GPU (NVIDIA)
            if GPUtil:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        info["gpu_temp"] = f"{gpus[0].temperature}°C"
                except: pass
            # CPU
            if wmi:
                try:
                    w = wmi.WMI(namespace="root\\wmi")
                    temps = w.MSAcpi_ThermalZoneTemperature()
                    if temps:
                        celsius = (temps[0].CurrentTemperature / 10.0) - 273.15
                        info["cpu_temp"] = f"{round(celsius, 1)}°C"
                except: pass

        return {"status": "success", "data": info}
    except Exception as e:
        return {"status": "error", "message": f"Telemetry failed: {str(e)}"}

def control_media(action, app_hint=None):
    try:
        import time
        # 1. Provide Focus (Crucial for suspended/minimized apps)
        focus_msg = ""
        if gw and app_hint:
            try:
                # Fuzzy search across all windows
                target_win = None
                all_wins = gw.getAllWindows()
                for w in all_wins:
                    if app_hint.lower() in w.title.lower():
                        target_win = w
                        break
                
                if target_win:
                    if target_win.isMinimized:
                        target_win.restore()
                        time.sleep(0.5) # Wait for "Repaint/Wake up"
                    
                    target_win.activate()
                    time.sleep(0.2)
                    focus_msg = f"Resurrected '{target_win.title}'. "
            except Exception as fe:
                focus_msg = f"(Wake-up failed: {str(fe)}) "

        # 2. Key Mapping (Standardize Resume to PlayPause)
        mapping = {
            "play": "playpause",
            "play_song": "playpause",
            "play_music": "playpause",
            "pause": "playpause",
            "resume": "playpause",
            "play_pause": "playpause",
            "next": "nexttrack",
            "next_song": "nexttrack",
            "change": "nexttrack",
            "change_song": "nexttrack",
            "skip": "nexttrack",
            "skip_song": "nexttrack",
            "previous": "prevtrack",
            "back": "prevtrack",
            "volume_up": "volumeup",
            "volume_down": "volumedown",
            "mute": "volumemute"
        }
        
        key = mapping.get(action.lower())
        if key:
            if "volume" in key:
                # Boost volume steps: 5 presses = ~10% change for snappier control
                for _ in range(5):
                    pyautogui.press(key)
            else:
                pyautogui.press(key)
            return {"status": "success", "message": f"{focus_msg}Media action: {action}"}
        else:
            return {"status": "error", "message": f"Unknown media action: {action}"}
    except Exception as e:
        return {"status": "error", "message": f"Media control failed: {str(e)}"}

def type_text(text):
    pyautogui.write(text, interval=0.1)
    return {"status": "success", "message": f"Typed: {text}"}

def press_key(key):
    pyautogui.press(key)
    return {"status": "success", "message": f"Pressed key: {key}"}

def submit_text(text):
    """Types text and immediately presses Enter — for search boxes, chat inputs, etc."""
    import time
    pyautogui.write(text, interval=0.1)
    time.sleep(0.1)  # Brief pause so the keystroke registers before Enter
    pyautogui.press("enter")
    return {"status": "success", "message": f"Typed and submitted: {text}"}

# Hotkey combos that are destructive and require explicit approval before executing
_DESTRUCTIVE_HOTKEYS = {
    frozenset(["alt", "f4"]),           # Close active window
    frozenset(["ctrl", "w"]),            # Close active tab/window
    frozenset(["ctrl", "alt", "del"]),   # System interrupt
    frozenset(["ctrl", "shift", "esc"]), # Task Manager (can kill processes)
    frozenset(["win", "l"]),             # Lock screen (handled by lock_screen tool, avoid double-trigger)
    frozenset(["alt", "f4"]),            # Close window
    frozenset(["ctrl", "alt", "delete"]),
}

def hotkey(keys):
    """Press a keyboard shortcut. keys: '+'-separated, e.g. 'ctrl+c', 'alt+tab', 'win+d'.
    Destructive combos (alt+f4, ctrl+w, ctrl+alt+del, win+l) require phone approval first.
    """
    try:
        normalized = keys.lower().strip().replace(' ', '+')
        key_list = [k.strip() for k in normalized.split('+') if k.strip()]
        # Common word aliases to pyautogui key names
        key_map = {
            'control': 'ctrl',
            'windows': 'win',
            'escape': 'esc',
            'delete': 'del',
            'return': 'enter',
        }
        key_list = [key_map.get(k, k) for k in key_list]

        # Block destructive hotkey combos — route through approval flow
        key_set = frozenset(key_list)
        if key_set in _DESTRUCTIVE_HOTKEYS:
            return _hotkey_confirmed(keys, key_list)

        pyautogui.hotkey(*key_list)
        return {"status": "success", "message": f"Hotkey: {'+'.join(key_list)}"}
    except Exception as e:
        return {"status": "error", "message": f"Hotkey failed: {str(e)}"}

@requires_confirmation
def _hotkey_confirmed(original_keys, key_list):
    """Executes a destructive hotkey after explicit user approval."""
    pyautogui.hotkey(*key_list)
    return {"status": "success", "message": f"Destructive hotkey executed: {original_keys}"}

def open_url(url):
    """Open a URL in the default browser. Adds https:// automatically if missing."""
    import webbrowser
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    webbrowser.open(url)
    return {"status": "success", "message": f"Opened: {url}"}

def set_volume(level):
    """Set system master volume to an exact percentage (0-100)."""
    try:
        level = max(0, min(100, int(level)))
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return {"status": "success", "message": f"Volume set to {level}%"}
        except ImportError:
            return {"status": "error", "message": "pycaw not installed. Run: pip install pycaw"}
    except Exception as e:
        return {"status": "error", "message": f"Volume control failed: {str(e)}"}

def lock_screen():
    """Locks the Windows workstation immediately."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return {"status": "success", "message": "Screen locked"}
    except Exception as e:
        return {"status": "error", "message": f"Lock failed: {str(e)}"}

@requires_confirmation
def sleep_pc():
    """Puts the PC to sleep. WARNING: This will terminate the bridge connection."""
    subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    return {"status": "success", "message": "PC going to sleep"}

def get_battery():
    """Returns battery percentage and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {"status": "error", "message": "No battery detected (desktop PC)"}
        status = "Charging" if battery.power_plugged else "Discharging"
        secs = battery.secsleft
        if secs in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN) or secs < 0:
            time_left = "N/A"
        else:
            time_left = f"{secs // 3600}h {(secs % 3600) // 60}m"
        return {"status": "success", "data": {
            "percent": f"{battery.percent:.0f}%",
            "status": status,
            "time_left": time_left
        }}
    except Exception as e:
        return {"status": "error", "message": f"Battery check failed: {str(e)}"}

@requires_confirmation
def terminate_process(name):
    """Force-closes all processes matching name. Requires approval since unsaved work may be lost."""
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

@requires_confirmation
def create_file(name, content="", append=False):
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    # If name is just a filename, put it on desktop. Otherwise treat as path.
    path = name if os.path.isabs(name) else os.path.join(desktop, name)
    
    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        # If appending, add a newline first
        if append and os.path.exists(path):
            f.write("\n")
        f.write(content)
    return {"status": "success", "message": f"File {'appended' if append else 'created'} at {path}"}

@requires_confirmation
def create_folder(name):
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    path = name if os.path.isabs(name) else os.path.join(desktop, name)
    
    os.makedirs(path, exist_ok=True)
    return {"status": "success", "message": f"Folder created at {path}"}

# Helper to execute a pending action after approval
def confirm_action(action_id):
    if action_id in pending_actions:
        action = pending_actions.pop(action_id)
        return action["func"](*action["args"], **action["kwargs"])
    return {"status": "error", "message": "Invalid action ID"}
