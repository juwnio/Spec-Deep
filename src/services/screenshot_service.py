import pyautogui
import base64
from io import BytesIO
from PIL import Image
from .image_processor import ImageProcessor

class ScreenshotService:
    @staticmethod
    def capture_and_encode() -> str:
        # Capture screenshot
        screenshot = pyautogui.screenshot()
        
        # Enhance the image
        enhanced = ImageProcessor.enhance_screenshot(screenshot)
        
        # Encode to base64
        buffered = BytesIO()
        enhanced.save(buffered, format="JPEG", quality=95)
        return base64.b64encode(buffered.getvalue()).decode()
