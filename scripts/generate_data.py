import json
import os

def generate_dataset():
    dataset = [
        # ── SCREENSHOT ──────────────────────────────────────────────────────────
        {
            "instruction": "Capture the current screen and save it.",
            "thought": "The user wants a screenshot. I should call the screenshot tool.",
            "action": '{"tool": "screenshot", "parameters": {}}'
        },
        {
            "instruction": "Take a screenshot.",
            "thought": "User wants to capture the screen.",
            "action": '{"tool": "screenshot", "parameters": {}}'
        },
        {
            "instruction": "Take a screenshot and tell me if my browser is open.",
            "thought": "I need to capture the screen to see its current state.",
            "action": '{"tool": "screenshot", "parameters": {}}'
        },

        # ── LAUNCH APP ──────────────────────────────────────────────────────────
        {
            "instruction": "Open the calculator app.",
            "thought": "The user wants to open the calculator. I'll use the launch_app tool.",
            "action": '{"tool": "launch_app", "parameters": {"name": "calculator"}}'
        },
        {
            "instruction": "Play some relaxing music.",
            "thought": "The user wants music. I should open Spotify.",
            "action": '{"tool": "launch_app", "parameters": {"name": "spotify"}}'
        },
        {
            "instruction": "Launch Chrome and go to google.com",
            "thought": "I will launch Chrome first. The URL will be handled separately.",
            "action": '{"tool": "launch_app", "parameters": {"name": "chrome"}}'
        },
        {
            "instruction": "Open Notepad.",
            "thought": "User wants the text editor.",
            "action": '{"tool": "launch_app", "parameters": {"name": "notepad"}}'
        },
        {
            "instruction": "Open the browser.",
            "thought": "User wants to open the default browser (Brave).",
            "action": '{"tool": "launch_app", "parameters": {"name": "browser"}}'
        },

        # ── GET SYSTEM INFO ─────────────────────────────────────────────────────
        {
            "instruction": "What is the current CPU usage?",
            "thought": "I need to fetch CPU telemetry.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "cpu"}}'
        },
        {
            "instruction": "What is my current disk usage?",
            "thought": "I will check disk telemetry.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "disk"}}'
        },
        {
            "instruction": "Are there any high-memory processes running?",
            "thought": "I should check the system memory usage.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "mem"}}'
        },
        {
            "instruction": "Give me a full summary of my PC health.",
            "thought": "I'll fetch all system metrics for a complete summary.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "all"}}'
        },
        {
            "instruction": "Check my GPU temperature.",
            "thought": "User wants thermal data. I'll get all metrics including temp.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "temp"}}'
        },
        {
            "instruction": "Is my PC running hot?",
            "thought": "User wants temperature info. Use metric=temp.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "temp"}}'
        },

        # ── TERMINATE PROCESS ───────────────────────────────────────────────────
        {
            "instruction": "Close all Chrome windows.",
            "thought": "I should terminate the chrome process.",
            "action": '{"tool": "terminate_process", "parameters": {"name": "chrome"}}'
        },
        {
            "instruction": "Close Notepad immediately.",
            "thought": "I need to terminate the notepad process.",
            "action": '{"tool": "terminate_process", "parameters": {"name": "notepad"}}'
        },
        {
            "instruction": "Stop all Python processes.",
            "thought": "I'll terminate all python.exe instances.",
            "action": '{"tool": "terminate_process", "parameters": {"name": "python"}}'
        },

        # ── DELETE FILE ─────────────────────────────────────────────────────────
        {
            "instruction": "Delete the old log file in downloads.",
            "thought": "Deleting a file is a sensitive action requiring confirmation.",
            "action": '{"tool": "delete_file", "parameters": {"path": "C:/Users/kumar/Downloads/old_log.txt"}}'
        },
        {
            "instruction": "Delete the file test.txt from C:\\temp.",
            "thought": "Deleting a file requires user confirmation via the safety handshake.",
            "action": '{"tool": "delete_file", "parameters": {"path": "C:\\\\temp\\\\test.txt"}}'
        },

        # ── CREATE FILE ─────────────────────────────────────────────────────────
        {
            "instruction": "Create a note on my Desktop called todo.txt saying Buy milk.",
            "thought": "The user wants to create a file. I'll use create_file.",
            "action": '{"tool": "create_file", "parameters": {"name": "todo.txt", "content": "Buy milk", "append": false}}'
        },
        {
            "instruction": "Add Remember to buy milk to notes.txt.",
            "thought": "The user wants to append text to an existing file.",
            "action": '{"tool": "create_file", "parameters": {"name": "notes.txt", "content": "Remember to buy milk", "append": true}}'
        },
        {
            "instruction": "Write Done for today to work.txt.",
            "thought": "User wants to create/overwrite a file with content.",
            "action": '{"tool": "create_file", "parameters": {"name": "work.txt", "content": "Done for today", "append": false}}'
        },

        # ── TYPE TEXT ───────────────────────────────────────────────────────────
        {
            "instruction": "Type Hello World in the active window.",
            "thought": "User wants to type text without pressing enter.",
            "action": '{"tool": "type_text", "parameters": {"text": "Hello World"}}'
        },
        {
            "instruction": "Type my name is Spider-Arm.",
            "thought": "User wants to type text only, no submission needed.",
            "action": '{"tool": "type_text", "parameters": {"text": "my name is Spider-Arm"}}'
        },

        # ── SUBMIT TEXT ─────────────────────────────────────────────────────────
        {
            "instruction": "Type turtle and press enter.",
            "thought": "User wants to type text AND submit it. I must use submit_text, not two separate calls.",
            "action": '{"tool": "submit_text", "parameters": {"text": "turtle"}}'
        },
        {
            "instruction": "Search for lo-fi music on YouTube.",
            "thought": "Search means type and submit. Use submit_text.",
            "action": '{"tool": "submit_text", "parameters": {"text": "lo-fi music"}}'
        },
        {
            "instruction": "Type spider arm and submit.",
            "thought": "User wants to type and submit. Use submit_text.",
            "action": '{"tool": "submit_text", "parameters": {"text": "spider arm"}}'
        },

        # ── PRESS KEY ───────────────────────────────────────────────────────────
        {
            "instruction": "Press enter.",
            "thought": "User wants a single key press. Use press_key. Do NOT use type_text.",
            "action": '{"tool": "press_key", "parameters": {"key": "enter"}}'
        },
        {
            "instruction": "Hit enter.",
            "thought": "User wants to press the enter key. Use press_key.",
            "action": '{"tool": "press_key", "parameters": {"key": "enter"}}'
        },
        {
            "instruction": "Press escape.",
            "thought": "User wants to press the escape key.",
            "action": '{"tool": "press_key", "parameters": {"key": "esc"}}'
        },
        {
            "instruction": "Press the space bar.",
            "thought": "User wants to press space.",
            "action": '{"tool": "press_key", "parameters": {"key": "space"}}'
        },
        {
            "instruction": "Press tab.",
            "thought": "User wants to press the tab key.",
            "action": '{"tool": "press_key", "parameters": {"key": "tab"}}'
        },

        # ── HOTKEY ──────────────────────────────────────────────────────────────
        {
            "instruction": "Copy that.",
            "thought": "User wants to copy. The keyboard shortcut is Ctrl+C.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "ctrl+c"}}'
        },
        {
            "instruction": "Paste it.",
            "thought": "User wants to paste. The keyboard shortcut is Ctrl+V.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "ctrl+v"}}'
        },
        {
            "instruction": "Undo that.",
            "thought": "User wants to undo the last action. Shortcut is Ctrl+Z.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "ctrl+z"}}'
        },
        {
            "instruction": "Select all.",
            "thought": "User wants to select all text. Shortcut is Ctrl+A.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "ctrl+a"}}'
        },
        {
            "instruction": "Save the file.",
            "thought": "User wants to save. Shortcut is Ctrl+S.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "ctrl+s"}}'
        },
        {
            "instruction": "Switch window.",
            "thought": "User wants to switch the active window. Alt+Tab is the shortcut.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "alt+tab"}}'
        },
        {
            "instruction": "Alt tab.",
            "thought": "User wants to switch windows using Alt+Tab.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "alt+tab"}}'
        },
        {
            "instruction": "Show the desktop.",
            "thought": "User wants to show the desktop. Win+D is the shortcut.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "win+d"}}'
        },
        {
            "instruction": "Minimize all windows.",
            "thought": "User wants to minimize everything. Win+D shows the desktop.",
            "action": '{"tool": "hotkey", "parameters": {"keys": "win+d"}}'
        },

        # ── OPEN URL ─────────────────────────────────────────────────────────────
        {
            "instruction": "Open youtube.com.",
            "thought": "User wants to open a URL in the browser. Use open_url.",
            "action": '{"tool": "open_url", "parameters": {"url": "youtube.com"}}'
        },
        {
            "instruction": "Go to google.com.",
            "thought": "User wants to navigate to Google. Use open_url.",
            "action": '{"tool": "open_url", "parameters": {"url": "google.com"}}'
        },
        {
            "instruction": "Open my GitHub profile.",
            "thought": "User wants to open a URL. Use open_url.",
            "action": '{"tool": "open_url", "parameters": {"url": "github.com"}}'
        },
        {
            "instruction": "Navigate to reddit.com.",
            "thought": "User wants to go to a website. Use open_url.",
            "action": '{"tool": "open_url", "parameters": {"url": "reddit.com"}}'
        },

        # ── SET VOLUME ───────────────────────────────────────────────────────────
        {
            "instruction": "Set volume to 40.",
            "thought": "User wants exact volume level. Use set_volume with level 40.",
            "action": '{"tool": "set_volume", "parameters": {"level": 40}}'
        },
        {
            "instruction": "Set volume to 70 percent.",
            "thought": "User wants volume at 70%. Use set_volume.",
            "action": '{"tool": "set_volume", "parameters": {"level": 70}}'
        },
        {
            "instruction": "Lower volume to 20.",
            "thought": "User wants exact volume level 20. Use set_volume.",
            "action": '{"tool": "set_volume", "parameters": {"level": 20}}'
        },
        {
            "instruction": "Max out the volume.",
            "thought": "User wants full volume. Use set_volume with level 100.",
            "action": '{"tool": "set_volume", "parameters": {"level": 100}}'
        },

        # ── LOCK SCREEN ──────────────────────────────────────────────────────────
        {
            "instruction": "Lock my PC.",
            "thought": "User wants to lock the workstation immediately.",
            "action": '{"tool": "lock_screen", "parameters": {}}'
        },
        {
            "instruction": "Lock the screen.",
            "thought": "User wants to lock the screen. Use lock_screen.",
            "action": '{"tool": "lock_screen", "parameters": {}}'
        },
        {
            "instruction": "I am stepping away, lock the computer.",
            "thought": "User wants to lock the workstation before leaving.",
            "action": '{"tool": "lock_screen", "parameters": {}}'
        },

        # ── SLEEP PC ─────────────────────────────────────────────────────────────
        {
            "instruction": "Put the PC to sleep.",
            "thought": "User wants to sleep the PC. This requires confirmation as it disconnects the bridge.",
            "action": '{"tool": "sleep_pc", "parameters": {}}'
        },
        {
            "instruction": "Sleep.",
            "thought": "User wants the PC to go to sleep. Use sleep_pc.",
            "action": '{"tool": "sleep_pc", "parameters": {}}'
        },

        # ── GET BATTERY ──────────────────────────────────────────────────────────
        {
            "instruction": "Check the battery.",
            "thought": "User wants battery status. Use get_battery.",
            "action": '{"tool": "get_battery", "parameters": {}}'
        },
        {
            "instruction": "How much battery is left?",
            "thought": "User wants battery percentage. Use get_battery.",
            "action": '{"tool": "get_battery", "parameters": {}}'
        },
        {
            "instruction": "Is my laptop charging?",
            "thought": "User wants charging status. Use get_battery.",
            "action": '{"tool": "get_battery", "parameters": {}}'
        },

        # ── CONTROL MEDIA ────────────────────────────────────────────────────────
        {
            "instruction": "Resume the music.",
            "thought": "User wants to play/resume music. Use control_media with play_pause.",
            "action": '{"tool": "control_media", "parameters": {"action": "play_pause", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Pause the music.",
            "thought": "User wants to pause. Use control_media with play_pause.",
            "action": '{"tool": "control_media", "parameters": {"action": "play_pause", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Next song.",
            "thought": "User wants to skip to the next track.",
            "action": '{"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Change the song.",
            "thought": "Change means skip to the next track. Use control_media with action next.",
            "action": '{"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Skip this song.",
            "thought": "User wants to skip to the next track.",
            "action": '{"tool": "control_media", "parameters": {"action": "next", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Previous song.",
            "thought": "User wants to go back to the previous track.",
            "action": '{"tool": "control_media", "parameters": {"action": "previous", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Go back to the last song.",
            "thought": "User wants the previous track. Use control_media with previous.",
            "action": '{"tool": "control_media", "parameters": {"action": "previous", "app_hint": "spotify"}}'
        },
        {
            "instruction": "Volume up.",
            "thought": "User wants to increase audio volume using media key.",
            "action": '{"tool": "control_media", "parameters": {"action": "volume_up"}}'
        },
        {
            "instruction": "Volume down.",
            "thought": "User wants to decrease audio volume.",
            "action": '{"tool": "control_media", "parameters": {"action": "volume_down"}}'
        },
        {
            "instruction": "Mute the PC.",
            "thought": "User wants to mute audio. Use control_media mute.",
            "action": '{"tool": "control_media", "parameters": {"action": "mute"}}'
        },
        {
            "instruction": "Silence everything.",
            "thought": "User wants to mute the PC audio.",
            "action": '{"tool": "control_media", "parameters": {"action": "mute"}}'
        },
    ]

    output_path = "data/pc_control_dataset.jsonl"
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")

    print(f"Generated {len(dataset)} training examples in {output_path}")

if __name__ == "__main__":
    generate_dataset()
