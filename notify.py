import pytesseract
import pyautogui
import requests
from PIL import Image, ImageEnhance, ImageFilter
import time
import re
import difflib
import hashlib

# Config
WEBHOOK = "{link_webhook}"
PLAYERS = ["{users}"]  # names to watch

# Path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Chat region
CHAT_REGION = (50, 300, 650, 400)

# Save last fish
last_fish = {}   # example: { "din_astra damsel": 3.3 }

# Hash line to prevent duplicate prints
last_lines = set()

# ==========================================

def send_to_discord(msg):
    payload = {"content": f"🎣 {msg}"}
    try:
        requests.post(WEBHOOK, json=payload)
    except Exception as e:
        print("Failed to send:", e)

# ------------------------------------------
# UTILITIES
# ------------------------------------------

def normalize(text):
    """Remove symbols, make lowercase, for fuzzy matching."""
    return re.sub(r'[^a-zA-Z ]', '', text).lower().strip()

def extract_info(line):
    """Extract fish name + weight from a chat line"""
    pattern = r"(?:caught \*\*|obtained a |obtained an )(.+?)\s*\(([\d\.]+)kg\)"
    match = re.search(pattern, line)
    if not match:
        return None, None

    fish_name = match.group(1).strip()
    weight = round(float(match.group(2)), 1)
    return fish_name, weight

def similar(a, b):
    """Fuzzy match for fish names"""
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.6

def line_hash(player, fish_name, weight):
    """Generate a unique hash for a line to prevent duplicates"""
    return hashlib.md5(f"{player}_{fish_name}_{weight}".encode()).hexdigest()

# ------------------------------------------
# LOGIC FILTER
# ------------------------------------------

def find_existing_fish(player_key, norm_new, weight):
    """Find a similar fish with close weight (to handle OCR noise)"""
    for existing in last_fish.keys():
        if existing.startswith(player_key):
            existing_name = existing.split("_", 1)[1]
            if similar(norm_new, existing_name):
                if abs(weight - last_fish[existing]) <= 1.0:
                    return existing
    return None

def should_send(fish_key, weight):
    """Determine if the message should be sent"""
    if weight > 1000:
        print(f"Skipped unrealistic weight (OCR error?): {fish_key} ({weight}kg)")
        return False

    old_weight = last_fish.get(fish_key)
    
    if old_weight is None:
        last_fish[fish_key] = weight
        return True

    if abs(weight - old_weight) > 1.0:
        last_fish[fish_key] = weight
        return True

    return False

print("Watching for players:", ", ".join(PLAYERS))

# ------------------------------------------
# MAIN LOOP
# ------------------------------------------
while True:
    screenshot = pyautogui.screenshot(region=CHAT_REGION)

    # OCR enhancement
    img = screenshot.convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)
    gray = img.convert("L")
    bw = gray.point(lambda x: 255 if x > 130 else 0, "1")

    text = pytesseract.image_to_string(bw, config="--psm 6")

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue

        line_low = line.lower()

        # Check if the line contains any player
        player_found = None
        for player in PLAYERS:
            if player.lower() in line_low:
                player_found = player
                break
        if not player_found:
            continue

        # Extract fish name + weight
        fish_name, weight = extract_info(line)
        if not fish_name:
            continue

        norm_new = normalize(fish_name)
        player_key = player_found.lower()

        # Fuzzy match fish name + weight
        existing = find_existing_fish(player_key, norm_new, weight)
        if existing:
            fish_key = existing
        else:
            fish_key = f"{player_key}_{norm_new}"

        # Unique hash to prevent duplicates
        h = line_hash(player_key, fish_name, weight)
        if h in last_lines:
            continue
        last_lines.add(h)
        if len(last_lines) > 500:
            last_lines.pop()

        # If allowed, send message
        if should_send(fish_key, weight):
            msg = f"{player_found} caught **{fish_name} ({weight}kg)**"
            send_to_discord(msg)
            print("Sent:", msg)

    time.sleep(0.5)
