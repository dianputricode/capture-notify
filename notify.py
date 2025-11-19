import pytesseract
import pyautogui
import requests
from PIL import Image
import time
import re

# config
WEBHOOK = "https://discord.com/api/webhooks/1440820644315922565/heZNYLExto-dvShF11CXPjJK5_17jBLWvMVy22C8Znehfd3MrTgKdy5-IGEnXAL8TjPo"
YOUR_NAME = "Din"

# path to tesseract 
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# values
CHAT_REGION = (50, 300, 650, 400)

# cooldown 30 minutes
COOLDOWN = 1800

# dictionary to store cooldown per fish
fish_cooldown = {}

def send_to_discord(msg):
    payload = {"content": f"🎣 {msg}"}
    requests.post(WEBHOOK, json=payload)

print("Watching for: [Server]: Din obtained ...")

while True:
    screenshot = pyautogui.screenshot(region=CHAT_REGION)
    text = pytesseract.image_to_string(screenshot)

    for line in text.split("\n"):
        if f"{YOUR_NAME} obtained" in line:

            match = re.search(r"obtained a (.*?\(.*?kg\))", line)
            if match:
                fish_info = match.group(1).strip()

                # if this fish was already sent in last 30 min → skip
                if fish_info in fish_cooldown:
                    if (time.time() - fish_cooldown[fish_info]) < COOLDOWN:
                        continue  

                # send to discord
                msg = f"{YOUR_NAME} caught: **{fish_info}**"
                send_to_discord(msg)
                print("Sent:", msg)

                # update cooldown timestamp
                fish_cooldown[fish_info] = time.time()

    time.sleep(0.4)
