


"""
Processor para múltiplos documentos.
Responsável por analisar, priorizar e detectar conflitos entre documentos.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class MultiDocumentProcessor:
    """Processa múltiplos documentos e analisa prioridades."""
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    # Tipos de documentos
    ACCESSORY_TYPES = ["PROCURACAO", "ADITAMENTO", "CERTIDAO", "FICHA_CADASTRAL"]
    CORPORATE_TYPES = ["ESTATUTO_SOCIAL", "ATA_DE_ASSEMBLEIA", "ATA_DE_ELEICAO", "CONTRATO_SOCIAL"]
    
    def __init__(self):
        """Inicializa o processor de múltiplos documentos."""
        pass
    
    def create_marked_document_text(self, doc_index: int, total_docs: int, 
                                    file_name: str, pdf_text: str, 
                                    metadata: Dict[str, Any]) -> str:
        """
        Cria texto marcado com metadados para múltiplos documentos.
        INCLUI informações de prioridade temporal (usado para metadados do JSON).
        
        Args:
            doc_index: Índice do documento
            total_docs: Total de documentos
            file_name: Nome do arquivo
            pdf_text: Texto do PDF
            metadata: Metadados do documento
            
        Returns:
            Texto marcado com cabeçalho
        """
        doc_type = metadata['document_type']
        is_accessory = self._is_accessory_document(doc_type)
        is_corporate = self._is_corporate_document(doc_type)
        
        complementation_note = ""
        if is_accessory:
            complementation_note = " - DOCUMENTO ACESSÓRIO: Use para complementar dados, não como fonte principal"
        elif is_corporate:
            complementation_note = " - DOCUMENTO SOCIETÁRIO: Fonte principal de dados estruturais"
        
        header = f"""=== DOCUMENTO {doc_index}/{total_docs}: {file_name} ===
METADADOS DO DOCUMENTO:
- Tipo: {doc_type}
- Data de Registro: {metadata['registration_date'] or 'Não identificada'}
- Número do Documento: {metadata['document_number'] or 'Não identificado'}
- Score de Prioridade: {metadata['priority_score']} (maior = mais recente)
- Classificação: {'ACESSÓRIO' if is_accessory else 'CORPORATIVO' if is_corporate else 'GENÉRICO'}{complementation_note}

CONTEÚDO:
{pdf_text}

=== FIM DO DOCUMENTO {doc_index} ===
"""
        return header
    
    def create_marked_document_text_no_priority(self, doc_index: int, total_docs: int, 
                                               file_name: str, pdf_text: str, 
                                               metadata: Dict[str, Any]) -> str:
        """
        Cria texto marcado SEM informações de prioridade temporal.
        Usado para enviar ao LLM - todos os documentos têm o mesmo peso.
        
        Args:
            doc_index: Índice do documento
            total_docs: Total de documentos
            file_name: Nome do arquivo
            pdf_text: Texto do PDF
            metadata: Metadados do documento
            
        Returns:
            Texto marcado sem prioridade
        """
        doc_type = metadata['document_type']
        is_accessory = self._is_accessory_document(doc_type)
        is_corporate = self._is_corporate_document(doc_type)
        
        complementation_note = ""
        if is_accessory:
            complementation_note = " - DOCUMENTO ACESSÓRIO: Use para complementar dados"
        elif is_corporate:
            complementation_note = " - DOCUMENTO SOCIETÁRIO: Fonte principal de dados"
        
        header = f"""=== DOCUMENTO {doc_index}/{total_docs}: {file_name} ===
METADADOS DO DOCUMENTO:
- Tipo: {doc_type}
- Número do Documento: {metadata['document_number'] or 'Não identificado'}
- Classificação: {'ACESSÓRIO' if is_accessory else 'CORPORATIVO' if is_corporate else 'GENÉRICO'}{complementation_note}

CONTEÚDO:
{pdf_text}

=== FIM DO DOCUMENTO {doc_index} ===
"""
        return header
    
    def analyze_document_priority(self, processed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa a prioridade dos documentos.
        IMPORTANTE: Esta análise é APENAS INFORMATIVA no JSON de resposta.
        
        Args:
            processed_files: Lista de arquivos processados com metadados
            
        Returns:
            Dicionário com análise de prioridade
        """
        if not processed_files:
            return {}
        
        # Ordenar por prioridade (apenas informativo)
        sorted_by_priority = sorted(processed_files, key=lambda x: x['priority_score'], reverse=True)
        highest_priority = sorted_by_priority[0]
        highest_priority_type = highest_priority['document_type']
        
        # Identificar documento societário principal
        corporate_doc = None
        for doc in processed_files:
            if self._is_corporate_document(doc['document_type']):
                corporate_doc = doc
                break
        
        # Determinar estratégia (informativa)
        extraction_strategy = self._determine_extraction_strategy(
            highest_priority_type, corporate_doc is not None
        )
        
        return {
            "most_recent_document": {
                "file_name": highest_priority['file_name'],
                "document_type": highest_priority['document_type'],
                "signature_date": highest_priority['signature_date'],
                "priority_score": highest_priority['priority_score'],
                "is_accessory": self._is_accessory_document(highest_priority_type),
                "is_corporate": self._is_corporate_document(highest_priority_type)
            },
            "corporate_document_reference": {
                "file_name": corporate_doc['file_name'],
                "document_type": corporate_doc['document_type'],
                "signature_date": corporate_doc['signature_date']
            } if corporate_doc else None,
            "extraction_strategy": extraction_strategy,
            "complementation_needed": self._is_accessory_document(highest_priority_type),
            "documents_by_priority": [
                {
                    "file_name": doc['file_name'],
                    "document_type": doc['document_type'],
                    "signature_date": doc['signature_date'],
                    "priority_score": doc['priority_score'],
                    "is_accessory": self._is_accessory_document(doc['document_type']),
                    "is_corporate": self._is_corporate_document(doc['document_type'])
                } for doc in sorted_by_priority
            ],
            "priority_rule": "INFORMAÇÃO APENAS: Documentos listados por data. Na extração, TODOS analisados igualmente."
        }
    
    def generate_changes_summary(self, processed_files: List[Dict[str, Any]], 
                                gemini_response: str) -> str:
        """
        Gera resumo das principais mudanças entre documentos.
        PROCURAÇÕES SÃO IGNORADAS.
        
        Args:
            processed_files: Lista de arquivos processados
            gemini_response: Resposta do Gemini
            
        Returns:
            String com resumo de mudanças
        """
        if len(processed_files) < 2:
            return "Documento único - sem mudanças a comparar"
        
        doc_types = [doc['document_type'] for doc in processed_files]
        changes = []
        
        # Identificar tipos de documentos
        accessory_docs = [doc for doc in processed_files if self._is_accessory_document(doc['document_type'])]
        corporate_docs = [doc for doc in processed_files if self._is_corporate_document(doc['document_type'])]
        procuracao_docs = [doc for doc in processed_files if doc['document_type'] == 'PROCURACAO']
        
        if procuracao_docs:
            changes.append("⚠️ Procurações detectadas e IGNORADAS para fins de representantes")
        
        if accessory_docs and corporate_docs:
            changes.append("📋 Documentos acessórios complementando dados de documentos societários")
        
        # Analisar mudanças por tipo
        if "ATA_DE_ASSEMBLEIA" in doc_types:
            changes.append("📊 Ata de Assembleia detectada - possíveis mudanças em quotas ou representantes")
        
        if "ATA_DE_ELEICAO" in doc_types:
            changes.append("👔 Ata de Eleição detectada - mudança na diretoria/administração")
        
        if "CONTRATO_SOCIAL" in doc_types:
            changes.append("📝 Contrato Social/Alteração - mudanças estruturais na sociedade")
        
        # Analisar datas corporativas
        corporate_dates = [doc['signature_date'] for doc in corporate_docs if doc['signature_date']]
        if len(set(corporate_dates)) > 1:
            changes.append("📅 Múltiplas datas em documentos corporativos - evolução temporal")
        
        # Analisar texto Gemini
        if gemini_response:
            gemini_upper = gemini_response.upper()
            if "ELEIÇÃO" in gemini_upper or "ELEITO" in gemini_upper:
                changes.append("🗳️ Eleição/nomeação de novos representantes identificada")
            if "ALTERAÇÃO" in gemini_upper:
                changes.append("🔄 Alterações contratuais identificadas")
        
        if not changes:
            return "Múltiplos documentos sem mudanças significativas identificadas"
        
        return "\n".join(changes)
    
    def detect_potential_conflicts(self, processed_files: List[Dict[str, Any]]) -> List[str]:
        """
        Detecta potenciais conflitos entre documentos.
        
        Args:
            processed_files: Lista de arquivos processados
            
        Returns:
            Lista de avisos sobre conflitos
        """
        warnings = []
        
        if len(processed_files) < 2:
            return warnings
        
        # Verificar documentos do mesmo tipo com datas diferentes
        type_dates = {}
        for doc in processed_files:
            doc_type = doc['document_type']
            date = doc['signature_date']
            if doc_type not in type_dates:
                type_dates[doc_type] = []
            if date:
                type_dates[doc_type].append(date)
        
        for doc_type, dates in type_dates.items():
            if len(set(dates)) > 1:
                warnings.append(f"⚠️ Múltiplas datas para {doc_type}: {', '.join(sorted(set(dates)))}")
        
        # Verificar diferença temporal grande
        dates = [doc['priority_score'] for doc in processed_files if doc['priority_score'] > 0]
        if len(dates) > 1:
            date_diff = max(dates) - min(dates)
            if date_diff > 31536000:  # > 1 ano em segundos
                warnings.append("⚠️ Documentos com diferença temporal > 1 ano - verificar validade")
        
        return warnings
    
    def _is_accessory_document(self, doc_type: str) -> bool:
        """Verifica se é documento acessório."""
        return doc_type in self.ACCESSORY_TYPES
    
    def _is_corporate_document(self, doc_type: str) -> bool:
        """Verifica se é documento societário."""
        return doc_type in self.CORPORATE_TYPES
    
    def _determine_extraction_strategy(self, highest_priority_type: str, 
                                      has_corporate: bool) -> str:
        """Determina estratégia de extração (informativa)."""
        if self._is_accessory_document(highest_priority_type):
            if has_corporate:
                return "Documento mais recente é acessório - complementar dados do documento societário"
            return "Documento acessório sem documento societário - extrair o que for possível"
        elif self._is_corporate_document(highest_priority_type):
            return "Documento societário mais recente - usar como fonte principal"
        return "Documento genérico - aplicar extração padrão"
