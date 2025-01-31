import pyautogui
import base64
from io import BytesIO
from PIL import Image

class ScreenshotService:
    @staticmethod
    def capture_and_encode() -> str:
        """Capture screenshot and encode to base64."""
        screenshot = pyautogui.screenshot()
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=95)
        return base64.b64encode(buffered.getvalue()).decode()
