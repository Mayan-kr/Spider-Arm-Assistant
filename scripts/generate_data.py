import json
import os

def generate_dataset():
    dataset = [
        {
            "instruction": "Capture the current screen and save it.",
            "thought": "The user wants a screenshot. I should call the screenshot tool.",
            "action": '{"tool": "screenshot", "parameters": {}}'
        },
        {
            "instruction": "Open the calculator app.",
            "thought": "The user wants to open the calculator. I'll use the launch_app tool.",
            "action": '{"tool": "launch_app", "parameters": {"name": "calculator"}}'
        },
        {
            "instruction": "What is the current CPU usage?",
            "thought": "I need to fetch system telemetry to check CPU usage.",
            "action": '{"tool": "get_system_info", "parameters": {"metric": "cpu"}}'
        },
        {
            "instruction": "Delete the old log file in downloads.",
            "thought": "Deleting a file is a sensitive action. I must request confirmation first.",
            "action": '{"tool": "request_confirmation", "parameters": {"action": "delete", "target": "C:/Users/kumar/Downloads/old_log.txt"}}'
        },
        {
            "instruction": "Play some relaxing music.",
            "thought": "The user wants music. I can try to open a media player or a specific URL.",
            "action": '{"tool": "launch_app", "parameters": {"name": "spotify"}}'
        },
        {
            "instruction": "Type 'Hello World' in the active window.",
            "thought": "I need to simulate keyboard input for the user.",
            "action": '{"tool": "type_text", "parameters": {"text": "Hello World"}}'
        },
        {
            "instruction": "Close all chrome windows.",
            "thought": "I should iterate through processes and close chrome.exe.",
            "action": '{"tool": "terminate_process", "parameters": {"name": "chrome"}}'
        },
        {
            "instruction": "Take a screenshot and tell me if my browser is open.",
            "thought": "I need to take a screenshot and then check the process list for browser applications.",
            "action": "{\"tool\": \"screenshot\", \"args\": {}}"
        },
        {
            "instruction": "What is my current disk usage?",
            "thought": "I will check the system telemetry to get disk usage statistics.",
            "action": "{\"tool\": \"get_system_telemetry\", \"args\": {}}"
        },
        {
            "instruction": "Close Notepad immediately.",
            "thought": "I need to find the process ID for Notepad and terminate it.",
            "action": "{\"tool\": \"close_app\", \"args\": {\"app_name\": \"notepad\"}}"
        },
        {
            "instruction": "Delete the file 'test.txt' from C:\\temp.",
            "thought": "Deleting a file is a sensitive action and requires user confirmation.",
            "action": "{\"tool\": \"delete_file\", \"args\": {\"file_path\": \"C:\\\\temp\\\\test.txt\"}}"
        },
        {
            "instruction": "Are there any high-memory processes running?",
            "thought": "I should check the process list and sort by memory usage.",
            "action": "{\"tool\": \"get_system_telemetry\", \"args\": {}}"
        },
        {
            "instruction": "Launch Chrome and go to google.com",
            "thought": "I will use the launch_app tool to start Chrome with the specified URL.",
            "action": "{\"tool\": \"launch_app\", \"args\": {\"app_name\": \"chrome\", \"url\": \"https://google.com\"}}"
        },
        {
            "instruction": "Check if the file 'important.pdf' exists in my Documents folder.",
            "thought": "I need to verify the existence of a specific file.",
            "action": "{\"tool\": \"get_system_telemetry\", \"args\": {}}"
        },
        {
            "instruction": "Give me a summary of my PC health.",
            "thought": "I'll fetch CPU, RAM, and disk info for a summary.",
            "action": "{\"tool\": \"get_system_telemetry\", \"args\": {}}"
        },
        {
            "instruction": "Stop all python processes.",
            "thought": "I'll identify all python.exe instances and close them.",
            "action": "{\"tool\": \"close_app\", \"args\": {\"app_name\": \"python\"}}"
        },
        {
            "instruction": "Clean up the temp folder.",
            "thought": "This is a batch deletion and needs careful handling/confirmation.",
            "action": "{\"tool\": \"delete_file\", \"args\": {\"file_path\": \"C:\\\\Windows\\\\Temp\"}}"
        }
    ]
    
    output_path = "data/pc_control_dataset.jsonl"
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        for entry in dataset:
            # Formatting for Unsloth-style chat/instruction
            # Using a simplified format that we can later map to ChatML or Alpaca
            f.write(json.dumps(entry) + "\n")
    
    print(f"Generated {len(dataset)} examples in {output_path}")

if __name__ == "__main__":
    generate_dataset()
