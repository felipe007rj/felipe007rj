"""Modelo de dados para Receipt (recibo de processamento)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Receipt:
    """Representa um recibo de processamento de mensagem."""
    
    request_id: Optional[str] = None
    message: Optional[Dict[str, Any]] = None
    ocr_data: List[Dict[str, Any]] = field(default_factory=list)
    genai_data: Optional[Dict[str, Any]] = None
    output_response: Optional[str] = None
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    document_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o receipt para dicionário."""
        return {
            'request_id': self.request_id,
            'message': self.message,
            'ocr_data': self.ocr_data,
            'genai_data': self.genai_data,
            'output_response': self.output_response,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'document_info': self.document_info
        }
