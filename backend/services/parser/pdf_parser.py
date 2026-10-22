# backend/services/parser/pdf_parser.py
import pdfplumber
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流中提取纯文本"""
    text = ""
    try:
        # 使用 pdfplumber 打开字节流
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # 提取当前页的文本，并在每页末尾加个换行
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text.strip():
            return "⚠️ 未能从该 PDF 中提取到文字，可能是扫描版图片（请手动粘贴文字）。"
            
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"PDF 解析失败: {str(e)}")