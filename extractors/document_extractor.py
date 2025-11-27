"""
Extractor para metadados e tipos de documentos.
Responsável por identificar tipos de documentos, extrair nomes e metadados.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class DocumentExtractor:
    """Extrai metadados e identifica tipos de documentos."""
    
    # Tipos de documentos
    DOCUMENT_TYPES = {
        'CONTRATO_SOCIAL': 'Contrato Social',
        'ESTATUTO_SOCIAL': 'Estatuto Social',
        'ATA_DE_ASSEMBLEIA': 'Ata de Assembleia',
        'ATA_DE_ELEICAO': 'Ata de Eleição',
        'ADITAMENTO': 'Aditamento',
        'PROCURACAO': 'Procuração',
        'CERTIDAO': 'Certidão',
        'FICHA_CADASTRAL': 'Ficha Cadastral',
        'DOCUMENTO_GENERICO': 'Documento Genérico'
    }
    
    # Padrões de documentos (ordem importa - mais específico primeiro)
    DOCUMENT_PATTERNS = [
        (r'INSTRUMENTO\s+PARTICULAR\s+DE\s+(?:PRIMEIRA|SEGUNDA|TERCEIRA|QUARTA|QUINTA)?\s*ALTERA[ÇC][ÃA]O\s+(?:DO\s+)?CONTRATO\s+SOCIAL', 
         'Instrumento Particular de Alteração Contrato Social', 'CONTRATO_SOCIAL'),
        (r'INSTRUMENTO\s+PARTICULAR\s+DE\s+ALTERA[ÇC][ÃA]O', 
         'Instrumento Particular de Alteração', 'CONTRATO_SOCIAL'),
        (r'INSTRUMENTO\s+PARTICULAR', 
         'Instrumento Particular', 'CONTRATO_SOCIAL'),
        (r'CONSTITUI[ÇC][ÃA]O\s+(?:POR\s+)?(?:TRANSFORMA[ÇC][ÃA]O)?',
         'Constituição por Transformação de Empresário em Sociedade', 'CONTRATO_SOCIAL'),
        (r'ALTERA[ÇC][ÃA]O\s+CONTRATUAL', 
         'Alteração Contratual', 'CONTRATO_SOCIAL'),
        (r'ALTERA[ÇC][ÃA]O\s+(?:DO\s+)?CONTRATO\s+SOCIAL', 
         'Alteração Contrato Social', 'CONTRATO_SOCIAL'),
        (r'ADITAMENTO\s+(?:AO\s+)?CONTRATO', 
         'Aditamento ao Contrato Social', 'ADITAMENTO'),
        (r'TERMO\s+ADITIVO', 
         'Termo Aditivo', 'ADITAMENTO'),
        (r'ADITAMENTO', 
         'Aditamento', 'ADITAMENTO'),
        (r'ATA\s+(?:DA\s+)?ASSEMBLEIA\s+GERAL\s+ORDIN[AÁ]RIA\s+E\s+EXTRAORDIN[AÁ]RIA', 
         'Ata de Assembleia Geral Ordinária e Extraordinária', 'ATA_DE_ASSEMBLEIA'),
        (r'ATA\s+(?:DA\s+)?ASSEMBLEIA\s+GERAL\s+EXTRAORDIN[AÁ]RIA', 
         'Ata de Assembleia Geral Extraordinária', 'ATA_DE_ASSEMBLEIA'),
        (r'ATA\s+(?:DA\s+)?ASSEMBLEIA\s+GERAL\s+ORDIN[AÁ]RIA', 
         'Ata de Assembleia Geral Ordinária', 'ATA_DE_ASSEMBLEIA'),
        (r'ATA\s+(?:DA\s+)?ASSEMBLEIA\s+GERAL', 
         'Ata de Assembleia Geral', 'ATA_DE_ASSEMBLEIA'),
        (r'ATA\s+(?:DE\s+)?ELEI[ÇC][ÃA]O', 
         'Ata de Eleição', 'ATA_DE_ELEICAO'),
        (r'ATA\s+(?:DE\s+)?REUNI[ÃA]O', 
         'Ata de Reunião', 'ATA_DE_ASSEMBLEIA'),
        (r'ESTATUTO\s+SOCIAL(?:\s+CONSOLIDADO)?', 
         'Estatuto Social', 'ESTATUTO_SOCIAL'),
        (r'CONTRATO\s+SOCIAL', 
         'Contrato Social', 'CONTRATO_SOCIAL'),
        (r'(?:INSTRUMENTO\s+(?:P[UÚ]BLICO\s+)?(?:DE\s+)?)?PROCURA[ÇC][ÃA]O', 
         'Procuração', 'PROCURACAO'),
        (r'CERTID[ÃA]O', 
         'Certidão Simplificada', 'CERTIDAO'),
        (r'FICHA\s+CADASTRAL', 
         'Ficha Cadastral', 'FICHA_CADASTRAL'),
    ]
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    def __init__(self):
        """Inicializa o extractor de documentos."""
        pass
    
    def extract_document_name(self, ocr_text: str) -> str:
        """
        Extrai o nome completo do documento do texto OCR.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Nome do documento ou mensagem padrão
        """
        if not ocr_text:
            return self.DATA_NOT_AVAILABLE
        
        # Normalizar texto
        ocr_text_upper = ocr_text.upper()
        ocr_text_normalized = re.sub(r'\s+', ' ', ocr_text_upper)
        
        # Procurar pelos padrões na ordem
        for pattern, doc_name, _ in self.DOCUMENT_PATTERNS:
            match = re.search(pattern, ocr_text_normalized)
            if match:
                # FILTRO: NUNCA retornar Procuração
                if 'Procuração' in doc_name or 'PROCURAÇÃO' in doc_name.upper():
                    continue
                return doc_name
        
        return self.DATA_NOT_AVAILABLE
    
    def identify_document_type(self, text: str) -> str:
        """
        Identifica o tipo do documento baseado no conteúdo.
        
        Args:
            text: Texto do documento
            
        Returns:
            Código do tipo do documento
        """
        if not text:
            return 'DOCUMENTO_GENERICO'
        
        # Normalizar texto
        text_upper = text.upper()
        text_normalized = re.sub(r'\s+', ' ', text_upper)
        
        # Procurar pelos padrões
        for pattern, _, doc_type in self.DOCUMENT_PATTERNS:
            if re.search(pattern, text_normalized):
                return doc_type
        
        return 'DOCUMENTO_GENERICO'
    
    def extract_document_metadata(self, pdf_text: str, doc_index: int, uri: str, 
                                  date_extractor=None) -> Dict[str, Any]:
        """
        Extrai metadados importantes do documento para análise.
        
        Args:
            pdf_text: Texto do PDF
            doc_index: Índice do documento
            uri: URI do arquivo
            date_extractor: Instância de DateExtractor (opcional)
            
        Returns:
            Dicionário com metadados
        """
        metadata = {
            "document_index": doc_index,
            "file_name": uri.split('/')[-1] if '/' in uri else uri,
            "document_type": self.identify_document_type(pdf_text),
            "signature_date": None,
            "registration_date": None,
            "document_number": self._extract_document_number(pdf_text),
            "priority_score": 0
        }
        
        # Extrair datas se date_extractor fornecido
        if date_extractor:
            metadata["signature_date"] = date_extractor.extract_signature_date_level_0(pdf_text)
            metadata["registration_date"] = self._extract_registration_date(pdf_text, date_extractor)
        
        # Calcular score de prioridade
        metadata["priority_score"] = self._calculate_document_priority(
            metadata["signature_date"], 
            metadata["registration_date"]
        )
        
        return metadata
    
    def is_accessory_document(self, doc_type: str) -> bool:
        """
        Verifica se o documento é acessório (procuração, aditamento).
        
        Args:
            doc_type: Código do tipo do documento
            
        Returns:
            True se for documento acessório
        """
        accessory_types = ["PROCURACAO", "ADITAMENTO", "CERTIDAO", "FICHA_CADASTRAL"]
        return doc_type in accessory_types
    
    def is_corporate_document(self, doc_type: str) -> bool:
        """
        Verifica se o documento é societário principal.
        
        Args:
            doc_type: Código do tipo do documento
            
        Returns:
            True se for documento societário
        """
        corporate_types = ["ESTATUTO_SOCIAL", "ATA_DE_ASSEMBLEIA", "ATA_DE_ELEICAO", "CONTRATO_SOCIAL"]
        return doc_type in corporate_types
    
    def _extract_document_number(self, text: str) -> Optional[str]:
        """Extrai número do documento (NIRE, protocolo, etc.)."""
        if not text:
            return None
        
        number_patterns = [
            r"NIRE\s*:?\s*(\d+)",
            r"Protocolo\s*:?\s*(\d+)",
            r"Registro\s*:?\s*(\d+)"
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_registration_date(self, text: str, date_extractor) -> Optional[str]:
        """Extrai data de registro na junta comercial."""
        if not text:
            return None
        
        registration_patterns = [
            r"registrado em (\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"arquivado em (\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"protocolado em (\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"NIRE.*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})"
        ]
        
        for pattern in registration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return date_extractor.normalize_any(date_str)
        
        return None
    
    def _calculate_document_priority(self, signature_date: Optional[str], 
                                    registration_date: Optional[str]) -> int:
        """
        Calcula score de prioridade baseado nas datas.
        Documento mais recente = maior prioridade.
        """
        try:
            # Usar data de registro se disponível, senão assinatura
            date_str = registration_date or signature_date
            if not date_str:
                return 0
            
            # Converter para timestamp
            date_obj = datetime.fromisoformat(date_str)
            timestamp = int(date_obj.timestamp())
            
            return timestamp
            
        except (ValueError, AttributeError):
            return 0
