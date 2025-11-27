"""Validador de datas."""


class DateValidator:
    """Valida datas."""
    
    @staticmethod
    def is_valid_date(day: str, month: str, year: str) -> bool:
        """
        Valida se dia, mês e ano formam uma data válida.
        
        Args:
            day: Dia (1-31)
            month: Mês (1-12)
            year: Ano (>= 1900)
            
        Returns:
            True se válida, False caso contrário
        """
        try:
            return (1 <= int(day) <= 31 and 
                    1 <= int(month) <= 12 and 
                    int(year) >= 1900)
        except ValueError:
            return False
