"""Modelo de dados para metadados de documento."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentMetadata:
    """Metadados de um documento processado."""
    
    document_index: int
    file_name: str
    document_type: str
    signature_date: Optional[str] = None
    registration_date: Optional[str] = None
    document_number: Optional[str] = None
    priority_score: int = 0
    
    def to_dict(self) -> dict:
        """Converte os metadados para dicionário."""
        return {
            'document_index': self.document_index,
            'file_name': self.file_name,
            'document_type': self.document_type,
            'signature_date': self.signature_date,
            'registration_date': self.registration_date,
            'document_number': self.document_number,
            'priority_score': self.priority_score
        }
