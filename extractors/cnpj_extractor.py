"""
Extractor para CNPJ de documentos OCR.
Responsável por extrair e normalizar CNPJs.
"""

import re
from typing import Optional


class CNPJExtractor:
    """Extrai e normaliza CNPJs de texto OCR."""
    
    # Comprimento esperado de CNPJ (14 dígitos)
    CNPJ_LENGTH = 14
    
    # Índices para formatação CNPJ (XX.XXX.XXX/XXXX-XX)
    FIRST_BLOCK_END = 2
    SECOND_BLOCK_END = 5
    THIRD_BLOCK_END = 8
    FOURTH_BLOCK_END = 12
    
    def __init__(self):
        """Inicializa o extractor de CNPJ."""
        self.cnpj_patterns = [
            r'\b(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})\b',  # XX.XXX.XXX/XXXX-XX ou variações
            r'\b(\d{14})\b',  # 14 dígitos consecutivos
            r'CNPJ[:\s-]*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})',  # Após label "CNPJ"
            r'SEDE[:\s-]*(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})',   # Após label "SEDE"
        ]
    
    def extract_from_ocr(self, ocr_text: str) -> str:
        """
        Extrai CNPJ do texto OCR usando regex patterns.
        Procura por 14 dígitos consecutivos que podem ter pontos, barras e hífens.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            CNPJ extraído ou string vazia se não encontrado
        """
        if not ocr_text:
            return ""
        
        for pattern in self.cnpj_patterns:
            matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
            for match in matches:
                cnpj_raw = match.group(1)
                cnpj_digits = re.sub(r'\D', '', cnpj_raw)
                if len(cnpj_digits) == self.CNPJ_LENGTH:
                    return self.normalize(cnpj_digits)
        
        return ""
    
    def normalize(self, cnpj: str) -> str:
        """
        Normaliza CNPJ para o formato padrão XX.XXX.XXX/XXXX-XX.
        Remove caracteres não numéricos e aplica formatação.
        
        Args:
            cnpj: CNPJ em qualquer formato
            
        Returns:
            CNPJ formatado ou string vazia se inválido
        """
        if not cnpj:
            return ""
        
        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', cnpj)
        
        # Valida comprimento
        if len(digits) != self.CNPJ_LENGTH:
            return ""
        
        # Formata: XX.XXX.XXX/XXXX-XX
        formatted = (
            f"{digits[:self.FIRST_BLOCK_END]}."
            f"{digits[self.FIRST_BLOCK_END:self.SECOND_BLOCK_END]}."
            f"{digits[self.SECOND_BLOCK_END:self.THIRD_BLOCK_END]}/"
            f"{digits[self.THIRD_BLOCK_END:self.FOURTH_BLOCK_END]}-"
            f"{digits[self.FOURTH_BLOCK_END:]}"
        )
        
        return formatted
    
    def validate(self, cnpj: str) -> bool:
        """
        Valida se uma string é um CNPJ válido (formato estrutural, não dígitos verificadores).
        
        Args:
            cnpj: CNPJ para validar
            
        Returns:
            True se válido estruturalmente, False caso contrário
        """
        if not cnpj:
            return False
        
        digits = re.sub(r'\D', '', cnpj)
        return len(digits) == self.CNPJ_LENGTH and digits.isdigit()
