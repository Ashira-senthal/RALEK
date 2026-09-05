from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.extracted_text_chunks = []
        
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.extracted_text_chunks.append(text)
            
    def get_text(self):
        return ' '.join(self.extracted_text_chunks)
