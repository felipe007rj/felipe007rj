"""
Extractor para datas em documentos.
Responsável por extrair e normalizar datas de assinatura, validade e mandato.
"""

import re
import unicodedata
from datetime import datetime
from typing import List, Optional, Tuple


class DateExtractor:
    """Extrai e normaliza datas de documentos OCR e texto."""
    
    # Padrões de data
    EXTENDED_DATE_PATTERN = r"\d+\s+de\s+[a-z]+\s+de\s+\d{4}"
    SIMPLE_DATE_PATTERN = r"(\d{1,2}/\d{1,2}/\d{4})"
    MONTH_DATE_PATTERN = r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})"
    ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
    
    # Mapeamento de meses
    MONTH_NAMES = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08', 'setembro': '09',
        'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    
    def __init__(self):
        """Inicializa o extractor de datas."""
        pass
    
    def normalize_any(self, text: str) -> Optional[str]:
        """
        Normaliza qualquer formato de data para YYYY-MM-DD.
        
        Args:
            text: Texto contendo data
            
        Returns:
            Data normalizada em formato ISO ou None
        """
        if not text or not isinstance(text, str):
            return None
        
        text = text.strip()
        
        # Já está no formato ISO
        if re.match(self.ISO_DATE_PATTERN, text):
            return text
        
        # Formato simples: DD/MM/YYYY
        match = re.search(self.SIMPLE_DATE_PATTERN, text)
        if match:
            day, month, year = match.group(1).split('/')
            if self._is_valid_date(day, month, year):
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Formato extenso: DD de MÊS de YYYY
        match = re.search(self.MONTH_DATE_PATTERN, text, re.IGNORECASE)
        if match:
            day = match.group(1)
            month_name = match.group(2).lower()
            year = match.group(3)
            
            month = self.MONTH_NAMES.get(month_name)
            if month and self._is_valid_date(day, month, year):
                return f"{year}-{month}-{day.zfill(2)}"
        
        return None
    
    def extract_signature_date_level_0(self, ocr_text: str) -> Optional[str]:
        """
        NÍVEL 0: Busca direta por padrões de assinatura com alta confiança.
        Busca frases explícitas como "assinado em", "firmado em", etc.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Data de assinatura normalizada ou None
        """
        if not ocr_text:
            return None
        
        # Normalizar texto
        text_normalized = unicodedata.normalize("NFKD", ocr_text)
        text_lower = text_normalized.lower()
        
        # Padrões de assinatura com contexto explícito
        signature_patterns = [
            # Padrão: "assinado em DD/MM/YYYY"
            r"assinado\s+em\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            # Padrão: "firmado em DD/MM/YYYY"
            r"firmado\s+em\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            # Padrão: "subscrito em DD/MM/YYYY"
            r"subscrito\s+em\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            # Padrão: "datado de DD/MM/YYYY"
            r"datado\s+de\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            # Padrão: "São Paulo, DD/MM/YYYY"
            r"São\s+Paulo,?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            # Padrão: "assinado em DD de MÊS de YYYY"
            r"assinado\s+em\s+(\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4})",
            # Padrão: "firmado em DD de MÊS de YYYY"
            r"firmado\s+em\s+(\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4})",
        ]
        
        for pattern in signature_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                date_str = match.group(1)
                normalized = self.normalize_any(date_str)
                if normalized:
                    return normalized
        
        return None
    
    def find_signature_date_by_proximity(self, ocr_text: str) -> Optional[str]:
        """
        Busca data de assinatura por proximidade com seções de assinatura.
        Identifica seções com palavras-chave (assinatura, testemunha, etc.)
        e busca datas próximas com análise de nomes.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Data de assinatura normalizada ou None
        """
        if not ocr_text:
            return None
        
        # Normalizar texto
        text_normalized = unicodedata.normalize("NFKD", ocr_text)
        
        # Lista para armazenar candidatos
        dates_found: List[Tuple[str, str, int]] = []
        
        # Buscar todas as datas simples (DD/MM/YYYY)
        simple_matches = re.finditer(self.SIMPLE_DATE_PATTERN, text_normalized, re.IGNORECASE)
        for match in simple_matches:
            date_str = match.group(1)
            position = match.start()
            
            # Normalizar para análise
            normalized = self.normalize_any(date_str)
            if not normalized:
                continue
            
            # Verificar se não está em contexto de lei
            if self._is_date_in_law_context(text_normalized, date_str):
                continue
            
            # Calcular score de proximidade com seção de assinatura
            proximity_score = self._check_signature_section_proximity(text_normalized, position)
            
            # Contar nomes próximos à data
            names_count = self._count_names_near_date(text_normalized, position)
            
            # Score total: proximidade + nomes
            total_score = proximity_score + (names_count * 10)
            
            dates_found.append((normalized, date_str, total_score))
        
        # Buscar datas por extenso (DD de MÊS de YYYY)
        extended_matches = re.finditer(self.EXTENDED_DATE_PATTERN, text_normalized, re.IGNORECASE)
        for match in extended_matches:
            date_str = match.group(0)
            position = match.start()
            
            normalized = self.normalize_any(date_str)
            if not normalized:
                continue
            
            # Verificar contexto de lei
            if self._is_date_in_law_context(text_normalized, date_str):
                continue
            
            proximity_score = self._check_signature_section_proximity(text_normalized, position)
            names_count = self._count_names_near_date(text_normalized, position)
            total_score = proximity_score + (names_count * 10)
            
            dates_found.append((normalized, date_str, total_score))
        
        if not dates_found:
            return None
        
        # Ordenar por score (maior primeiro)
        dates_found.sort(key=lambda x: x[2], reverse=True)
        
        # Retornar a data com maior score
        return dates_found[0][0]
    
    def extract_validity_date(self, ocr_full: str) -> Optional[str]:
        """
        Extrai data de validade de procuração.
        
        Args:
            ocr_full: Texto completo do OCR
            
        Returns:
            Data de validade normalizada ou None
        """
        if not ocr_full:
            return None
        
        # Padrões de validade
        validity_patterns = [
            r"valid[ao].*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"vigência.*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"prazo.*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"até\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        ]
        
        text_lower = ocr_full.lower()
        
        for pattern in validity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1)
                normalized = self.normalize_any(date_str)
                if normalized:
                    return normalized
        
        return None
    
    def extract_mandate_validity_date(self, response_text: str) -> Optional[str]:
        """
        Extrai data de validade de mandato do texto de resposta Gemini.
        
        Args:
            response_text: Texto de resposta do Gemini
            
        Returns:
            Data de validade normalizada ou None
        """
        if not response_text:
            return None
        
        # Normalizar texto
        text_normalized = unicodedata.normalize("NFKD", response_text)
        text_lower = text_normalized.lower()
        
        # Padrões de validade de mandato
        mandate_patterns = [
            r"mandato.*?até\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"mandato.*?vigente\s+até\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"eleitos?\s+para\s+mandato.*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"mandato.*?encerra.*?em\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        ]
        
        for pattern in mandate_patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1)
                normalized = self.normalize_any(date_str)
                if normalized:
                    return normalized
        
        return None
    
    def find_most_recent_date_in_text(self, text: str) -> Optional[str]:
        """
        Encontra a data mais recente no texto.
        
        Args:
            text: Texto para buscar datas
            
        Returns:
            Data mais recente normalizada ou None
        """
        dates_found = []
        
        # Buscar todas as datas
        self._extract_simple_dates(text, dates_found)
        self._extract_extended_dates(text, dates_found)
        
        if not dates_found:
            return None
        
        # Ordenar por data (mais recente primeiro)
        dates_found.sort(key=lambda x: x[0], reverse=True)
        return dates_found[0][1]  # Retornar formato de exibição
    
    def _extract_simple_dates(self, text: str, dates_found: List[Tuple[str, str]]) -> None:
        """Extrai datas simples (DD/MM/YYYY) e adiciona à lista."""
        matches = re.finditer(self.SIMPLE_DATE_PATTERN, text)
        for match in matches:
            date_str = match.group(1)
            normalized = self.normalize_any(date_str)
            if normalized:
                dates_found.append((normalized, date_str))
    
    def _extract_extended_dates(self, text: str, dates_found: List[Tuple[str, str]]) -> None:
        """Extrai datas por extenso e adiciona à lista."""
        matches = re.finditer(self.EXTENDED_DATE_PATTERN, text, re.IGNORECASE)
        for match in matches:
            date_str = match.group(0)
            normalized = self.normalize_any(date_str)
            if normalized:
                dates_found.append((normalized, date_str))
    
    def _is_valid_date(self, day: str, month: str, year: str) -> bool:
        """Valida se uma data é válida."""
        try:
            datetime(int(year), int(month), int(day))
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_date_in_law_context(self, text: str, date_str: str) -> bool:
        """
        Verifica se uma data está em contexto de lei (ex: "Lei 123/2024").
        Datas de leis devem ser ignoradas para assinatura.
        """
        # Buscar "Lei" ou "Decreto" próximo à data
        date_position = text.find(date_str)
        if date_position == -1:
            return False
        
        # Janela de contexto (100 caracteres antes)
        window_start = max(0, date_position - 100)
        context = text[window_start:date_position]
        
        law_keywords = ['lei', 'decreto', 'portaria', 'resolução', 'medida provisória']
        context_lower = context.lower()
        
        return any(keyword in context_lower for keyword in law_keywords)
    
    def _count_names_near_date(self, text: str, date_position: int, window_size: int = 500) -> int:
        """
        Conta quantos nomes próprios existem próximos a uma data.
        Indicador de que a data está em seção de assinatura.
        """
        window_start = max(0, date_position - window_size)
        window_end = min(len(text), date_position + window_size)
        context = text[window_start:window_end]
        
        # Padrão simples: palavras iniciadas com maiúscula (potencialmente nomes)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        matches = re.findall(name_pattern, context)
        
        return len(matches)
    
    def _check_signature_section_proximity(self, text: str, position: int, window_size: int = 500) -> int:
        """
        Calcula score de proximidade com seção de assinatura.
        Score alto = mais próximo de palavras-chave de assinatura.
        """
        window_start = max(0, position - window_size)
        window_end = min(len(text), position + window_size)
        context = text[window_start:window_end].lower()
        
        signature_keywords = [
            'assinatura', 'assina', 'testemunha', 'sócio', 'administrador',
            'diretor', 'presidente', 'outorgante', 'outorgado'
        ]
        
        score = 0
        for keyword in signature_keywords:
            if keyword in context:
                score += 10
        
        return score
