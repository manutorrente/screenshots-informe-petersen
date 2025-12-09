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

ENVIRONMENTS = [
    {
        "label": "17_cdh_prod",
        "base_url": "http://172.30.215.201:7180"
    },
    {
        "label": "18_cdh_desa",
        "base_url": "http://172.30.213.201:7180"
    }
]

# Target Selector
SELECTOR_TARGET = "#main-page-content > div > div.status-and-charts > div.status-pane"

def screenshot_smart_crop(page, selector, file_path):
    """
    Measures the exact dimensions of the internal content (children) 
    to determine the width AND height, ensuring nothing is cut off.
    """
    locator = page.locator(selector).first
    
    try:
        locator.wait_for(state="visible", timeout=15000)
    except:
        print(f"ERROR: Could not find visible element: {selector}")
        return

    # 1. Force Overflow Visible
    # This ensures that if the element itself has a scrollbar, we force it open
    # so the screenshot captures the full length.
    locator.evaluate("el => { el.style.height = 'auto'; el.style.overflow = 'visible'; }")
    time.sleep(0.5)

    # 2. Get the container's raw starting position
    box = locator.bounding_box()
    
    if not box:
        print(f"Error: No bounding box for {selector}")
        return

    # 3. Measure Content Dimensions
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

    # 4. Define the crop area
    clip_area = {
        "x": box["x"],
        "y": box["y"],
        "width": dimensions["width"], 
        "height": dimensions["height"]
    }

    # 5. Take the screenshot
    if clip_area["width"] > 0 and clip_area["height"] > 0:
        page.screenshot(path=file_path, clip=clip_area)
        print(f"Screenshot saved: {file_path}")
    else:
        print("Warning: Calculation failed. Taking standard screenshot.")
        locator.screenshot(path=file_path)


def process_environment(env, playwright_instance):
    label = env['label']
    base_url = env['base_url']
    url_login = f"{base_url}/cmf/login"

    print(f"\n--- Starting processing for {label} ({base_url}) ---")
    
    # --- FIX: Set a massive viewport height (4500px) ---
    # This ensures the entire page is rendered at once, so "scrolling" is not needed.
    browser = playwright_instance.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1920, "height": 4500})

    # --- LOGIN ---
    print(f"[{label}] Logging in...")
    page.goto(url_login)
    page.fill('input[name="j_username"]', CLOUDERA_USER)
    page.fill('input[name="j_password"]', CLOUDERA_PASSWORD)
    page.press('input[name="j_password"]', 'Enter')
    
    try:
        page.wait_for_url("**/cmf/home", timeout=20000)
        print(f"[{label}] Login successful.")
    except:
        print(f"[{label}] Login failed.")
        page.screenshot(path=os.path.join(OUTPUT_DIR, f"error_login_{label}.png"))
        browser.close()
        return

    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- SCREENSHOT ---
    print(f"[{label}] Capturing Status Pane...")
    file_path = os.path.join(OUTPUT_DIR, f"status_pane_{label}.png")
    screenshot_smart_crop(page, SELECTOR_TARGET, file_path)

    print(f"[{label}] Completed.")
    browser.close()

def run_all():
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