"""
Extractor genérico para campos de texto.
Responsável por extrair campos de linha única e blocos de texto.
"""

from typing import List


class FieldExtractor:
    """Extrai campos genéricos de texto estruturado."""
    
    def __init__(self):
        """Inicializa o extractor de campos."""
        pass
    
    def extract_line_field(self, target: str, lines: List[str]) -> str:
        """
        Extrai um campo de linha única da resposta Gemini (com ou sem negrito).
        
        Args:
            target: Nome do campo a buscar (ex: "CNPJ:")
            lines: Linhas do texto
            
        Returns:
            Valor do campo ou string vazia se não encontrado
        """
        target_lower = target.lower()
        
        for line in lines:
            normalized_line = self._normalize_line(line)
            if normalized_line.lower().startswith(target_lower):
                return normalized_line[len(target):].strip()
        
        return ''
    
    def extract_block_field(self, target: str, lines: List[str]) -> str:
        """
        Extrai um campo de múltiplas linhas (bloco) da resposta Gemini.
        
        Args:
            target: Nome do campo a buscar (ex: "Cotas societárias:")
            lines: Linhas do texto
            
        Returns:
            Valor do campo ou string vazia se não encontrado
        """
        target_lower = target.lower()
        
        for i, line in enumerate(lines):
            normalized_line = self._normalize_line(line)
            if normalized_line.lower().startswith(target_lower):
                return self._collect_block_value(lines, i, target)
        
        return ''

    def _normalize_line(self, line: str) -> str:
        """Remove marcações markdown e espaços extras de uma linha."""
        return line.replace('**', '').strip()

    def _collect_block_value(self, lines: List[str], start_index: int, target: str) -> str:
        """Coleta o conteúdo de um campo de bloco a partir do índice inicial."""
        block_lines: List[str] = []
        current_line = self._normalize_line(lines[start_index])
        inline_value = current_line[len(target):].strip()
        if inline_value:
            block_lines.append(inline_value)
        
        for j in range(start_index + 1, len(lines)):
            next_line = lines[j].strip()
            if not next_line:
                continue
            
            next_line_clean = self._normalize_line(next_line)
            if next_line_clean.endswith(':') and j > start_index + 1:
                break
            
            block_lines.append(next_line_clean)
        
        return '\n'.join(block_lines).strip()
    
    def _is_field_start(self, line: str) -> bool:
        """
        Verifica se uma linha marca o início de um novo campo.
        Campos geralmente terminam com ':'.
        """
        line_clean = line.replace('**', '').strip()
        
        # Lista de campos conhecidos do Gemini
        known_fields = [
            'junta comercial:', 'cnpj:', 'razão social:', 'natureza jurídica:',
            'endereço:', 'cotas societárias:', 'representantes legais:',
            'referência da origem:', 'data de assinatura:', 
            'poderes e representação:', 'regras de representação:',
            'representante '  # Início de bloco de representante
        ]
        
        line_lower = line_clean.lower()
        
        # Verificar se começa com algum campo conhecido
        return any(line_lower.startswith(field) for field in known_fields)
