import pyautogui
import base64
from io import BytesIO
from PIL import Image

class ScreenshotService:
    @staticmethod
    def capture_and_encode() -> str:
        screenshot = pyautogui.screenshot()
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()
