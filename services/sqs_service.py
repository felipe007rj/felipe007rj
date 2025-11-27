"""Serviço de comunicação com Amazon SQS."""

import botocore
from typing import Any, Dict, Optional


class SQSService:
    """Gerencia operações com Amazon SQS."""
    
    def __init__(self, sqs_client, input_queue_url: str, output_queue_url: str, dlq_url: str):
        """
        Inicializa o serviço SQS.
        
        Args:
            sqs_client: Cliente boto3 do SQS
            input_queue_url: URL da fila de entrada
            output_queue_url: URL da fila de saída
            dlq_url: URL da Dead Letter Queue
        """
        self.client = sqs_client
        self.input_queue_url = input_queue_url
        self.output_queue_url = output_queue_url
        self.dlq_url = dlq_url
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Recebe uma mensagem da fila de entrada.
        
        Returns:
            Mensagem recebida ou None se não houver mensagens
        """
        try:
            response = self.client.receive_message(
                QueueUrl=self.input_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
            messages = response.get('Messages', [])
            if not messages:
                return None
            
            msg = messages[0]
            print(f"Received SQS message: {msg}")
            return msg
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error receiving SQS message: {e}")
            return None
    
    def send_message(self, message_body: str, queue_url: Optional[str] = None) -> None:
        """
        Envia uma mensagem para uma fila.
        
        Args:
            message_body: Corpo da mensagem
            queue_url: URL da fila (usa output_queue_url se None)
        """
        if queue_url is None:
            queue_url = self.output_queue_url
        
        try:
            self.client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body
            )
            print(f"Sent message to SQS queue: {queue_url}")
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error sending message to SQS queue {queue_url}: {e}")
    
    def delete_message(self, receipt_handle: str) -> None:
        """
        Remove uma mensagem da fila de entrada.
        
        Args:
            receipt_handle: Handle da mensagem
        """
        try:
            self.client.delete_message(
                QueueUrl=self.input_queue_url,
                ReceiptHandle=receipt_handle
            )
            print(f"Deleted SQS message with receipt handle: {receipt_handle}")
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error deleting SQS message: {e}")
    
    def send_to_dlq(self, message_body: str) -> None:
        """
        Envia uma mensagem para a Dead Letter Queue.
        
        Args:
            message_body: Corpo da mensagem
        """
        self.send_message(message_body, queue_url=self.dlq_url)
