"""文档加载器 - 解析 PDF/DOCX/MD/TXT 提取纯文本"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    文档加载器

    支持格式：txt, md, pdf, docx
    返回纯文本字符串，供后续分块和向量化。
    """

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

    def load(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {self.SUPPORTED_EXTENSIONS}")

        if ext in (".txt", ".md"):
            return self._load_text(path)
        elif ext == ".pdf":
            return self._load_pdf(path)
        elif ext == ".docx":
            return self._load_docx(path)

    def load_bytes(self, content: bytes, filename: str) -> str:
        """从字节流加载，用于文件上传场景"""
        ext = Path(filename).suffix.lower()
        if ext in (".txt", ".md"):
            return content.decode("utf-8", errors="ignore")
        elif ext == ".pdf":
            return self._load_pdf_bytes(content)
        elif ext == ".docx":
            return self._load_docx_bytes(content)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def _load_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def _load_pdf(self, path: Path) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except ImportError:
            logger.warning("PyPDF2 未安装，无法解析 PDF")
            raise

    def _load_pdf_bytes(self, content: bytes) -> str:
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except ImportError:
            logger.warning("PyPDF2 未安装，无法解析 PDF")
            raise

    def _load_docx(self, path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx 未安装，无法解析 DOCX")
            raise

    def _load_docx_bytes(self, content: bytes) -> str:
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx 未安装，无法解析 DOCX")
            raise
