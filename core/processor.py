"""
Core Processor - Orquestrador Principal da Aplicação.
Integra todos os módulos: extractors, processors, services, validators.

Este é o resultado final da refatoração - substitui o FirpAIProcessor original.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime

# Services
from services import SQSService, S3Service, OCRService, GenAIService, PDFService

# Extractors
from extractors import (
    CNPJExtractor,
    CompanyExtractor,
    DateExtractor,
    DocumentExtractor,
    RepresentativeExtractor,
    FieldExtractor
)

# Processors
from processors import (
    GeminiResponseProcessor,
    MultiDocumentProcessor,
    ProcuracaoProcessor,
    ResponseBuilder
)

# Validators
from validators import MessageValidator, DateValidator, RepresentativeValidator

# Models
from models import Receipt

# Config
from config import settings, SecretsManager


class CoreProcessor:
    """
    Orquestrador principal da aplicação.
    Substitui o FirpAIProcessor original com arquitetura modular.
    """
    
    def __init__(self):
        """Inicializa todos os módulos necessários."""
        print("🚀 Inicializando CoreProcessor...")
        
        # Inicializar credenciais
        self._initialize_credentials()
        
        # Services
        self._initialize_services()
        
        # Extractors
        self._initialize_extractors()
        
        # Processors
        self._initialize_processors()
        
        # Validators
        self._initialize_validators()
        
        # Receipt para tracking
        self.receipt = None
        
        print("✅ CoreProcessor inicializado com sucesso!")
    
    def _initialize_credentials(self):
        """Inicializa credenciais do Secrets Manager."""
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager', region_name=settings.REGION_NAME)
            secrets_manager = SecretsManager(secrets_client)
            
            secrets = secrets_manager.get_secrets(settings.SECRET_NAME)
            self.gemini_api_key = secrets.get('GEMINI_API_KEY')
            self.gcloud_credentials = secrets.get('GCLOUD_CREDENTIALS')
            
            # Salvar credenciais Google Cloud
            secrets_manager.save_gcloud_credentials(self.gcloud_credentials)
            
        except Exception as e:
            print(f"⚠️  Erro ao obter credenciais: {e}")
            self.gemini_api_key = None
            self.gcloud_credentials = None
    
    def _initialize_services(self):
        """Inicializa os services."""
        import boto3
        
        # Criar clientes boto3
        sqs_client = boto3.client('sqs', region_name=settings.REGION_NAME)
        s3_client = boto3.client('s3', region_name=settings.REGION_NAME)
        
        self.sqs_service = SQSService(
            sqs_client=sqs_client,
            input_queue_url=settings.SQS_INPUT_QUEUE_URL,
            output_queue_url=settings.SQS_OUTPUT_QUEUE_URL,
            dlq_url=settings.SQS_INPUT_DLQ_URL
        )
        
        self.s3_service = S3Service(
            s3_client=s3_client,
            bucket_name=settings.S3_BUCKET
        )
        
        # Criar cliente Document AI
        from google.api_core.client_options import ClientOptions
        from google.cloud import documentai_v1beta3 as documentai
        
        client_options = ClientOptions(
            api_endpoint=f"{settings.DOCUMENT_AI_LOCATION}-documentai.googleapis.com"
        )
        documentai_client = documentai.DocumentProcessorServiceClient(
            client_options=client_options
        )
        
        self.ocr_service = OCRService(
            documentai_client=documentai_client,
            project=settings.DOCUMENT_AI_PROJECT,
            location=settings.DOCUMENT_AI_LOCATION,
            processor_id=settings.DOCUMENT_AI_PROCESSOR_ID
        )
        
        # Criar cliente Gemini
        from google import genai
        genai_client = genai.Client(api_key=self.gemini_api_key)
        
        # Carregar base prompt
        base_prompt = self.s3_service.get_prompt(settings.PROMPT_URI)
        
        self.genai_service = GenAIService(
            genai_client=genai_client,
            model_name=settings.GEMINI_MODEL,
            base_prompt=base_prompt
        )
        
        self.pdf_service = PDFService()
    
    def _initialize_extractors(self):
        """Inicializa os extractors."""
        self.cnpj_extractor = CNPJExtractor()
        self.company_extractor = CompanyExtractor()
        self.date_extractor = DateExtractor()
        self.document_extractor = DocumentExtractor()
        self.representative_extractor = RepresentativeExtractor()
        self.field_extractor = FieldExtractor()
    
    def _initialize_processors(self):
        """Inicializa os processors."""
        self.gemini_processor = GeminiResponseProcessor()
        self.multi_doc_processor = MultiDocumentProcessor()
        self.procuracao_processor = ProcuracaoProcessor()
        self.response_builder = ResponseBuilder()
    
    def _initialize_validators(self):
        """Inicializa os validators."""
        self.message_validator = MessageValidator()
        self.date_validator = DateValidator()
        self.representative_validator = RepresentativeValidator()
    
    def new_receipt(self):
        """Inicializa um novo receipt para tracking."""
        self.receipt = Receipt(
            request_id=None,
            message=None,
            ocr_data=[],
            genai_data=None,
            output_response=None,
            start_time=datetime.now().isoformat(),
            end_time=None,
            document_info=None
        )
    
    def process_loop(self):
        """
        Loop principal de processamento.
        Substitui o loop do main() original.
        """
        print("🔄 Iniciando loop de processamento...")
        
        while True:
            try:
                # Buscar mensagem
                msg = self.sqs_service.receive_message()
                
                if not msg:
                    print("⏳ Sem mensagens na fila, aguardando...")
                    time.sleep(5)
                    continue
                
                # Processar mensagem
                success = self.process_message(msg)
                
                if success:
                    # Deletar mensagem processada
                    self.sqs_service.delete_message(msg['ReceiptHandle'])
                    print("✅ Mensagem processada e deletada da fila")
                else:
                    print("❌ Falha no processamento")
                
            except KeyboardInterrupt:
                print("\n⏹️  Interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro no loop: {e}")
                time.sleep(5)
    
    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Processa uma mensagem SQS completa.
        
        Args:
            message: Mensagem SQS
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Inicializar receipt
            self.new_receipt()
            
            # Validar mensagem
            if not self.message_validator.validate_sqs_message(message):
                print("❌ Mensagem inválida, enviando para DLQ")
                self.sqs_service.send_to_dlq(message['Body'])
                return True  # Retorna True para deletar da fila principal
            
            # Processar PDFs
            ocr_text, processed_files = self.process_pdfs(message['Body'])
            
            if not ocr_text:
                print("❌ Falha no processamento de PDFs")
                return False
            
            # Chamar Gemini
            print("🤖 Chamando Gemini API...")
            prompt = self._build_prompt(ocr_text)
            gemini_response, genai_metadata = self.genai_service.generate_content(prompt)
            
            # Armazenar metadados do Gemini no receipt
            if genai_metadata:
                self.receipt.genai_data = genai_metadata
            
            if not gemini_response:
                print("❌ Falha na chamada do Gemini")
                return False
            
            # Processar resposta Gemini
            data_out = self._process_gemini_response(gemini_response, ocr_text)
            
            # Processar representantes
            data_out = self._process_representatives(gemini_response, data_out)
            
            # Processar procurações
            data_out = self.procuracao_processor.augment_with_procuracao(
                ocr_text, data_out, self.date_extractor
            )
            
            # Construir resposta final
            json_response = self.build_final_response(
                data_out, processed_files, gemini_response
            )
            
            # Enviar para fila de saída
            self.sqs_service.send_message(json_response, queue_url=settings.SQS_OUTPUT_QUEUE_URL)
            
            # Upload receipt para S3
            self._upload_receipt()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")
            return False
    
    def process_pdfs(self, message_body: str) -> tuple:
        """
        Processa PDFs da mensagem.
        
        Args:
            message_body: Body da mensagem SQS
            
        Returns:
            Tupla (ocr_text, processed_files)
        """
        try:
            import json
            data = json.loads(message_body)
        except Exception as e:
            print(f"❌ Erro ao parsear mensagem: {e}")
            return "", []
        
        self.receipt.request_id = data.get('id', '')
        
        # Identificar múltiplos documentos
        pdf_uris = data.get('pdf_uris', [])
        total_docs = len(pdf_uris)
        
        # Limite máximo
        MAX_DOCUMENTS = 3
        if total_docs > MAX_DOCUMENTS:
            print(f"⚠️  {total_docs} documentos detectados, processando apenas {MAX_DOCUMENTS}")
            pdf_uris = pdf_uris[:MAX_DOCUMENTS]
        
        # Armazenar info de documentos
        self.receipt.document_info = {
            'total_documents': total_docs,
            'processed_documents': len(pdf_uris),
            'is_multiple_documents': len(pdf_uris) > 1,
            'exceeded_limit': total_docs > MAX_DOCUMENTS,
            'ignored_documents': pdf_uris[MAX_DOCUMENTS:] if total_docs > MAX_DOCUMENTS else []
        }
        
        print(f"📄 Processando {len(pdf_uris)} documento(s)")
        
        # Processar cada PDF
        pdf_texts = []
        processed_files = []
        
        for i, uri in enumerate(pdf_uris, 1):
            print(f"📥 Processando documento {i}/{len(pdf_uris)}: {uri}")
            
            # Download do S3
            pdf_bytes = self.s3_service.download_object(uri)
            if not pdf_bytes:
                print(f"❌ Falha no download: {uri}")
                continue
            
            # Split se necessário
            pdf_chunks, total_pages = self.pdf_service.split_pdf_if_needed(
                pdf_bytes, max_pages=15
            )
            
            print(f"📃 {total_pages} páginas, {len(pdf_chunks)} chunk(s)")
            
            # OCR de cada chunk
            chunk_texts = []
            for j, chunk in enumerate(pdf_chunks, 1):
                print(f"🔍 OCR chunk {j}/{len(pdf_chunks)}...")
                ocr_result = self.ocr_service.process_document(chunk)
                if ocr_result:
                    chunk_texts.append(ocr_result)
            
            # Juntar chunks
            pdf_text = "\n".join(chunk_texts)
            
            # Extrair metadados
            metadata = self.document_extractor.extract_document_metadata(
                pdf_text, i, uri, self.date_extractor
            )
            
            processed_files.append(metadata)
            
            # Criar texto marcado (sem prioridade para LLM)
            if len(pdf_uris) > 1:
                marked_text = self.multi_doc_processor.create_marked_document_text_no_priority(
                    i, len(pdf_uris), metadata['file_name'], pdf_text, metadata
                )
                pdf_texts.append(marked_text)
            else:
                pdf_texts.append(pdf_text)
            
            # Armazenar no receipt
            self.receipt.ocr_data.append({
                "document_index": i,
                "file_name": metadata['file_name'],
                "ocr_text": pdf_text,
                "total_pages": total_pages,
                "chunks_processed": len(pdf_chunks)
            })
        
        # Juntar todos os textos
        ocr_text = "\n\n".join(pdf_texts)
        
        return ocr_text, processed_files
    
    def build_final_response(self, data_out: Dict[str, Any], 
                            processed_files: List[Dict], 
                            gemini_response: str) -> str:
        """
        Constrói a resposta JSON final.
        
        Args:
            data_out: Dados extraídos
            processed_files: Lista de arquivos processados
            gemini_response: Resposta do Gemini
            
        Returns:
            JSON string da resposta
        """
        # Normalizar output
        data_out = self.response_builder.normalize_output(
            data_out, self.cnpj_extractor, self.date_extractor
        )
        
        # Validar campos obrigatórios
        data_out = self.response_builder.validate_required_fields(data_out)
        
        # Limpar dados
        data_out = self.response_builder.clean_output(data_out)
        
        # Análise de múltiplos documentos (se aplicável)
        priority_analysis = None
        changes_summary = None
        conflicts = None
        
        if len(processed_files) > 1:
            priority_analysis = self.multi_doc_processor.analyze_document_priority(processed_files)
            changes_summary = self.multi_doc_processor.generate_changes_summary(
                processed_files, gemini_response
            )
            conflicts = self.multi_doc_processor.detect_potential_conflicts(processed_files)
        
        # Construir resposta
        json_response = self.response_builder.build_response(
            self.receipt.request_id,
            data_out,
            self.receipt.document_info,
            priority_analysis,
            changes_summary,
            conflicts
        )
        
        self.receipt.output_response = json_response
        self.receipt.end_time = datetime.now().isoformat()
        
        return json_response
    
    def _build_prompt(self, ocr_text: str) -> str:
        """Constrói o prompt para o Gemini."""
        # Usar o método do GenAIService que já tem o prompt base carregado
        return self.genai_service.build_prompt(ocr_text)
    
    def _process_gemini_response(self, gemini_response: str, ocr_text: str) -> Dict[str, Any]:
        """Processa resposta do Gemini."""
        # Extrair JSON ou fazer parse de texto
        data_out = self.gemini_processor.extract_json_from_response(gemini_response)
        
        if not data_out or not data_out.get('cnpj'):
            # Fallback para parse de texto
            data_out = self.gemini_processor.parse_text_response(
                gemini_response, self.field_extractor
            )
        
        # Aplicar fallbacks de OCR
        data_out = self.gemini_processor.apply_fallbacks(
            data_out, ocr_text, 
            self.cnpj_extractor, 
            self.company_extractor
        )
        
        # Validar campos finais
        data_out = self.gemini_processor.validate_final_fields(data_out)
        
        return data_out
    
    def _process_representatives(self, gemini_response: str, 
                                data_out: Dict[str, Any]) -> Dict[str, Any]:
        """Processa representantes da resposta Gemini."""
        # Extrair representantes detalhados
        representatives = self.representative_extractor.extract_detailed_representatives(
            gemini_response.split('\n')
        )
        
        # Calcular quantidade
        count = self.representative_extractor.calculate_count(representatives)
        
        # Consolidar poderes
        poderes = self.gemini_processor.consolidate_poderes_representacao(representatives)
        
        # Atualizar data_out
        data_out['representantes_detalhados'] = representatives
        data_out['quantidade_representantes'] = count
        data_out['poderes_e_representacao'] = poderes
        
        # Nomes dos representantes
        names = [rep.get('nome', '') for rep in representatives 
                if rep.get('nome') and rep['nome'] != "Dado não disponível no documento"]
        data_out['representantes_legais'] = '\n'.join(names)
        
        return data_out
    
    def _upload_receipt(self):
        """Upload do receipt para S3."""
        try:
            # Usar método específico do S3Service
            self.s3_service.upload_receipt(
                request_id=self.receipt.request_id,
                receipt_data=self.receipt.__dict__
            )
            
        except Exception as e:
            print(f"⚠️  Erro ao enviar receipt: {e}")
