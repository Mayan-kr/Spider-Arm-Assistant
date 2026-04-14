import os
import re
import subprocess
import sys
import json

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("="*60)
    print("      🕷️ Spider-Arm: Automated Setup Wizard v2.0 🕷️")
    print("="*60)
    print("This wizard will link your PC to your private dashboard.")
    print("Please have your Firebase Console ready.\n")

def get_input(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def run_step(name, func):
    print(f"\n[STEP] {name}...")
    try:
        func()
        print(f"[SUCCESS] {name} complete.")
        return True
    except Exception as e:
        print(f"[ERROR] {name} failed: {e}")
        return False

def setup():
    clear()
    print_banner()

    # --- 1. COLLECT INFORMATION ---
    print("--- 1. Firebase Information ---")
    print("Find these under Project Settings -> Web App (Firebase SDK snippet)\n")
    
    config = {
        "apiKey": get_input("API Key"),
        "authDomain": get_input("Auth Domain"),
        "projectId": get_input("Project ID"),
        "storageBucket": get_input("Storage Bucket"),
        "messagingSenderId": get_input("Messaging Sender ID"),
        "appId": get_input("App ID"),
        "measurementId": get_input("Measurement ID")
    }
    
    email = get_input("Your Gmail (for security rules lockdown)")

    # --- 2. CONFIG INJECTION ---
    def inject_config():
        path = "mobile/index.html"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Could not find {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Build JS config string
        js_config = "const firebaseConfig = {\n"
        for k, v in config.items():
            js_config += f'            {k}: "{v}",\n'
        js_config = js_config.rstrip(",\n") + "\n        };"

        # Regex replace
        pattern = r"// /\* FIREBASE_CONFIG_START \*/(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n(.*?)\r?\n\s+// /\* FIREBASE_CONFIG_END \*/"
        
        # Simpler robust marker replace
        start_marker = "// /* FIREBASE_CONFIG_START */"
        end_marker = "// /* FIREBASE_CONFIG_END */"
        
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("Markers not found in index.html")

        new_content = content[:start_idx] + "\n        " + js_config + "\n        " + content[end_idx:]
        
        # Also replace the placeholder email in the bot greeting (line 341 approx)
        new_content = re.sub(r"Hey Kumar!", f"Hey {email.split('@')[0].capitalize()}!", new_content)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

    run_step("Injecting Configuration into Dashboard", inject_config)

    # --- 3. DEPENDENCIES ---
    def install_deps():
        deps = ["psutil", "pyautogui", "firebase-admin", "GPUtil", "wmi", "pygetwindow"]
        print(f"Installing system dependencies: {', '.join(deps)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + deps)

    run_step("Installing Python Dependencies", install_deps)

    # --- 4. BRAIN ACTIVATION (TRAINING) ---
    def train_brain():
        print("Activating AI Brain (this will take 3-5 minutes on an RTX GPU)...")
        # Run train.py and pipe output so user can see progress
        process = subprocess.Popen([sys.executable, "train.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(f"  [TRAINING] {line.strip()}")
        process.wait()
        if process.returncode != 0:
            raise Exception("Training process crashed.")

    run_step("Awakening the AI Brain (Fine-Tuning)", train_brain)

    # --- 5. FINISH ---
    print("\n" + "="*60)
    print("      🎉 SETUP COMPLETE! SPIDER-ARM IS READY 🎉")
    print("="*60)
    print(f"\nYour dashboard is now linked to: {config['projectId']}")
    print(f"Authorized Email: {email}")
    print("\nFINAL STEPS:")
    print("1. Run 'firebase login' to authenticate.")
    print("2. Run 'firebase deploy' to put your dashboard on the web.")
    print("3. Start your PC agent: 'python -m backend.firebase_bridge'")
    print("\nEnjoy your private agentic PC assistant! 🕸️🤖")

if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n[WIZARD] Setup cancelled by user.")
