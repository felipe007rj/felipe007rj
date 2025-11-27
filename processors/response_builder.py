"""
ResponseBuilder - Construtor de resposta JSON final.
Responsável por montar a resposta completa com validações e enriquecimento.
"""

import json
from typing import Dict, Any, List


class ResponseBuilder:
    """Constrói a resposta JSON final do processamento."""
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    def __init__(self):
        """Inicializa o construtor de resposta."""
        pass
    
    def build_response(self, request_id: str, data_out: Dict[str, Any], 
                      document_info: Dict[str, Any] = None,
                      priority_analysis: Dict[str, Any] = None,
                      changes_summary: str = None,
                      conflicts: List[str] = None) -> str:
        """
        Constrói a resposta JSON final.
        
        Args:
            request_id: ID da requisição
            data_out: Dados extraídos
            document_info: Informações sobre documentos processados
            priority_analysis: Análise de prioridade de documentos
            changes_summary: Resumo de mudanças
            conflicts: Lista de conflitos detectados
            
        Returns:
            String JSON da resposta
        """
        response_data = {
            "id": request_id,
            "data": data_out
        }
        
        # Adicionar metadados de documentos no formato legado
        if document_info:
            metadata = {
                "total_documents": document_info.get('total_documents', 0),
                "processed_documents": document_info.get(
                    'processed_documents', document_info.get('total_documents', 0)
                ),
                "is_multiple_documents": document_info.get('is_multiple_documents', False),
                "processing_type": "LOTE" if document_info.get('is_multiple_documents') else "ÚNICO",
                "exceeded_limit": document_info.get('exceeded_limit', False)
            }

            ignored_documents = document_info.get('ignored_documents', [])
            if document_info.get('exceeded_limit') and ignored_documents:
                metadata["warning"] = (
                    f"Limite de 3 documentos excedido. Total recebido: {document_info.get('total_documents', 0)}. "
                    f"Processados: {document_info.get('processed_documents', 0)}. "
                    f"Ignorados: {len(ignored_documents)}"
                )
                metadata["ignored_documents"] = [
                    doc.split('/')[-1] if '/' in doc else doc for doc in ignored_documents
                ]

            # Análises adicionais mantidas para compatibilidade estendida
            if priority_analysis:
                metadata["priority_analysis"] = priority_analysis
            if changes_summary:
                metadata["changes_summary"] = changes_summary
            if conflicts:
                metadata["conflict_warnings"] = conflicts

            response_data["document_metadata"] = metadata
        
        json_response = json.dumps(response_data, ensure_ascii=False)
        
        return json_response
    
    def validate_required_fields(self, data_out: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida campos obrigatórios e aplica valores padrão se necessário.
        
        Args:
            data_out: Dados a validar
            
        Returns:
            Dicionário validado
        """
        # Campos que não podem estar vazios
        required_fields = [
            "junta_comercial",
            "cnpj", 
            "razao_social",
            "natureza_juridica",
            "endereco",
            "cotas_societarias",
            "representantes_legais",
            "referencia_da_origem",
            "data_assinatura",
            "poderes_e_representacao"
        ]
        
        for field in required_fields:
            if field not in data_out or not data_out[field] or data_out[field].strip() == "":
                data_out[field] = self.DATA_NOT_AVAILABLE
        
        # Validar lista de representantes detalhados
        if "representantes_detalhados" not in data_out:
            data_out["representantes_detalhados"] = []
        
        # Validar quantidade de representantes
        if "quantidade_representantes" not in data_out:
            data_out["quantidade_representantes"] = len(data_out.get("representantes_detalhados", []))
        
        return data_out
    
    def normalize_output(self, data_out: Dict[str, Any], cnpj_extractor, 
                        date_extractor) -> Dict[str, Any]:
        """
        Normaliza campos da resposta (CNPJ, datas, etc).
        
        Args:
            data_out: Dados a normalizar
            cnpj_extractor: Instância de CNPJExtractor
            date_extractor: Instância de DateExtractor
            
        Returns:
            Dicionário normalizado
        """
        # Normalizar CNPJ
        if "cnpj" in data_out:
            data_out["cnpj"] = cnpj_extractor.normalize(data_out["cnpj"])
        
        # Normalizar data de assinatura
        if "data_assinatura" in data_out:
            normalized_date = date_extractor.normalize_any(data_out["data_assinatura"])
            if normalized_date:
                data_out["data_assinatura"] = normalized_date
        
        # Normalizar datas de validade em representantes
        if "representantes_detalhados" in data_out:
            for rep in data_out["representantes_detalhados"]:
                if "data_validade_regras" in rep:
                    normalized = date_extractor.normalize_any(rep["data_validade_regras"])
                    if normalized:
                        rep["data_validade_regras"] = normalized
        
        return data_out
    
    def clean_output(self, data_out: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa dados da resposta (remove excesso de whitespace, etc).
        
        Args:
            data_out: Dados a limpar
            
        Returns:
            Dicionário limpo
        """
        # Limpar strings (remover excesso de espaços, newlines desnecessários)
        string_fields = [
            "junta_comercial", "cnpj", "razao_social", "natureza_juridica",
            "endereco", "cotas_societarias", "representantes_legais",
            "referencia_da_origem", "data_assinatura", "poderes_e_representacao"
        ]
        
        for field in string_fields:
            if field in data_out and isinstance(data_out[field], str):
                # Remover múltiplos espaços
                data_out[field] = ' '.join(data_out[field].split())
        
        return data_out
