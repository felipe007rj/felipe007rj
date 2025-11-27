"""Serviço de OCR com Google Document AI."""

from google.api_core.exceptions import GoogleAPIError


class OCRService:
    """Gerencia operações de OCR com Google Document AI."""
    
    def __init__(self, documentai_client, project: str, location: str, processor_id: str):
        """Inicializa o serviço de OCR."""
        self.client = documentai_client
        self.processor_name = (
            f"projects/{project}/locations/{location}/processors/{processor_id}"
        )
    
    def process_pdf(self, pdf_bytes: bytes) -> str:
        """
        Realiza OCR em um PDF usando Google Document AI.
        
        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            
        Returns:
            Texto extraído do PDF
        """
        try:
            doc = {"content": pdf_bytes, "mime_type": "application/pdf"}
            request = {
                "name": self.processor_name,
                "raw_document": doc,
            }
            result = self.client.process_document(request=request)
            text = result.document.text or ""
            print("OCR completed successfully.")
            return text
        except GoogleAPIError as e:
            print(f"Google API error during OCR: {e}")
            return ""
        except Exception as e:
            print(f"General error during OCR: {e}")
            return ""

    # Compatibilidade com código legado
    def process_document(self, pdf_bytes: bytes) -> str:
        """Mantém compatibilidade com assinatura anterior."""
        return self.process_pdf(pdf_bytes)
