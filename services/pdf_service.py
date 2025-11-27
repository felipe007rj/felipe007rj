"""Serviço de manipulação de PDFs."""

import io
from typing import List, Tuple
from pypdf import PdfReader, PdfWriter


class PDFService:
    """Gerencia operações com arquivos PDF."""
    
    @staticmethod
    def split_pdf(pdf_bytes: bytes, max_pages: int = 15) -> Tuple[List[bytes], int]:
        """
        Divide um PDF em chunks de até max_pages páginas cada.
        
        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            max_pages: Número máximo de páginas por chunk
            
        Returns:
            Tupla com (lista de PDFs em bytes, número total de páginas)
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            num_pages = len(reader.pages)
            
            if num_pages <= max_pages:
                print(f"PDF has {num_pages} pages, no split needed.")
                return [pdf_bytes], num_pages
            
            chunks = []
            for start in range(0, num_pages, max_pages):
                writer = PdfWriter()
                for i in range(start, min(start + max_pages, num_pages)):
                    writer.add_page(reader.pages[i])
                
                output = io.BytesIO()
                writer.write(output)
                chunks.append(output.getvalue())
            
            print(f"PDF split into {len(chunks)} chunks.")
            return chunks, num_pages
        except Exception as e:
            print(f"Error splitting PDF: {e}")
            return [], 0

    # Compatibilidade com código legado
    @staticmethod
    def split_pdf_if_needed(pdf_bytes: bytes, max_pages: int = 15) -> Tuple[List[bytes], int]:
        """Mantém compatibilidade com assinaturas antigas."""
        return PDFService.split_pdf(pdf_bytes, max_pages=max_pages)
