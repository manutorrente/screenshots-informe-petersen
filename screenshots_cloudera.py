import time
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# 1. Load Environment Variables
load_dotenv(override=True)

CLOUDERA_USER = os.getenv("CLOUDERA_USER")
CLOUDERA_PASSWORD = os.getenv("CLOUDERA_PASSWORD")

if not CLOUDERA_USER or not CLOUDERA_PASSWORD:
    raise ValueError("Missing credentials! Please set CLOUDERA_USER and CLOUDERA_PASSWORD in your .env file.")

# --- CONFIGURATION ---
OUTPUT_DIR = "output"

# List of environments to process
ENVIRONMENTS = [
    {
        "label": "1_prod_cloudera",
        "base_url": "http://172.30.215.101:7180",
        "cluster_id": "1546372102"
    },
    {
        "label": "16_desa_cloudera",
        "base_url": "http://172.30.213.121:7180",
        "cluster_id": "1546331798"
    }
]

# Selectors (Shared across environments)
SELECTOR_HOME = "#main-page-content"
SELECTOR_HEALTH = "#allHealthIssuesPanel > div"

def screenshot_force_shrink(page, selector, file_path):
    """
    Forces the element to shrink to the size of its content (removing whitespace)
    using CSS injection, then crops the padding and saves.
    """
    locator = page.locator(selector).first
    
    try:
        locator.wait_for(state="visible", timeout=15000)
    except:
        print(f"ERROR: Could not find visible element: {selector}")
        return

    # Force element to shrink to fit content
    locator.evaluate("""el => {
        el.style.display = 'inline-block'; 
        el.style.width = 'fit-content';
    }""")
    
    time.sleep(0.5)

    # Calculate padding
    box = locator.bounding_box()
    padding = locator.evaluate("""el => {
        const style = window.getComputedStyle(el);
        return {
            top: parseFloat(style.paddingTop),
            left: parseFloat(style.paddingLeft),
            bottom: parseFloat(style.paddingBottom),
            right: parseFloat(style.paddingRight)
        }
    }""")

    if box:
        clip_area = {
            "x": box["x"] + padding["left"],
            "y": box["y"] + padding["top"],
            "width": box["width"] - padding["left"] - padding["right"],
            "height": box["height"] - padding["top"] - padding["bottom"]
        }
        
        if clip_area["width"] > 0 and clip_area["height"] > 0:
            page.screenshot(path=file_path, clip=clip_area)
            print(f"Screenshot saved: {file_path}")
        else:
            print("Warning: Element collapsed to zero size. Taking standard screenshot.")
            locator.screenshot(path=file_path)
    else:
        print(f"Error: No bounding box for {selector}")


def process_environment(env, playwright_instance):
    """
    Handles the login and screenshot logic for a single environment.
    """
    label = env['label']
    base_url = env['base_url']
    cluster_id = env['cluster_id']
    
    # Construct URLs dynamically
    url_login = f"{base_url}/cmf/login"
    url_health = f"{base_url}/cmf/allHealthIssues?clusterId={cluster_id}"

    print(f"\n--- Starting processing for {label} ({base_url}) ---")
    
    # Launch browser
    browser = playwright_instance.chromium.launch(headless=True)
    page = browser.new_page()

    # --- STEP 1: LOGIN ---
    print(f"[{label}] Logging in...")
    page.goto(url_login)
    page.fill('input[name="j_username"]', CLOUDERA_USER)
    page.fill('input[name="j_password"]', CLOUDERA_PASSWORD)
    page.press('input[name="j_password"]', 'Enter')
    
    try:
        page.wait_for_url("**/cmf/home", timeout=20000)
        print(f"[{label}] Login successful.")
    except:
        print(f"[{label}] Login failed or timed out.")
        # Save error screenshot to output dir
        page.screenshot(path=os.path.join(OUTPUT_DIR, f"error_login_{label}.png"))
        browser.close()
        return

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- STEP 2: HOME SCREENSHOT ---
    print(f"[{label}] Capturing Home Dashboard...")
    # Construct full path: output/dashboard_env1_101.png
    file_path_home = os.path.join(OUTPUT_DIR, f"dashboard_{label}.png")
    screenshot_force_shrink(page, SELECTOR_HOME, file_path_home)

    # --- STEP 3: NAVIGATE TO HEALTH ISSUES ---
    print(f"[{label}] Navigating to Health Issues...")
    page.goto(url_health)
    page.wait_for_load_state("networkidle")

    # --- STEP 4: CLICK BUTTON ---
    print(f"[{label}] Clicking 'Organize By Health Test'...")
    try:
        btn = page.locator("text=/Organi.*By Health Test/i")
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
    except:
        print(f"[{label}] Could not find button. Proceeding...")

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- STEP 5: HEALTH SCREENSHOT ---
    print(f"[{label}] Capturing Health Panel...")
    file_path_health = os.path.join(OUTPUT_DIR, f"health_{label}.png")
    screenshot_force_shrink(page, SELECTOR_HEALTH, file_path_health)
    
    print(f"[{label}] Completed.")
    browser.close()

def run_all():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    with sync_playwright() as p:
        for env in ENVIRONMENTS:
            try:
                process_environment(env, p)
            except Exception as e:
                print(f"CRITICAL ERROR processing {env['label']}: {e}")

if __name__ == "__main__":
    run_all()