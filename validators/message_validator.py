"""Validador de mensagens SQS."""

import json
from typing import Any, Dict

from config.settings import CNPJ_LENGTH


class MessageValidator:
    """Valida mensagens recebidas do SQS."""
    
    @staticmethod
    def validate_sqs_message(msg: Dict[str, Any]) -> bool:
        """
        Valida a estrutura e campos obrigatórios da mensagem SQS.
        
        Args:
            msg: Mensagem do SQS
            
        Returns:
            True se válida, False caso contrário
            
        Campos obrigatórios:
            - id (str)
            - pdf_uris (list de str com URIs s3://)
            - cnpj (str com 14 dígitos numéricos)
        """
        if 'Body' not in msg:
            print("SQS message missing 'Body' field.")
            return False
        
        try:
            body = json.loads(msg['Body'])
        except Exception as e:
            print(f"SQS message body is not valid JSON: {e}")
            return False
        
        if not isinstance(body, dict):
            print("SQS message body is not a JSON object.")
            return False
        
        # Validar campo 'id'
        if 'id' not in body or not isinstance(body['id'], str) or not body['id']:
            print("SQS message body missing or invalid 'id' field.")
            return False
        
        # Validar campo 'pdf_uris'
        if 'pdf_uris' not in body or not isinstance(body['pdf_uris'], list) or not body['pdf_uris']:
            print("SQS message body missing or invalid 'pdf_uris' field.")
            return False
        
        for uri in body['pdf_uris']:
            if not isinstance(uri, str) or not uri.startswith('s3://'):
                print(f"Invalid PDF URI in 'pdf_uris': {uri}")
                return False
        
        # Validar campo 'cnpj'
        cnpj = body.get('cnpj')
        if not isinstance(cnpj, str) or len(cnpj) != CNPJ_LENGTH or not cnpj.isdigit():
            print(f"SQS message body missing or invalid 'cnpj' field: {cnpj}")
            return False
        
        return True
