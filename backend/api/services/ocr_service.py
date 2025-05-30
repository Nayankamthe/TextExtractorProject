import os
import tempfile
from datetime import datetime
from pdf2image import convert_from_path
import easyocr
import re
import numpy as np
from decouple import config
from dateutil import parser





class OCRService:
    def __init__(self, file_path):
        self.file_path = file_path
        self.reader = easyocr.Reader(['en'],gpu=False)

    def pdf_to_images(self, pdf_path):
        """Convert PDF pages to images."""
        return convert_from_path(pdf_path,poppler_path=config('poppler_path'))

    def extract_text_from_images(self, images):
        """Extract text from list of images using EasyOCR."""
        full_text = ''
        for image in images:
            np_image = np.array(image)
            result = self.reader.readtext(np_image, detail=0, paragraph=True)
            full_text += '\n'.join(result) + '\n'
        print("process text:",full_text)
        return full_text
    def extract_text_with_positions(self, images):
        results = []
        for img in images:
            results.extend(self.reader.readtext(np.array(img), detail=1))
        return results

    def parse_receipt_data(self, text, file_path):
        merchant_name = text.strip().splitlines()[0]

        total_match = re.search(r'Total\s*[:\-]?\s*\$?(\d+\.\d{2})', text, re.IGNORECASE)
        total_amount = float(total_match.group(1)) if total_match else None

        date_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{2,4})', text)
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(AM|PM)?)', text, re.IGNORECASE)

        if date_match:
            date_str = date_match.group(1)
            date_format = '%d/%m/%Y' if len(date_str.split('/')[-1]) == 4 else '%d/%m/%y'
            purchased_date = parser.parse(date_str).strftime('%d/%m/%y')
            if time_match:
                time_str = time_match.group(1)
                try:
                    purchased_datetime = datetime.strptime(f"{date_str} {time_str}", f"{date_format} %I:%M %p")
                except:
                    purchased_datetime = purchased_date
            else:
                purchased_datetime = purchased_date
        else:
            purchased_datetime = None

        return {
            "purchased_at": purchased_datetime,
            "merchant_name": merchant_name,
            "total_amount": total_amount,
            "file_path": file_path,
        }

    def process_receipt_pdf(self):
        """Main function to process a PDF and return receipt data."""
        images = self.pdf_to_images(self.file_path)
        text = self.extract_text_from_images(images)
        return self.parse_receipt_data(text, self.file_path)
    # def extract_receipt_data(self):
    #     # Dummy data for now. Integrate OCR/AI tool later (Tesseract, Google Vision, etc.)
    #     return {
    #         "purchased_at": datetime.utcnow(),
    #         "merchant_name": "ABC Store",
    #         "total_amount": 123.45,
    #         "file_path": self.file_path,
    #     }
