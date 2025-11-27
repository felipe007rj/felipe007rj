"""Serviço de comunicação com Amazon S3."""

import botocore
import json
from datetime import datetime
from typing import Optional


class S3Service:
    """Gerencia operações com Amazon S3."""
    
    def __init__(self, s3_client, bucket_name: str):
        """
        Inicializa o serviço S3.
        
        Args:
            s3_client: Cliente boto3 do S3
            bucket_name: Nome do bucket
        """
        self.client = s3_client
        self.bucket_name = bucket_name
    
    def download_object(self, uri: str) -> Optional[bytes]:
        """
        Faz download de um objeto do S3 usando URI s3://bucket/key.
        
        Args:
            uri: URI do objeto no formato s3://bucket/key
            
        Returns:
            Conteúdo do objeto em bytes ou None em caso de erro
        """
        try:
            if not uri.startswith("s3://"):
                print(f"Invalid S3 URI: {uri}")
                return None
            
            parts = uri.replace("s3://", "").split("/", 1)
            if len(parts) != 2:
                print(f"Malformed S3 URI: {uri}")
                return None
            
            bucket, key = parts
            obj = self.client.get_object(Bucket=bucket, Key=key)
            print(f"Downloaded object from S3: s3://{bucket}/{key}")
            return obj['Body'].read()
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error downloading from S3: {e}")
            return None
        except Exception as e:
            print(f"General error downloading from S3: {e}")
            return None
    
    def get_prompt(self, uri: str) -> str:
        """
        Baixa e decodifica um prompt do S3 ou arquivo local.
        
        Args:
            uri: URI do prompt (s3:// ou caminho local)
            
        Returns:
            Conteúdo do prompt como string UTF-8
        """
        try:
            # Suporte para arquivos locais
            if uri.startswith('/') or uri.startswith('./'):
                with open(uri, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # S3
                obj = self.download_object(uri)
                if obj is None:
                    print(f"Base prompt not found at {uri}")
                    return ""
                return obj.decode('utf-8')
        except Exception as e:
            print(f"Error getting base prompt: {e}")
            return ""
    
    def upload_receipt(self, request_id: str, receipt_data: dict) -> None:
        """
        Faz upload de um receipt para o S3.
        
        Args:
            request_id: ID da requisição
            receipt_data: Dados do receipt
        """
        try:
            receipt_json = json.dumps(receipt_data, ensure_ascii=False, indent=2)
            receipt_filename = f"{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            s3_key = f"receipts/{receipt_filename}"
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=receipt_json.encode('utf-8'),
                ContentType='application/json'
            )
            print(f"Uploaded receipt to S3: s3://{self.bucket_name}/{s3_key}")
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error uploading receipt to S3: {e}")
        except Exception as e:
            print(f"General error uploading receipt to S3: {e}")
