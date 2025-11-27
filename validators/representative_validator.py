"""Validador de representantes legais."""

from typing import List, Dict

from config.settings import DATA_NOT_AVAILABLE


class RepresentativeValidator:
    """Valida e normaliza dados de representantes legais."""
    
    @staticmethod
    def validate_and_normalize(representatives: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Valida e normaliza lista de representantes.
        
        - Preenche campos vazios com DATA_NOT_AVAILABLE
        - Remove duplicatas por nome
        - Remove procuradores
        - Valida consistência entre campos principais e de origem
        
        Args:
            representatives: Lista de representantes
            
        Returns:
            Lista normalizada e validada
        """
        if not representatives:
            return representatives
        
        # Preencher campos vazios
        for rep in representatives:
            RepresentativeValidator._fill_empty_fields(rep)
            RepresentativeValidator._validate_field_consistency(rep)
        
        # Filtrar procuradores
        filtered = RepresentativeValidator._filter_procuradores(representatives)
        
        # Remover duplicatas
        unique = RepresentativeValidator._remove_duplicates(filtered)
        
        return unique
    
    @staticmethod
    def _fill_empty_fields(rep: Dict[str, str]) -> None:
        """Preenche campos vazios com DATA_NOT_AVAILABLE."""
        required_fields = [
            "nome", "cpf", "cargo", "endereco_residencia",
            "tipo_assinatura", "origem_assinatura",
            "regras_representacao", "origem_regras_representacao",
            "data_validade_regras", "origem_data_validade"
        ]
        
        for field in required_fields:
            if not rep.get(field) or rep[field].strip() == "":
                rep[field] = DATA_NOT_AVAILABLE
        
        # Remove campo 'endereco' se existir (legado)
        if "endereco" in rep:
            del rep["endereco"]
    
    @staticmethod
    def _validate_field_consistency(rep: Dict[str, str]) -> None:
        """Valida consistência entre campos principais e campos de origem."""
        field_pairs = [
            ("tipo_assinatura", "origem_assinatura"),
            ("regras_representacao", "origem_regras_representacao"),
            ("data_validade_regras", "origem_data_validade")
        ]
        
        for main_field, origin_field in field_pairs:
            main_value = rep.get(main_field, "")
            origin_value = rep.get(origin_field, "")
            
            # Se campo principal vazio, origem deve estar vazia
            if main_value == DATA_NOT_AVAILABLE:
                if origin_value != DATA_NOT_AVAILABLE:
                    print(f"⚠️ INCONSISTÊNCIA: {rep.get('nome')} - {main_field} vazio mas {origin_field} tem valor")
                    rep[origin_field] = DATA_NOT_AVAILABLE
            
            # Se campo principal preenchido, origem NÃO pode estar vazia
            elif main_value and main_value != DATA_NOT_AVAILABLE:
                if origin_value == DATA_NOT_AVAILABLE or not origin_value:
                    print(f"🚨 ERRO: {rep.get('nome')} - {main_field} tem valor mas {origin_field} vazio!")
    
    @staticmethod
    def _filter_procuradores(representatives: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove procuradores da lista."""
        procurador_terms = ["PROCURADOR", "OUTORGADO", "MANDATÁRIO", "MANDATARIO", "PROCURACAO"]
        
        filtered = []
        for rep in representatives:
            cargo = rep.get("cargo", "").upper()
            
            # Se o cargo contém termo de procurador, não incluir
            if any(term in cargo for term in procurador_terms):
                print(f"⚠️ Procurador filtrado: {rep.get('nome')} - Cargo: {rep.get('cargo')}")
                continue
            
            filtered.append(rep)
        
        return filtered
    
    @staticmethod
    def _remove_duplicates(representatives: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicatas baseado no nome."""
        seen_names = set()
        unique = []
        
        for rep in representatives:
            nome_lower = rep.get("nome", "").lower().strip()
            
            if nome_lower and nome_lower != DATA_NOT_AVAILABLE.lower() and nome_lower not in seen_names:
                seen_names.add(nome_lower)
                unique.append(rep)
            elif not nome_lower or nome_lower == DATA_NOT_AVAILABLE.lower():
                # Incluir representantes sem nome válido (casos especiais)
                unique.append(rep)
        
        return unique
