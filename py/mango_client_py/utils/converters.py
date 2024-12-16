# mango_client_py/utils/converters.py

from decimal import Decimal
from typing import Union

def to_native(amount: Union[int, float, Decimal], decimals: int) -> int:
    """Konvertiert einen Betrag in die native Darstellung basierend auf den Dezimalstellen."""
    return int(Decimal(amount) * (10 ** decimals))
