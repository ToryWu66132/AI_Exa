import re

def clean_text(text):
    text = re.sub(r"\s+", " ", text)  # 去多余空白
    text = re.sub(r"<.*?>", "", text)  # 去HTML
    return text.strip()