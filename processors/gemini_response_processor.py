"""
Processor para respostas do Gemini.
Responsável por processar, validar e extrair JSON das respostas da API Gemini.
"""

import json
import re
from typing import Dict, Any, List, Optional


class GeminiResponseProcessor:
    """Processa respostas da API Gemini."""
    
    DATA_NOT_AVAILABLE = "Dado não disponível no documento"
    
    # Campos padrão da resposta
    DEFAULT_RESPONSE_FIELDS = {
        "junta_comercial": "",
        "cnpj": "",
        "razao_social": "",
        "natureza_juridica": "",
        "endereco": "",
        "cotas_societarias": "",
        "representantes_legais": "",
        "representantes_detalhados": [],
        "quantidade_representantes": 0,
        "referencia_da_origem": "",
        "data_assinatura": "",
        "poderes_e_representacao": ""
    }
    
    def __init__(self):
        """Inicializa o processor de resposta Gemini."""
        pass
    
    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extrai JSON da resposta do Gemini.
        Remove markdown code blocks se necessário.
        
        Args:
            response_text: Texto de resposta do Gemini
            
        Returns:
            Dicionário com dados extraídos
        """
        try:
            # Extrair primeiro JSON válido
            json_str = self._extract_first_json(response_text)
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ Erro ao extrair JSON: {e}")
            return self.DEFAULT_RESPONSE_FIELDS.copy()
    
    def parse_text_response(self, response_text: str, field_extractor) -> Dict[str, Any]:
        """
        Faz parse de resposta em texto (não-JSON) do Gemini.
        Extrai campos usando FieldExtractor.
        
        Args:
            response_text: Texto de resposta do Gemini
            field_extractor: Instância de FieldExtractor
            
        Returns:
            Dicionário com dados extraídos
        """
        data_out = self.DEFAULT_RESPONSE_FIELDS.copy()
        lines = response_text.split('\n')
        
        # Extrair campos de linha única
        simple_fields = ["cnpj", "razao_social", "junta_comercial", "endereco", "natureza_juridica"]
        for field in simple_fields:
            field_target = self._get_field_target(field)
            data_out[field] = field_extractor.extract_line_field(field_target, lines)
        
        # Extrair campos de bloco
        data_out["cotas_societarias"] = field_extractor.extract_block_field("Cotas societárias:", lines)
        
        # Limpar newlines de cotas_societarias
        if data_out["cotas_societarias"]:
            data_out["cotas_societarias"] = data_out["cotas_societarias"].replace('\n', ', ')
        
        # Extrair data de assinatura
        data_assinatura = field_extractor.extract_line_field("Data de assinatura:", lines)
        if not data_assinatura:
            data_assinatura = field_extractor.extract_block_field("Data de assinatura:", lines)
        
        if data_assinatura:
            data_assinatura = data_assinatura.replace('\n', ', ')
        
        data_out["data_assinatura"] = data_assinatura
        
        # Extrair referência da origem
        data_out["referencia_da_origem"] = field_extractor.extract_line_field("Referência da origem:", lines)
        if not data_out["referencia_da_origem"]:
            data_out["referencia_da_origem"] = self.DATA_NOT_AVAILABLE
        
        return data_out
    
    def apply_fallbacks(self, data_out: Dict[str, Any], ocr_text: str, 
                       cnpj_extractor, company_extractor) -> Dict[str, Any]:
        """
        Aplica fallbacks de extração de OCR quando Gemini não extraiu.
        
        Args:
            data_out: Dados extraídos do Gemini
            ocr_text: Texto OCR completo
            cnpj_extractor: Instância de CNPJExtractor
            company_extractor: Instância de CompanyExtractor
            
        Returns:
            Dicionário com dados enriquecidos
        """
        # Fallback Junta Comercial
        if not data_out.get("junta_comercial") or data_out["junta_comercial"] == "":
            junta = company_extractor.extract_junta_comercial(ocr_text)
            if junta:
                data_out["junta_comercial"] = junta
        
        # Fallback CNPJ
        if not data_out.get("cnpj") or data_out["cnpj"] == "":
            cnpj = cnpj_extractor.extract_from_ocr(ocr_text)
            if cnpj:
                data_out["cnpj"] = cnpj
        
        # Fallback Razão Social
        if not data_out.get("razao_social") or data_out["razao_social"] == "":
            razao = company_extractor.extract_razao_social(ocr_text)
            if razao:
                data_out["razao_social"] = razao
        
        # Fallback Natureza Jurídica
        if (not data_out.get("natureza_juridica") or 
            data_out["natureza_juridica"] == "" or
            data_out["natureza_juridica"] == self.DATA_NOT_AVAILABLE):
            natureza = company_extractor.extract_natureza_juridica(data_out.get("razao_social", ""))
            if natureza:
                data_out["natureza_juridica"] = natureza
        
        return data_out
    
    def validate_final_fields(self, data_out: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida campos finais e aplica valores padrão se necessário.
        
        Args:
            data_out: Dados a validar
            
        Returns:
            Dicionário validado
        """
        # Validar data_assinatura não vazia
        if not data_out.get("data_assinatura") or data_out["data_assinatura"].strip() == "":
            data_out["data_assinatura"] = self.DATA_NOT_AVAILABLE
        
        # Validar referencia_da_origem não vazia
        if (not data_out.get("referencia_da_origem") or 
            data_out["referencia_da_origem"] == "" or
            data_out["referencia_da_origem"] == self.DATA_NOT_AVAILABLE):
            data_out["referencia_da_origem"] = self.DATA_NOT_AVAILABLE
        
        # Validar cotas_societarias não vazia
        if not data_out.get("cotas_societarias") or data_out["cotas_societarias"] == "":
            data_out["cotas_societarias"] = self.DATA_NOT_AVAILABLE
        
        return data_out
    
    def consolidate_poderes_representacao(self, representantes_detalhados: List[Dict[str, str]]) -> str:
        """
        Consolida poderes e representação de todos os representantes.
        
        Args:
            representantes_detalhados: Lista de representantes com detalhes
            
        Returns:
            String consolidada com poderes
        """
        if not representantes_detalhados:
            return self.DATA_NOT_AVAILABLE
        
        poderes_list = []
        for rep in representantes_detalhados:
            regras = rep.get('regras_representacao', '')
            if regras and regras != self.DATA_NOT_AVAILABLE:
                # Personalizar com nome do representante
                nome = rep.get('nome', 'Representante')
                poderes_personalizados = f"{nome}: {regras}"
                poderes_list.append(poderes_personalizados)
        
        if not poderes_list:
            return self.DATA_NOT_AVAILABLE
        
        return "; ".join(poderes_list)
    
    def _extract_first_json(self, blob: str) -> str:
        """
        Extrai o primeiro objeto JSON bem formado de uma string.
        Remove markdown code blocks se necessário.
        
        Args:
            blob: String contendo JSON
            
        Returns:
            String JSON extraída
        """
        blob = blob.strip()
        
        # Remover blocos markdown se presentes
        if blob.startswith("```json") and blob.endswith("```"):
            blob = blob[7:-3].strip()
        elif blob.startswith("```") and blob.endswith("```"):
            blob = blob[3:-3].strip()
        
        # Se já está bem formado
        if blob.startswith("{") and blob.endswith("}"):
            try:
                json.loads(blob)
                return blob
            except json.JSONDecodeError:
                pass
        
        # Buscar primeiro { e último }
        start = blob.find("{")
        end = blob.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            candidate = blob[start:end+1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        
        return blob
    
    def _get_field_target(self, field: str) -> str:
        """Mapeia nomes de campos para targets de extração."""
        field_targets = {
            "junta_comercial": "Junta Comercial:",
            "cnpj": "CNPJ:",
            "razao_social": "Razão Social:",
            "natureza_juridica": "Natureza Jurídica:",
            "endereco": "Endereço:",
            "cotas_societarias": "Cotas societárias:",
            "representantes_legais": "Representantes legais:",
            "referencia_da_origem": "Referência da origem:",
            "data_assinatura": "Data de assinatura:"
        }
        return field_targets.get(field, f"{field.replace('_', ' ').title()}:")
