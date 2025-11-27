"""
Gerenciamento de secrets do AWS Secrets Manager.
"""

import json
import os
from typing import Any, Dict


class SecretsManager:
    """Gerencia secrets do AWS Secrets Manager."""
    
    def __init__(self, secrets_manager_client):
        """
        Inicializa o gerenciador de secrets.
        
        Args:
            secrets_manager_client: Cliente boto3 do Secrets Manager
        """
        self.client = secrets_manager_client
        self._secrets_cache: Dict[str, Any] = {}
    
    def get_secrets(self, secret_name: str) -> Dict[str, Any]:
        """
        Recupera secrets do AWS Secrets Manager.
        
        Args:
            secret_name: Nome do secret no AWS
            
        Returns:
            Dicionário com os secrets
        """
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        secret_value_response = self.client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_value_response['SecretString'])
        
        self._secrets_cache[secret_name] = secret
        return secret
    
    def get_gemini_api_key(self, secret_name: str, key_name: str) -> str:
        """
        Recupera a API key do Gemini.
        
        Args:
            secret_name: Nome do secret
            key_name: Nome da chave dentro do secret
            
        Returns:
            API key do Gemini
        """
        secrets = self.get_secrets(secret_name)
        return secrets[key_name]
    
    def get_gcloud_credentials(self, secret_name: str, key_name: str) -> str:
        """
        Recupera as credenciais do Google Cloud.
        
        Args:
            secret_name: Nome do secret
            key_name: Nome da chave dentro do secret
            
        Returns:
            Credenciais do Google Cloud como string JSON
        """
        secrets = self.get_secrets(secret_name)
        return secrets[key_name]
    
    def write_gcloud_credentials_file(self, secret_name: str, key_name: str, 
                                     output_path: str = '/tmp/gcloud_creds.json') -> None:
        """
        Escreve as credenciais do Google Cloud em um arquivo.
        
        Args:
            secret_name: Nome do secret
            key_name: Nome da chave dentro do secret
            output_path: Caminho do arquivo de saída
        """
        credentials = self.get_gcloud_credentials(secret_name, key_name)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(credentials)
