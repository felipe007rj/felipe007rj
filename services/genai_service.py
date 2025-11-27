"""Serviço de integração com Google Gemini API."""

import json
import re
from datetime import datetime


class GenAIService:
    """Gerencia operações com Google Gemini API."""
    
    def __init__(self, genai_client, model_name: str, base_prompt: str):
        """Inicializa o serviço GenAI."""
        self.client = genai_client
        self.model_name = model_name
        self.base_prompt = base_prompt or ""
        self.last_metadata = None
    
    def build_prompt(self, ocr_text: str) -> str:
        """Monta o prompt final combinando prompt base e texto OCR."""
        if not self.base_prompt:
            return ocr_text
        if "{OCR_TEXT_AQUI}" in self.base_prompt:
            return self.base_prompt.replace("{OCR_TEXT_AQUI}", ocr_text)
        return f"{self.base_prompt}\n\n{ocr_text}"
    
    def generate_content(self, prompt_text: str) -> tuple:
        """
        Gera conteúdo usando o Gemini API.
        Returns uma tupla (texto, metadados).
        """
        try:
            genai_start_time = datetime.now().isoformat()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_text,
                config={
                    "max_output_tokens": 60192,
                    "temperature": 0,
                    "top_p": 0.8,
                }
            )
            
            text = response.text or ""
            # Fallback: extrair primeiro JSON válido se houver
            text = self.extract_first_json(text)
            
            genai_metadata = {
                "model": response.model_version,
                "input_token_count": response.usage_metadata.prompt_token_count,
                "output_token_count": response.usage_metadata.candidates_token_count,
                "genai_start_time": genai_start_time,
                "genai_end_time": datetime.now().isoformat(),
                "response": text
            }
            
            self.last_metadata = genai_metadata
            return text, genai_metadata
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "", None
    
    @staticmethod
    def extract_first_json(blob: str) -> str:
        """
        Extrai o primeiro objeto JSON bem-formado de uma string.
        Remove blocos de código markdown se necessário.
        
        Args:
            blob: String contendo possível JSON
            
        Returns:
            JSON extraído ou string original
        """
        blob = blob.strip()
        
        # Remove markdown json blocks se presentes
        if blob.startswith("```json") and blob.endswith("```"):
            blob = blob[7:-3].strip()
        elif blob.startswith("```") and blob.endswith("```"):
            blob = blob[3:-3].strip()
        
        if blob.startswith("{") and blob.endswith("}"):
            try:
                json.loads(blob)  # Valida se é JSON válido
                return blob
            except Exception:
                pass
        
        # Busca pela primeira abertura e fechamento plausíveis
        start = blob.find("{")
        end = blob.rfind("}")
        
        if start != -1 and end != -1 and end > start:
            candidate = blob[start:end+1]
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                pass
        
        return blob  # Retorna como está (pode já ser JSON limpo)
