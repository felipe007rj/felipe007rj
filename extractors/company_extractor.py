"""
Extractor para dados de empresas em documentos OCR.
Responsável por extrair razão social, natureza jurídica, endereço e junta comercial.
"""

import re
from typing import Optional


class CompanyExtractor:
    """Extrai dados de empresas de texto OCR."""
    
    # Sufixos corporativos comuns
    COMPANY_SUFFIXES = [
        'LTDA', 'S.A.', 'SA', 'S/A', 'EIRELI', 'MEI', 'EI', 
        'LTDA.', 'EPP', 'ME', 'MICROEMPRESA', 'EMPRESA DE PEQUENO PORTE',
        'SOCIEDADE SIMPLES', 'SS', 'COOPERATIVA', 'COOP',
        'FUNDACAO', 'ASSOCIACAO', 'OSCIP', 'ONG',
        'EMPRESA INDIVIDUAL DE RESPONSABILIDADE LIMITADA',
        'MICROEMPREENDEDOR INDIVIDUAL', 'EMPRESARIO INDIVIDUAL'
    ]
    
    # Mapeamento de Juntas Comerciais
    JUNTAS_COMERCIAIS = [
        (r"JUCESP|Junta Comercial do Estado de São Paulo", "Junta Comercial do Estado de São Paulo (JUCESP)"),
        (r"JUCERJA|Junta Comercial do Estado do Rio de Janeiro", "Junta Comercial do Estado do Rio de Janeiro (JUCERJA)"),
        (r"JUCEMG|Junta Comercial do Estado de Minas Gerais", "Junta Comercial do Estado de Minas Gerais (JUCEMG)"),
        (r"JUCEPAR|Junta Comercial do Estado do Paraná", "Junta Comercial do Estado do Paraná (JUCEPAR)"),
        (r"JUCERGS|Junta Comercial do Estado do Rio Grande do Sul", "Junta Comercial do Estado do Rio Grande do Sul (JUCERGS)"),
        (r"JUCESC|Junta Comercial do Estado de Santa Catarina", "Junta Comercial do Estado de Santa Catarina (JUCESC)"),
        (r"JUCEB|Junta Comercial do Estado da Bahia", "Junta Comercial do Estado da Bahia (JUCEB)"),
        (r"JUCEPE|Junta Comercial do Estado de Pernambuco", "Junta Comercial do Estado de Pernambuco (JUCEPE)"),
        (r"JUCEC|Junta Comercial do Estado do Ceará", "Junta Comercial do Estado do Ceará (JUCEC)"),
        (r"JCDF|Junta Comercial do Distrito Federal", "Junta Comercial do Distrito Federal (JCDF)")
    ]
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    def __init__(self):
        """Inicializa o extractor de dados de empresa."""
        self._build_patterns()
    
    def _build_patterns(self):
        """Constrói os padrões regex para extração."""
        suffixes_pattern = r'(?:LTDA|S\.A\.|SA|S/A|EIRELI|MEI|EI|LTDA\.|EPP|ME|SOCIEDADE SIMPLES|SS)'
        
        self.razao_social_patterns = [
            r'NOME EMPRESARIAL[:\s\n]+([A-Z][A-Z\s&\'-\.]+' + suffixes_pattern + r'\.?)',
            r'RAZ[AÃ]O SOCIAL[:\s\n]+([A-Z][A-Z\s&\'-\.]+' + suffixes_pattern + r'\.?)',
            r'EMPRESA[:\s\n]+([A-Z][A-Z\s&\'-\.]+' + suffixes_pattern + r'\.?)',
            r'\b([A-Z][A-Z\s&\'-\.]{10,}' + suffixes_pattern + r'\.?)\b'
        ]
        
        # Padrões para S.A. com espaços/pontos variáveis
        self.sa_patterns = [
            r'S\s*\.\s*A\s*\.',  # S . A .
            r'S\s*\.\s*A\b',      # S . A (sem ponto final)
            r'S\s*/\s*A\b',       # S / A
        ]
    
    def extract_razao_social(self, ocr_text: str) -> str:
        """
        Extrai Razão Social do texto OCR usando padrões comuns.
        Procura por nomes de empresa próximos a labels ou com sufixos corporativos.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Razão social extraída ou string vazia se não encontrado
        """
        if not ocr_text:
            return ""
        
        for pattern in self.razao_social_patterns:
            matches = re.finditer(pattern, ocr_text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                razao = match.group(1).strip()
                # Remove excesso de espaços
                razao = re.sub(r'\s+', ' ', razao)
                if len(razao) > 5:  # Nome muito curto provavelmente é inválido
                    return razao
        
        return ""
    
    def extract_natureza_juridica(self, razao_social: str) -> str:
        """
        Extrai o tipo de empresa (LTDA, SA, EIRELI, etc.) da razão social.
        
        Args:
            razao_social: Razão social da empresa
            
        Returns:
            Natureza jurídica extraída ou mensagem padrão se não encontrado
        """
        if not razao_social:
            return self.DATA_NOT_AVAILABLE
        
        razao_upper = razao_social.upper()
        
        # PRIMEIRA TENTATIVA: Buscar padrões específicos de S.A.
        for pattern in self.sa_patterns:
            if re.search(pattern, razao_upper):
                return "S.A."
        
        # SEGUNDA TENTATIVA: Normalizar removendo espaços extras
        razao_normalized = re.sub(r'(?<=\w)\s+(?=\w)', '', razao_upper)
        
        # Buscar tipos de empresa (em ordem de prioridade)
        for company_type in self.COMPANY_SUFFIXES:
            # Buscar como palavra isolada
            pattern = r'\b' + re.escape(company_type) + r'\b'
            if re.search(pattern, razao_normalized):
                return company_type
        
        return self.DATA_NOT_AVAILABLE
    
    def extract_junta_comercial(self, ocr_text: str) -> Optional[str]:
        """
        Extrai o nome da Junta Comercial do texto OCR.
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Nome da Junta Comercial ou None se não encontrado
        """
        if not ocr_text:
            return None
        
        text_upper = ocr_text.upper()
        
        for pattern, junta_name in self.JUNTAS_COMERCIAIS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return junta_name
        
        return None
    
    def extract_endereco(self, ocr_text: str) -> str:
        """
        Extrai endereço da sede da empresa.
        (Implementação simplificada - pode ser expandida conforme necessário)
        
        Args:
            ocr_text: Texto extraído via OCR
            
        Returns:
            Endereço extraído ou string vazia
        """
        if not ocr_text:
            return ""
        
        # Padrões comuns de endereço
        endereco_patterns = [
            r'ENDERE[ÇC]O[:\s\n]+([^\n]{20,100})',
            r'SEDE[:\s\n]+([^\n]{20,100})',
            r'LOCALIZADA?\s+(?:NA|NO|EM)\s+([^\n]{20,100})',
        ]
        
        for pattern in endereco_patterns:
            matches = re.finditer(pattern, ocr_text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                endereco = match.group(1).strip()
                # Remove excesso de espaços
                endereco = re.sub(r'\s+', ' ', endereco)
                if len(endereco) > 15:
                    return endereco
        
        return ""
