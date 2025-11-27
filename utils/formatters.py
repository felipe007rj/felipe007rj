"""Formatadores para CNPJ, datas e outros dados."""

import re
from typing import Optional
from datetime import datetime
import unicodedata

from config.settings import (
    CNPJ_LENGTH,
    CNPJ_FIRST_BLOCK_END,
    CNPJ_SECOND_BLOCK_END,
    CNPJ_THIRD_BLOCK_END,
    CNPJ_FOURTH_BLOCK_END,
    ISO_DATE_PATTERN,
    MONTH_DATE_PATTERN,
    MONTH_NAMES
)


class Formatters:
    """Formatadores de dados."""
    
    @staticmethod
    def normalize_cnpj(s: str) -> str:
        """
        Normaliza CNPJ para o formato XX.XXX.XXX/XXXX-XX.
        
        Args:
            s: String contendo o CNPJ
            
        Returns:
            CNPJ formatado ou string original se inválido
        """
        if not s:
            return ""
        
        digits = re.sub(r"\D", "", s)
        if len(digits) != CNPJ_LENGTH:
            return s
        
        return (f"{digits[0:CNPJ_FIRST_BLOCK_END]}."
                f"{digits[CNPJ_FIRST_BLOCK_END:CNPJ_SECOND_BLOCK_END]}."
                f"{digits[CNPJ_SECOND_BLOCK_END:CNPJ_THIRD_BLOCK_END]}/"
                f"{digits[CNPJ_THIRD_BLOCK_END:CNPJ_FOURTH_BLOCK_END]}-"
                f"{digits[CNPJ_FOURTH_BLOCK_END:CNPJ_LENGTH]}")
    
    @staticmethod
    def normalize_date(text: str) -> Optional[str]:
        """
        Normaliza várias formatos de data para ISO (YYYY-MM-DD).
        
        Args:
            text: Texto contendo a data
            
        Returns:
            Data no formato ISO ou None se inválida
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Já está em ISO?
        if re.match(ISO_DATE_PATTERN, text):
            return text
        
        # DD/MM/YYYY ou DD-MM-YYYY
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
            return f"{y}-{mo:02d}-{d:02d}"
        
        # DD de MONTH de YYYY
        m2 = re.search(MONTH_DATE_PATTERN, text, re.IGNORECASE)
        if m2:
            d, mes, y = m2.group(1), m2.group(2).lower(), m2.group(3)
            mes = unicodedata.normalize("NFKD", mes).encode("ascii", "ignore").decode()
            mm = MONTH_NAMES.get(mes)
            if mm:
                return f"{y}-{mm}-{int(d):02d}"
        
        return None
    
    @staticmethod
    def iso_to_br_date(iso_date: str) -> str:
        """
        Converte data ISO (YYYY-MM-DD) para formato brasileiro (DD/MM/YYYY).
        
        Args:
            iso_date: Data no formato ISO
            
        Returns:
            Data no formato DD/MM/YYYY
        """
        if not iso_date or not re.match(ISO_DATE_PATTERN, iso_date):
            return iso_date
        
        year, month, day = iso_date.split('-')
        return f"{day}/{month}/{year}"
