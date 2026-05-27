def chunk_text(text, chunk_size=300, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        # 按照字符切块
        end = start + chunk_size
        chunks.append(text[start:end])
        # 支持overlap
        start += chunk_size - overlap

    return chunks