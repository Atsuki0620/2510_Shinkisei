"""
PDF処理ユーティリティ

特許明細書PDFからテキストを抽出する機能を提供します。
"""

import fitz  # PyMuPDF
from typing import Dict, List, Optional
import io


class PDFProcessor:
    """PDFファイルからテキストを抽出するクラス"""

    def __init__(self, max_file_size_mb: int = 20):
        """
        初期化

        Args:
            max_file_size_mb: 最大ファイルサイズ（MB）
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def extract_text_from_pdf(self, pdf_file) -> Dict[str, any]:
        """
        PDFファイルからテキストを抽出

        Args:
            pdf_file: Streamlitのアップロードファイルオブジェクト

        Returns:
            Dict: 抽出結果
                - success: bool
                - filename: str
                - file_size: int
                - page_count: int
                - text_content: str
                - error: str (エラー時のみ)
        """
        try:
            # ファイルサイズチェック
            pdf_file.seek(0, 2)  # ファイル末尾に移動
            file_size = pdf_file.tell()
            pdf_file.seek(0)  # ファイル先頭に戻る

            if file_size > self.max_file_size_bytes:
                return {
                    "success": False,
                    "filename": pdf_file.name,
                    "error": f"ファイルサイズが上限（{self.max_file_size_mb}MB）を超えています"
                }

            # PDFを読み込み
            pdf_bytes = pdf_file.read()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            # ページ数を先に取得
            page_count = pdf_document.page_count

            # 全ページからテキストを抽出
            text_content = ""
            for page_num in range(page_count):
                page = pdf_document[page_num]
                text_content += page.get_text()

            pdf_document.close()

            return {
                "success": True,
                "filename": pdf_file.name,
                "file_size": file_size,
                "page_count": page_count,
                "text_content": text_content.strip()
            }

        except Exception as e:
            return {
                "success": False,
                "filename": pdf_file.name if hasattr(pdf_file, 'name') else "unknown",
                "error": f"PDF処理エラー: {str(e)}"
            }

    def process_multiple_pdfs(self, pdf_files: List) -> List[Dict]:
        """
        複数のPDFファイルを処理

        Args:
            pdf_files: PDFファイルのリスト

        Returns:
            List[Dict]: 各PDFの抽出結果のリスト
        """
        results = []
        for pdf_file in pdf_files:
            result = self.extract_text_from_pdf(pdf_file)
            results.append(result)
        return results

    def validate_pdf_content(self, text_content: str, min_length: int = 100) -> bool:
        """
        抽出されたテキストの妥当性チェック

        Args:
            text_content: 抽出されたテキスト
            min_length: 最小文字数

        Returns:
            bool: 妥当な場合True
        """
        if not text_content or len(text_content.strip()) < min_length:
            return False
        return True


def format_file_size(size_bytes: int) -> str:
    """
    ファイルサイズを読みやすい形式に変換

    Args:
        size_bytes: バイト数

    Returns:
        str: フォーマットされたサイズ（例: "2.3 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
