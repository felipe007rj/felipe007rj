"""
Extractor para representantes legais do texto Gemini.
Responsável por extrair e processar dados de representantes.
"""

import re
from typing import Dict, List, Optional


class RepresentativeExtractor:
    """Extrai representantes legais de texto Gemini."""
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    # Palavras-chave de procuradores (devem ser filtrados)
    PROCURADOR_KEYWORDS = ['PROCURADOR', 'OUTORGADO', 'MANDATÁRIO', 'MANDATARIO']
    
    def __init__(self):
        """Inicializa o extractor de representantes."""
        self.field_mappings = {
            'Nome:': 'nome',
            'CPF:': 'cpf',
            'Cargo:': 'cargo',
            'Endereço da residência:': 'endereco_residencia',
            'Tipo de assinatura:': 'tipo_assinatura',
            'Origem da assinatura:': 'origem_assinatura',
            'Regras de representação:': 'regras_representacao',
            'Origem das regras de representação:': 'origem_regras_representacao',
            'Data de validade das regras:': 'data_validade_regras',
            'Origem da data de validade:': 'origem_data_validade'
        }
    
    def extract_representatives_names(self, lines: List[str]) -> str:
        """
        Extrai apenas os nomes dos representantes da resposta Gemini.
        
        Args:
            lines: Linhas do texto Gemini
            
        Returns:
            Nomes separados por newlines
        """
        representatives_detailed = self.extract_detailed_representatives(lines)
        if not representatives_detailed:
            return ""
        
        names = []
        for rep in representatives_detailed:
            if rep.get('nome') and rep['nome'] != self.DATA_NOT_AVAILABLE:
                names.append(rep['nome'])
        
        return '\n'.join(names)
    
    def extract_detailed_representatives(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Extrai dados detalhados dos representantes da resposta Gemini.
        
        Args:
            lines: Linhas do texto Gemini
            
        Returns:
            Lista de dicionários com dados dos representantes
        """
        start_index = self._find_representatives_section_start(lines)
        if start_index is None:
            return []
        
        return self._parse_representatives_data(lines, start_index)
    
    def validate_and_filter(self, representatives: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Valida dados de representantes: preenche campos vazios, remove duplicatas,
        e FILTRA procuradores.
        
        Args:
            representatives: Lista de representantes
            
        Returns:
            Lista validada e filtrada
        """
        if not representatives:
            return []
        
        # Preencher campos vazios
        for rep in representatives:
            for field in ['nome', 'cpf', 'cargo', 'endereco_residencia', 
                         'tipo_assinatura', 'origem_assinatura', 'regras_representacao',
                         'origem_regras_representacao', 'data_validade_regras', 
                         'origem_data_validade']:
                if field not in rep or not rep[field]:
                    rep[field] = self.DATA_NOT_AVAILABLE
        
        # FILTRAR PROCURADORES
        filtered_representatives = []
        for rep in representatives:
            cargo_upper = rep.get('cargo', '').upper()
            
            # Remove se cargo contém palavras de procurador
            is_procurador = any(keyword in cargo_upper for keyword in self.PROCURADOR_KEYWORDS)
            
            if not is_procurador:
                filtered_representatives.append(rep)
        
        # Remover duplicatas baseado no nome
        seen_names = set()
        unique_representatives = []
        
        for rep in filtered_representatives:
            nome = rep.get('nome', '')
            if nome and nome != self.DATA_NOT_AVAILABLE:
                nome_normalized = nome.strip().upper()
                if nome_normalized not in seen_names:
                    seen_names.add(nome_normalized)
                    unique_representatives.append(rep)
        
        return unique_representatives
    
    def calculate_count(self, representatives: List[Dict[str, str]]) -> int:
        """
        Calcula o número de representantes baseado em nomes válidos.
        
        Args:
            representatives: Lista de representantes
            
        Returns:
            Contagem de representantes válidos
        """
        if not representatives:
            return 0
        
        valid_count = 0
        for rep in representatives:
            nome = rep.get('nome', '')
            if nome and nome != self.DATA_NOT_AVAILABLE:
                valid_count += 1
        
        return valid_count
    
    def _find_representatives_section_start(self, lines: List[str]) -> Optional[int]:
        """Encontra o início da seção de representantes."""
        for i, line in enumerate(lines):
            line_clean = line.strip().replace('**', '').lower()
            if line_clean.startswith('representantes legais'):
                return i + 1
        return None
    
    def _parse_representatives_data(self, lines: List[str], start_index: int) -> List[Dict[str, str]]:
        """Faz parse dos dados de representantes a partir do índice dado."""
        representatives = []
        current_rep = None
        
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            
            if not line:
                continue
            
            # Nova representante começando
            if line.startswith('Representante '):
                if current_rep:
                    representatives.append(current_rep)
                current_rep = {}
                continue
            
            # Atualizar campos do representante atual
            if current_rep is not None:
                self._update_representative_field(line, current_rep)
        
        # Adicionar último representante
        if current_rep:
            representatives.append(current_rep)
        
        # Validar e filtrar
        representatives = self.validate_and_filter(representatives)
        
        return representatives
    
    def _update_representative_field(self, line: str, current_rep: Dict[str, str]) -> None:
        """Atualiza um campo específico no dicionário do representante."""
        for prefix, field_key in self.field_mappings.items():
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                current_rep[field_key] = value
                break
