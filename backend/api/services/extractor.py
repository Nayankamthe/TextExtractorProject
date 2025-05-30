import json
import re
from .ocr_service import OCRService
import os

class ReceiptExtractor:
    def __init__(self,file_path, config_path=None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.json")  # works no matter where called from

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.money_regex = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")
        self.date_patterns = [
            re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
            re.compile(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'),
            re.compile(r'[A-Za-z]{3,9} \d{1,2}, \d{4}')
        ]
        self.ocr = OCRService(file_path)
        self.file_path = file_path

    def _build_keyword_set(self, keywords):
        return set(k.lower() for k in keywords)

    def _find_nearby_value(self, results, keyword_set, regex_list, direction="below", max_dist=100):
        candidates = []
        for i, (box, text, _) in enumerate(results):
            if text.lower() in keyword_set:
                x0, y0 = box[0]
                for j in range(i + 1, len(results)):
                    (b2, t2, _) = results[j]
                    x1, y1 = b2[0]
                    if direction == "below" and abs(x0 - x1) < 100 and y1 > y0 and y1 - y0 < max_dist:
                        for rgx in regex_list:
                            match = rgx.search(t2)
                            if match:
                                candidates.append((match.group(0), abs(y1 - y0)))
        return sorted(candidates, key=lambda x: x[1])[0][0] if candidates else None

    def extract_fields(self, pdf_path):
        images = self.ocr.pdf_to_images(pdf_path)
        results = self.ocr.extract_text_with_positions(images)

        total_kw = self._build_keyword_set(self.config["total_amount"])
        date_kw = self._build_keyword_set(self.config["purchase_date"])

        total_amount = self._find_nearby_value(results, total_kw, [self.money_regex])
        purchase_date = self._find_nearby_value(results, date_kw, self.date_patterns)
        merchant = results[0][1] if results else None

        return {
            "merchant_name": merchant,
            "purchased_at": purchase_date,
            "total_amount": total_amount
        }
