"""Utilitários para manipulação de texto."""

import unicodedata
import re


class TextUtils:
    """Utilitários de texto."""
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normaliza texto Unicode (remove acentos).
        
        Args:
            text: Texto a normalizar
            
        Returns:
            Texto normalizado
        """
        if not text:
            return ""
        
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpa texto removendo espaços extras e quebras de linha.
        
        Args:
            text: Texto a limpar
            
        Returns:
            Texto limpo
        """
        if not text:
            return ""
        
        # Substituir múltiplas quebras de linha por espaço
        text = re.sub(r'\n+', ' ', text)
        # Substituir múltiplos espaços por um único espaço
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def remove_markdown_bold(text: str) -> str:
        """
        Remove marcadores de negrito do markdown (asteriscos).
        
        Args:
            text: Texto com markdown
            
        Returns:
            Texto sem asteriscos
        """
        if not text:
            return ""
        
        return text.replace('*', '').strip()
