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

# Unified list of environments with their specific configurations
ENVIRONMENTS = [
    # Environments with cluster_id (require health screenshots)
    {
        "label": "1_prod_cloudera",
        "base_url": "http://172.30.215.101:7180",
        "cluster_id": "1546372102",
        "type": "full"  # Includes home, health screenshots
    },
    {
        "label": "16_desa_cloudera",
        "base_url": "http://172.30.213.121:7180",
        "cluster_id": "1546331798",
        "type": "full"
    },
    # Environments without cluster_id (only status pane)
    {
        "label": "17_cdh_prod",
        "base_url": "http://172.30.215.201:7180",
        "type": "status_only"  # Only status pane screenshot
    },
    {
        "label": "18_cdh_desa",
        "base_url": "http://172.30.213.201:7180",
        "type": "status_only"
    }
]

# Selectors
SELECTOR_HOME = "#main-page-content"
SELECTOR_HEALTH = "#allHealthIssuesPanel > div"
SELECTOR_STATUS_PANE = "#main-page-content > div > div.status-and-charts > div.status-pane"


def screenshot_force_shrink(page, selector, file_path):
    """
    Forces the element to shrink to the size of its content (removing whitespace)
    using CSS injection, then crops the padding and saves.
    Used for home dashboard and health panel screenshots.
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


def screenshot_smart_crop(page, selector, file_path):
    """
    Measures the exact dimensions of the internal content (children) 
    to determine the width AND height, ensuring nothing is cut off.
    Used for status pane screenshots.
    """
    locator = page.locator(selector).first
    
    try:
        locator.wait_for(state="visible", timeout=15000)
    except:
        print(f"ERROR: Could not find visible element: {selector}")
        return

    # Force Overflow Visible
    locator.evaluate("el => { el.style.height = 'auto'; el.style.overflow = 'visible'; }")
    time.sleep(0.5)

    # Get the container's raw starting position
    box = locator.bounding_box()
    
    if not box:
        print(f"Error: No bounding box for {selector}")
        return

    # Measure Content Dimensions
    dimensions = locator.evaluate("""container => {
        const containerRect = container.getBoundingClientRect();
        let maxRight = 0;
        let maxBottom = 0;
        
        // Loop through all children to find the furthest edges
        for (let child of container.children) {
            const rect = child.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                maxRight = Math.max(maxRight, rect.right);
                maxBottom = Math.max(maxBottom, rect.bottom);
            }
        }
        
        // Fallback: if no children, use container dimensions
        if (maxRight === 0) maxRight = containerRect.right;
        if (maxBottom === 0) maxBottom = containerRect.bottom;

        // Calculate dimensions relative to the container's top-left corner
        const calculatedWidth = (maxRight - containerRect.left) + 15;
        const calculatedHeight = (maxBottom - containerRect.top) + 15;
        
        return {
            width: Math.min(calculatedWidth, containerRect.width),
            height: Math.max(calculatedHeight, containerRect.height) 
        };
    }""")

    # Define the crop area
    clip_area = {
        "x": box["x"],
        "y": box["y"],
        "width": dimensions["width"], 
        "height": dimensions["height"]
    }

    # Take the screenshot
    if clip_area["width"] > 0 and clip_area["height"] > 0:
        page.screenshot(path=file_path, clip=clip_area)
        print(f"Screenshot saved: {file_path}")
    else:
        print("Warning: Calculation failed. Taking standard screenshot.")
        locator.screenshot(path=file_path)


def login(page, base_url, label):
    """
    Performs login for any environment.
    Returns True if successful, False otherwise.
    """
    url_login = f"{base_url}/cmf/login"
    
    print(f"[{label}] Logging in...")
    page.goto(url_login)
    page.fill('input[name="j_username"]', CLOUDERA_USER)
    page.fill('input[name="j_password"]', CLOUDERA_PASSWORD)
    page.press('input[name="j_password"]', 'Enter')
    
    try:
        page.wait_for_url("**/cmf/home", timeout=20000)
        print(f"[{label}] Login successful.")
        return True
    except:
        print(f"[{label}] Login failed or timed out.")
        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{label}_error_login.png"))
        return False


def process_full_environment(page, env):
    """
    Process environments with full dashboard and health screenshots.
    """
    label = env['label']
    base_url = env['base_url']
    cluster_id = env['cluster_id']
    url_health = f"{base_url}/cmf/allHealthIssues?clusterId={cluster_id}"

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- HOME SCREENSHOT ---
    print(f"[{label}] Capturing Home Dashboard...")
    file_path_home = os.path.join(OUTPUT_DIR, f"{label}_dashboard.png")
    screenshot_force_shrink(page, SELECTOR_HOME, file_path_home)

    # --- NAVIGATE TO HEALTH ISSUES ---
    print(f"[{label}] Navigating to Health Issues...")
    page.goto(url_health)
    page.wait_for_load_state("networkidle")

    # --- CLICK BUTTON ---
    print(f"[{label}] Clicking 'Organize By Health Test'...")
    try:
        btn = page.locator("text=/Organi.*By Health Test/i")
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
    except:
        print(f"[{label}] Could not find button. Proceeding...")

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- HEALTH SCREENSHOT ---
    print(f"[{label}] Capturing Health Panel...")
    file_path_health = os.path.join(OUTPUT_DIR, f"{label}_health.png")
    screenshot_force_shrink(page, SELECTOR_HEALTH, file_path_health)


def process_status_only_environment(page, env):
    """
    Process environments with only status pane screenshot.
    """
    label = env['label']

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- STATUS PANE SCREENSHOT ---
    print(f"[{label}] Capturing Status Pane...")
    file_path = os.path.join(OUTPUT_DIR, f"{label}_status_pane.png")
    screenshot_smart_crop(page, SELECTOR_STATUS_PANE, file_path)


def process_environment(env, playwright_instance):
    """
    Handles the login and screenshot logic for a single environment.
    Routes to appropriate processing function based on environment type.
    """
    label = env['label']
    base_url = env['base_url']
    env_type = env['type']
    
    print(f"\n--- Starting processing for {label} ({base_url}) ---")
    
    # Launch browser with appropriate viewport
    # Status-only environments need larger viewport for full page rendering
    headless = env.get('headless', True)
    if env_type == "status_only":
        browser = playwright_instance.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1920, "height": 4500})
    else:
        browser = playwright_instance.chromium.launch(headless=headless)
        page = browser.new_page()

    # --- LOGIN ---
    if not login(page, base_url, label):
        browser.close()
        return

    # --- PROCESS BASED ON TYPE ---
    try:
        if env_type == "full":
            process_full_environment(page, env)
        elif env_type == "status_only":
            process_status_only_environment(page, env)
        
        print(f"[{label}] Completed.")
    except Exception as e:
        print(f"ERROR during processing {label}: {e}")
    finally:
        browser.close()


def run_all(headless=True):
    """
    Main entry point - processes all environments.
    """
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    with sync_playwright() as p:
        for env in ENVIRONMENTS:
            try:
                # Add headless parameter to environment config
                env['headless'] = headless
                process_environment(env, p)
            except Exception as e:
                print(f"CRITICAL ERROR processing {env['label']}: {e}")


