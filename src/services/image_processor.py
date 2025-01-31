import cv2
import numpy as np
from PIL import Image
import io

class ImageProcessor:
    @staticmethod
    def enhance_screenshot(image: Image.Image) -> Image.Image:
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply enhancements
        # 1. Increase contrast
        lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge((l,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 2. Sharpen image
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 3. Denoise
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced)
        
        # Convert back to PIL Image
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        return Image.fromarray(enhanced)
