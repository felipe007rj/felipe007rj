"""Modelo de dados para Representante Legal."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Representative:
    """Representa um representante legal da empresa."""
    
    nome: str = ""
    cpf: str = ""
    cargo: str = ""
    endereco_residencia: str = ""
    tipo_assinatura: str = ""
    origem_assinatura: str = ""
    regras_representacao: str = ""
    origem_regras_representacao: str = ""
    data_validade_regras: str = ""
    origem_data_validade: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Converte o representante para dicionário."""
        return {
            'nome': self.nome,
            'cpf': self.cpf,
            'cargo': self.cargo,
            'endereco_residencia': self.endereco_residencia,
            'tipo_assinatura': self.tipo_assinatura,
            'origem_assinatura': self.origem_assinatura,
            'regras_representacao': self.regras_representacao,
            'origem_regras_representacao': self.origem_regras_representacao,
            'data_validade_regras': self.data_validade_regras,
            'origem_data_validade': self.origem_data_validade
        }
