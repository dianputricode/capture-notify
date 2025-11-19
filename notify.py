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
CHAT_REGION = (50, 300, 650, 400)  # (x, y, width, height)

def send_to_discord(msg):
    payload = {"content": f"🎣 {msg}"}
    requests.post(WEBHOOK, json=payload)

last_msg = ""

print("Watching for: [Server]: Din obtained ...")

while True:
    # capture only the chat region
    screenshot = pyautogui.screenshot(region=CHAT_REGION)
    text = pytesseract.image_to_string(screenshot)

    # look for lines that contain the catch
    for line in text.split("\n"):
        if f"{YOUR_NAME} obtained" in line and line != last_msg:

            # extract fish name & weight 
            match = re.search(r"obtained a (.*?\(.*?kg\))", line)
            if match:
                fish_info = match.group(1)
                msg = f"{YOUR_NAME} caught: **{fish_info}**"
                send_to_discord(msg)
                print("Sent:", msg)
                last_msg = line

    time.sleep(0.5)
