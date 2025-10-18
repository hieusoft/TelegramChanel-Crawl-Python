import easyocr
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys, os
from config.config import Config

# Tắt log cảnh báo của EasyOCR
sys.stderr = open(os.devnull, 'w')


class ProcessImage:
    def __init__(self, langs=['en', 'vi']):
        self.config = Config()

        # Đọc cấu hình
        use_gpu = self.config.get("ocr.use_gpu", False)
        self.background_color = tuple(self.config.get("ocr.background_color", [0, 0, 0]))
        self.text_color = tuple(self.config.get("ocr.text_color", [255, 255, 255]))
        self.font_path = self.config.get("ocr.font_path", "C:/Windows/Fonts/arial.ttf")

        # Khởi tạo EasyOCR
        self.reader = easyocr.Reader(langs, gpu=use_gpu)

    def replace_text(self, image_path, find_text, new_text, output_path):
        # Đọc ảnh gốc
        img_cv = cv2.imread(image_path)
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # Nhận diện chữ
        results = self.reader.readtext(image_path)
        found = False

        for detection in results:
            text = detection[1]
            if find_text.lower() in text.lower():
                found = True
                bbox = detection[0]

                # Tính vùng chữ
                x_min = int(min([p[0] for p in bbox]))
                y_min = int(min([p[1] for p in bbox]))
                x_max = int(max([p[0] for p in bbox]))
                y_max = int(max([p[1] for p in bbox]))

                w = x_max - x_min
                h = y_max - y_min

                # Nới rộng vùng nền cho dễ nhìn
                padding = int(h * 0.1)
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(img_pil.width, x_max + padding)
                y_max = min(img_pil.height, y_max + padding)
                w = x_max - x_min
                h = y_max - y_min

              
                draw.rectangle([x_min, y_min, x_max, y_max], fill=self.background_color)

               
                font_size = h
                try:
                    font = ImageFont.truetype(self.font_path, font_size)
                except:
                    font = ImageFont.load_default()

                text_w, text_h = draw.textbbox((0, 0), new_text, font=font)[2:]
                while text_w > w and font_size > 5:
                    font_size -= 1
                    font = ImageFont.truetype(self.font_path, font_size)
                    text_w, text_h = draw.textbbox((0, 0), new_text, font=font)[2:]
                text_x = x_min + (w - text_w) // 2
                text_y = y_min + (h - text_h) // 2
                if "t.me" in text.lower():
                    new_text="T.me/"+new_text+"_bot" 
                    draw.text((text_x, text_y), new_text, font=font, fill=self.text_color)
                else:
                    new_text = new_text+".io"
                    draw.text((text_x, text_y), new_text, font=font, fill=self.text_color)
       
        if not found:
            font = ImageFont.truetype(self.font_path, 40)
            draw.text((20, 20), new_text, font=font, fill=self.text_color)


        img_out = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, img_out)
        print(f"✅ Ảnh đã lưu tại: {output_path}")


if __name__ == "__main__":
    processor = ProcessImage()
    processor.replace_text(
        image_path="5.jpg",
        find_text="hieu",
        new_text="SNOWELL",
        output_path="output.jpg"
    )
