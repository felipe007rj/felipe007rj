"""
Configurações centralizadas do projeto.
Todas as variáveis de ambiente, constantes e padrões.
"""

import os

# --- AWS CONFIGURATION ---
SQS_INPUT_QUEUE_URL = os.getenv(
    'SQS_INPUT_QUEUE_URL',
    'https://sqs.us-east-1.amazonaws.com/337909753777/firp-automacao-ia-in-sqs-dev'
)
SQS_OUTPUT_QUEUE_URL = os.getenv(
    'SQS_OUTPUT_QUEUE_URL',
    'https://sqs.us-east-1.amazonaws.com/337909753777/firp-automacao-ia-out-sqs-dev'
)
SQS_INPUT_DLQ_URL = os.getenv(
    'SQS_INPUT_DLQ_URL',
    'https://sqs.us-east-1.amazonaws.com/337909753777/firp-automacao-ia-in-sqsdlq-dev'
)
S3_BUCKET = os.getenv('S3_BUCKET', 'firp-automacao-ia-s3-dev')
REGION_NAME = os.getenv('REGION_NAME', 'us-east-1')

# --- GOOGLE CLOUD CONFIGURATION ---
DOCUMENT_AI_PROJECT = os.getenv('DOCUMENT_AI_PROJECT', 'nuclea-gen-ai-firmas-e-poderes')
DOCUMENT_AI_LOCATION = os.getenv('DOCUMENT_AI_LOCATION', 'us')
DOCUMENT_AI_PROCESSOR_ID = os.getenv('DOCUMENT_AI_PROCESSOR_ID', '3e6fc341c0db2e0f')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# --- SECRETS CONFIGURATION ---
GCLOUD_SECRET_KEY = os.getenv('GCLOUD_SECRET_KEY', 'CREDENCIAL-FIRP-AUTOMACAO-IA-DEV')
GEMINI_SECRET_KEY = os.getenv('GEMINI_SECRET_KEY', 'API-KEY-FIRP-AUTOMACAO-IA-DEV')
SECRET_NAME = os.getenv('SECRET_NAME', 'Automacao/DEV')

# --- PROMPT CONFIGURATION ---
PROMPT_URI = os.getenv(
    'PROMPT_URI',
    'prompt/base_prompt_v31.txt'
)

# --- PROCESSING CONSTANTS ---
DEFAULT_MAX_PAGES = 15
CNPJ_LENGTH = 14
REQUEST_TIMEOUT = 5
MAX_DOCUMENTS_PER_REQUEST = 3

# --- CNPJ FORMATTING INDICES ---
CNPJ_FIRST_BLOCK_END = 2
CNPJ_SECOND_BLOCK_END = 5
CNPJ_THIRD_BLOCK_END = 8
CNPJ_FOURTH_BLOCK_END = 12

# --- REGEX PATTERNS ---
EXTENDED_DATE_PATTERN = r"\d+\s+de\s+[a-z]+\s+de\s+\d{4}"
SIMPLE_DATE_PATTERN = r"(\d{1,2}/\d{1,2}/\d{4})"
MONTH_DATE_PATTERN = r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})"
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

# --- DEFAULT VALUES ---
DATA_NOT_AVAILABLE = "Dado não disponível no documento"
REPRESENTANTES_LEGAIS_FIELD = "representantes legais"

# --- DEFAULT RESPONSE FIELDS ---
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

# --- FIELD EXTRACTION TARGETS ---
FIELD_TARGETS = {
    "junta_comercial": "Junta Comercial:",
    "cnpj": "CNPJ:",
    "razao_social": "Razão Social:",
    "natureza_juridica": "Natureza Jurídica:",
    "endereco": "Endereço:",
    "cotas_societarias": "Cotas societárias:",
    "representantes_legais": REPRESENTANTES_LEGAIS_FIELD,
    "representantes_detalhados": REPRESENTANTES_LEGAIS_FIELD,
    "referencia_da_origem": "Referência da origem:",
    "data_assinatura": "Data de assinatura:"
}

# --- MONTH NAMES FOR DATE PARSING ---
MONTH_NAMES = {
    'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03', 'abril': '04',
    'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08', 'setembro': '09',
    'outubro': '10', 'novembro': '11', 'dezembro': '12'
}

# --- DOCUMENT TYPE MAPPINGS ---
DOCUMENT_TYPE_TO_NAME = {
    'PROCURACAO': 'Procuração',
    'ATA_DE_ASSEMBLEIA': 'Ata de Assembleia Geral',
    'ATA_DE_ELEICAO': 'Ata de Eleição',
    'CONTRATO_SOCIAL': 'Contrato Social',
    'ADITAMENTO': 'Aditamento',
    'ESTATUTO_SOCIAL': 'Estatuto Social',
    'CERTIDAO': 'Certidão',
    'FICHA_CADASTRAL': 'Ficha Cadastral',
}

# --- ACCESSORY AND CORPORATE DOCUMENT TYPES ---
ACCESSORY_DOCUMENT_TYPES = ["PROCURACAO", "ADITAMENTO", "CERTIDAO", "FICHA_CADASTRAL"]
CORPORATE_DOCUMENT_TYPES = ["ESTATUTO_SOCIAL", "ATA_DE_ASSEMBLEIA", "ATA_DE_ELEICAO", "CONTRATO_SOCIAL"]

# --- INVALID LAW DATES (NOT SIGNATURES) ---
INVALID_LAW_DATES = [
    "15/12/1976",  # Lei 6.404/76 (Lei das S.A.)
    "10/01/2002",  # Lei 10.406/02 (Código Civil)
    "11/08/1993",  # Lei 8.666/93 (Licitações)
    "05/10/1988",  # Constituição Federal
]
