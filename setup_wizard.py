import os
import re
import subprocess
import sys
import json
import random
import string
import webbrowser
import time
import shutil

# Anchor all file I/O to the project root (the directory this script lives in),
# regardless of what directory the user runs it from.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("="*70)
    try:
        print("      \U0001f577\ufe0f  Spider-ARM: Hybrid 'Cloud Architect' Wizard v2.5 \U0001f577\ufe0f")
    except UnicodeEncodeError:
        print("      [*]  Spider-ARM: Hybrid 'Cloud Architect' Wizard v2.5 [*]")
    print("="*70)
    print("Build or Link your Firebase Infrastructure in minutes.")
    print("Requirement: You must have the Firebase CLI installed.\n")

def get_input(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def run_cmd(cmd, capture_output=True):
    """Runs a shell command and returns the output."""
    try:
        # Specified encoding='utf-8' and errors='ignore' to handle Windows symbol mismatches
        result = subprocess.run(cmd, capture_output=capture_output, text=True, shell=True, check=True, encoding='utf-8', errors='ignore')
        # Check if stdout exists before stripping (handles capture_output=False)
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {cmd}")
        if e.stderr:
            print(f"Details: {e.stderr}")
        return None

def run_step(name, func):
    print(f"\n[STEP] {name}...")
    try:
        res = func()
        if res is not False:
            print(f"[SUCCESS] {name} complete.")
            return res
        return False
    except Exception as e:
        print(f"[ERROR] {name} failed: {e}")
        return False

def generate_id(prefix="spider-arm"):
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{suffix}"

def check_firebase_cli():
    """Verifies the Firebase CLI is installed before doing anything else."""
    if shutil.which("firebase") is None:
        print("\n[FATAL] Firebase CLI not found on PATH.")
        print("Please install it first:")
        print("  npm install -g firebase-tools")
        print("  OR  https://firebase.google.com/docs/cli")
        sys.exit(1)
    print("[OK] Firebase CLI detected.")

def setup():
    clear()
    print_banner()

    # --- 0. PRE-FLIGHT: Ensure Firebase CLI exists ---
    check_firebase_cli()

    # --- 1. AUTH CHECK ---
    def check_auth():
        print("Checking Firebase login status...")
        out = run_cmd("firebase projects:list")
        if not out or "Error" in out:
            print("Action Required: Please log in to Firebase in your browser.")
            run_cmd("firebase login", capture_output=False)
        return True

    if not run_step("Firebase Authentication", check_auth): return

    # --- 2. MODE SELECTION ---
    print("\nHow would you like to set up Spider-Arm?")
    print("[1] Create Fresh Project (Zero-Touch - Recommended)")
    print("[2] Link to Existing Project (Choose from your cloud list)")
    
    choice = get_input("Select mode", "1")
    
    project_id = None
    web_config = None

    if choice == "2":
        # --- LINK EXISTING ---
        def fetch_projects():
            print("Fetching your Firebase projects...")
            out = run_cmd("firebase projects:list --json")
            if not out: return False
            
            data = json.loads(out)
            projects = data.get("result", [])
            
            if not projects:
                print("[ERROR] No Firebase projects found in your account.")
                return False
                
            print("\nYour Projects:")
            for i, p in enumerate(projects):
                print(f"[{i+1}] {p['projectId']} ({p.get('displayName', 'No Title')})")
                
            pick = int(get_input("\nSelect Project Number", "1")) - 1
            selected = projects[pick]['projectId']
            
            # Fetch Web Apps in this project
            print(f"Checking for Web Apps in '{selected}'...")
            apps_out = run_cmd(f"firebase apps:list WEB --project {selected} --json")
            apps_data = json.loads(apps_out) if apps_out else {"result": []}
            apps = apps_data.get("result", [])
            
            app_id = None
            if not apps:
                print("No Web App found in this project. Registering 'Spider Dashboard'...")
                run_cmd(f'firebase apps:create WEB "Spider Dashboard" --project {selected}', capture_output=False)
                # Re-fetch
                apps_out = run_cmd(f"firebase apps:list WEB --project {selected} --json")
                apps = json.loads(apps_out).get("result", [])
            
            if apps:
                print("\nChoose Web App:")
                for i, a in enumerate(apps):
                    print(f"[{i+1}] {a['displayName']} ({a['appId']})")
                apick = int(get_input("Select App Number", "1")) - 1
                app_id = apps[apick]['appId']
            
            # Harvest Config
            print("Harvesting SDK credentials...")
            config_out = run_cmd(f"firebase apps:sdkconfig WEB {app_id} --project {selected} --json")
            if config_out:
                cfg_data = json.loads(config_out)
                return (selected, cfg_data.get("result", {}).get("sdkConfig"))
            return False

        res = run_step("Linking Existing Project", fetch_projects)
        if not res: return
        project_id, web_config = res
        # Switch CLI to this project
        run_cmd(f"firebase use {project_id} --alias default", capture_output=False)

    else:
        # --- CREATE NEW ---
        project_id = generate_id()
        def create_project():
            print(f"Creating project '{project_id}'... this takes ~30 seconds.")
            result = run_cmd(f'firebase projects:create {project_id} --display-name "Spider Arm Assistant"', capture_output=False)
            if result is None:
                print("[ERROR] Project creation command failed. Check Firebase CLI output above.")
                return False
            print("Waiting for cloud provisioning...")
            time.sleep(10)  # Give the backend time to stabilize
            use_result = run_cmd(f"firebase use {project_id} --alias default", capture_output=False)
            if use_result is None:
                print("[ERROR] Could not switch to new project. It may not have been created.")
                return False
            return True

        if not run_step(f"Provisioning Cloud Project ({project_id})", create_project): return

        def enable_firestore():
            print("Initializing Firestore Database (Region: us-central)...")
            run_cmd(f"firebase firestore:databases:create --location us-central --project {project_id}", capture_output=False)
            return True
        run_step("Activating Firestore Database", enable_firestore)

        def register_app():
            print("Registering the 'Spider Dashboard' Web App...")
            run_cmd(f'firebase apps:create WEB "Spider Dashboard" --project {project_id}', capture_output=False)
            print("Syncing app metadata (waiting 15 seconds for propagation)...")
            # Count down visibly so the user knows the wizard isn't frozen
            for i in range(15, 0, -1):
                print(f"  {i}s remaining...", end="\r")
                time.sleep(1)
            print(" " * 30, end="\r")  # Clear countdown line
            # Retry up to 3 times in case SDK config hasn't propagated yet
            for attempt in range(1, 4):
                config_out = run_cmd(f"firebase apps:sdkconfig WEB --project {project_id} --json")
                if config_out:
                    data = json.loads(config_out)
                    sdk = data.get("result", {}).get("sdkConfig")
                    if sdk:
                        return sdk
                print(f"  [RETRY {attempt}/3] SDK config not ready yet, waiting 10 more seconds...")
                time.sleep(10)
            print("[ERROR] Could not fetch SDK config after 3 attempts.")
            return None

        web_config = run_step("Registering Web Dashboard", register_app)

    if not web_config: 
        print("[CRITICAL] Could not harvest Web SDK Keys.")
        return

    # --- 3. UNIFIED VAULT INJECTION ---
    def save_vault():
        email = get_input("Your Gmail (for Security Lockdown rules)")
        
        vault = {
            "web_dashboard": web_config,
            "authorized_email": email,
            "service_account": None
        }
        
        # Use absolute paths anchored to project root so this works
        # regardless of where the user runs the wizard from.
        mobile_dir = os.path.join(PROJECT_ROOT, "mobile")
        os.makedirs(mobile_dir, exist_ok=True)
        js_content = "export const firebaseConfig = " + json.dumps(web_config, indent=4) + ";"
        with open(os.path.join(mobile_dir, "firebase-config.js"), "w") as f:
            f.write(js_content)
        
        return vault

    vault = run_step("Generating Unified Vault & Dashboard Config", save_vault)

    # Guard: if vault step failed, do not proceed to service account step
    if not vault or not isinstance(vault, dict):
        print("[CRITICAL] Vault generation failed. Cannot proceed to service account linking.")
        return

    # --- 4. SERVICE ACCOUNT ---
    def fetch_service_account():
        print("\n[SECURITY LINKING]")
        print("1. STEP 1: Enable Authentication")
        print("   -> Your browser will open the AUTH page.")
        print("   -> Click 'Get Started' -> 'Google' -> Enable -> SAVE.")
        auth_url = f"https://console.firebase.google.com/project/{project_id}/authentication/providers"
        webbrowser.open(auth_url)
        
        get_input("\nPress ENTER once you have enabled Google Sign-In to proceed to Key Generation")
        
        print("\n2. STEP 2: Generate Private Key")
        print("   -> Your browser will open the SERVICE ACCOUNTS page.")
        print("   -> Click 'Generate New Private Key' -> 'Create Key'.")
        sa_url = f"https://console.firebase.google.com/project/{project_id}/settings/serviceaccounts/adminsdk"
        webbrowser.open(sa_url)
        
        print("\n3. STEP 3: Paste JSON Content")
        print("   -> Open the downloaded JSON and paste its ENTIRE content here.")
        print("   -> (Press Enter on an empty line when finished):")
        
        lines = []
        while True:
            line = input().strip()
            if line == "": break
            lines.append(line)
        
        raw_json = "".join(lines)
        # Sanitization: Remove common copy-paste artifacts
        raw_json = raw_json.strip().replace('\x1b', '').replace('\x07', '')
        
        try:
            sa_data = json.loads(raw_json)
            vault["service_account"] = sa_data
            cred_path = os.path.join(PROJECT_ROOT, "credentials.json")
            with open(cred_path, "w") as f:
                json.dump(vault, f, indent=4)
            print(f"[OK] Credentials saved to: {cred_path}")
            return True
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON formatting: {e}")
            print("Tip: Make sure you copied the entire file content, including { and }.")
            return False

    if not run_step("Linking Security Systems (Service Account)", fetch_service_account): return

    # --- 5. DEPLOY ---
    def deploy_systems():
        print("Pushing Security Rules and Dashboard to the Cloud...")
        run_cmd("firebase deploy", capture_output=False)
        return True

    run_step("Live Deployment", deploy_systems)

    # --- 6. BRAIN GENERATION ---
    def compile_brain():
        model_dir = os.path.join(PROJECT_ROOT, "qwen_assistant_lora")
        if not os.path.exists(model_dir):
            print("AI Brain not found. Starting compilation (This takes 3-5 minutes)...")
            # Use sys.executable to target the active venv Python, and an absolute
            # path so this works regardless of the working directory at call time.
            train_script = os.path.join(PROJECT_ROOT, "train.py")
            run_cmd(f'"{sys.executable}" "{train_script}"', capture_output=False)

            # Verify training actually produced a model
            if not os.path.exists(model_dir):
                print("[ERROR] Training completed but no model folder was created.")
                print("Check the output above for errors. You can re-run 'python train.py' manually.")
                return False
            return True
        else:
            print("AI Brain already compiled. Skipping.")
            return True
            
    run_step("AI Brain Compilation", compile_brain)

    print("\n" + "="*70)
    try:
        print("      \U0001f38a  HYBRID SETUP COMPLETE! SPIDER-ARM IS LIVE \U0001f38a")
    except UnicodeEncodeError:
        print("      [**]  HYBRID SETUP COMPLETE! SPIDER-ARM IS LIVE [**]")
    print("="*70)
    print(f"Project ID: {project_id}")
    print(f"Dashboard URL: https://{project_id}.web.app")
    print("\nNext steps:")
    print("1. Open the URL on your phone.")
    print("2. Run 'python -m backend.firebase_bridge' to start the bridge.")
    print("\nWelcome back to the loop! \U0001f578\ufe0f\U0001f916")

if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n[WIZARD] Setup cancelled.")
    except Exception as e:
        print(f"\n[FATAL] Wizard crashed: {e}")
