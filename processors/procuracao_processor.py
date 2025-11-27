"""
Processor para procurações e poderes.
Responsável por extrair e processar informações de procurações.
"""

import re
from typing import Dict, List, Any, Optional


class ProcuracaoProcessor:
    """Processa procurações e poderes de representantes."""
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    def __init__(self):
        """Inicializa o processor de procurações."""
        pass
    
    def augment_with_procuracao(self, ocr_full: str, data_out: Dict[str, Any], 
                                date_extractor) -> Dict[str, Any]:
        """
        Enriquece dados com informações de procuração detectadas no OCR.
        
        Args:
            ocr_full: Texto OCR completo
            data_out: Dicionário de dados atual
            date_extractor: Instância de DateExtractor
            
        Returns:
            Dicionário enriquecido
        """
        # Detectar se há procuração
        if not self._has_procuracao(ocr_full):
            return data_out
        
        print("📋 Procuração detectada no OCR - extraindo informações")
        
        # Extrair nomes de procuradores
        nomes = self._extract_attorney_names(ocr_full)
        
        # Extrair data de validade
        validade = date_extractor.extract_validity_date(ocr_full)
        
        # Extrair data da procuração
        data_procuracao = self._extract_procuracao_date(ocr_full)
        
        # Adicionar procuradores aos representantes (apenas para informação)
        # NÃO adicionar aos representantes_detalhados (filtrados)
        if nomes:
            self._add_attorneys_to_representatives(data_out, nomes, validade)
        
        # Adicionar informação de validade às regras
        if validade:
            self._add_validity_to_rules(data_out, validade)
        
        return data_out
    
    def extract_validity_from_regras_text(self, regras: str) -> Optional[str]:
        """
        Busca informações de validade dentro do texto de regras.
        
        Args:
            regras: Texto das regras de representação
            
        Returns:
            String com informação de validade ou None
        """
        if not regras or regras.strip() == self.DATA_NOT_AVAILABLE:
            return None
        
        # Normalizar
        regras_lower = regras.lower()
        
        # Palavras-chave de validade
        keywords = ["mandato", "prazo", "vigencia", "vigência", "validade", "duracao", "duração"]
        
        if not any(keyword in regras_lower for keyword in keywords):
            return None
        
        # Quebrar em sentenças
        candidatos = re.split(r'[\n\.]+', regras)
        for trecho in candidatos:
            trecho_lower = trecho.lower()
            if any(keyword in trecho_lower for keyword in keywords):
                # Encontrou sentença com palavra-chave
                return trecho.strip()
        
        return None
    
    def _has_procuracao(self, ocr_text: str) -> bool:
        """Detecta se há procuração no texto."""
        return bool(re.search(r'procura[çc][ãa]o', ocr_text, re.IGNORECASE))
    
    def _extract_attorney_names(self, ocr_full: str) -> List[str]:
        """
        Extrai nomes de procuradores/outorgados do OCR.
        
        Args:
            ocr_full: Texto OCR completo
            
        Returns:
            Lista de nomes extraídos
        """
        nomes = []
        
        # Padrões para identificar procuradores
        patterns = [
            r'outorgado[:\s]+([A-Z][a-zA-Z\s]+)',
            r'procurador[:\s]+([A-Z][a-zA-Z\s]+)',
            r'mandatário[:\s]+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, ocr_full, re.IGNORECASE)
            for match in matches:
                nome = match.group(1).strip()
                # Limpar nome (remover excesso de espaços)
                nome = re.sub(r'\s+', ' ', nome)
                if len(nome) > 5 and nome not in nomes:
                    nomes.append(nome)
        
        return nomes
    
    def _extract_procuracao_date(self, ocr_full: str) -> Optional[str]:
        """
        Extrai data da procuração.
        
        Args:
            ocr_full: Texto OCR completo
            
        Returns:
            Data extraída ou None
        """
        # Padrões de data após "procuração"
        patterns = [
            r'procura[çc][ãa]o.*?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'outorgada\s+em\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ocr_full, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _add_attorneys_to_representatives(self, data_out: Dict[str, Any], 
                                         nomes: List[str], validade_iso: Optional[str]) -> None:
        """Adiciona procuradores aos representantes (apenas informativamente)."""
        if not nomes:
            return
        
        current_representatives = data_out.get("representantes_legais", "")
        separator = self._get_separator_for_representatives(current_representatives)
        
        attorneys_str = separator.join(f"{nome} (Procurador)" for nome in nomes)
        
        if current_representatives:
            data_out["representantes_legais"] += separator + attorneys_str
        else:
            data_out["representantes_legais"] = attorneys_str
    
    def _add_validity_to_rules(self, data_out: Dict[str, Any], 
                              validade_iso: Optional[str]) -> None:
        """Adiciona informação de validade às regras de representação."""
        if not validade_iso:
            return
        
        validity_note = f"Validade da procuração: {validade_iso}"
        
        current_rules = data_out.get("poderes_e_representacao", "")
        if current_rules and current_rules != self.DATA_NOT_AVAILABLE:
            data_out["poderes_e_representacao"] += f". {validity_note}"
        else:
            data_out["poderes_e_representacao"] = validity_note
    
    def _get_separator_for_representatives(self, current_representatives: str) -> str:
        """Determina o separador apropriado para representantes."""
        if not current_representatives:
            return ""
        if '\n' in current_representatives:
            return '\n'
        return ', '
