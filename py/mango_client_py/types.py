# mango_client_py/types.py

from dataclasses import dataclass
from solana.publickey import PublicKey
from typing import Dict, Any, List, Optional

@dataclass
class Group:
    public_key: PublicKey
    insurance_vault: PublicKey
    address_lookup_tables_list: List[Any]  # Typ entsprechend anpassen
    mint_infos_map_by_token_index: Dict[int, Any]  # Typ anpassen

    @classmethod
    def from_account(cls, public_key: PublicKey, account_data: Dict[str, Any]) -> 'Group':
        # Implementieren Sie die Logik zum Erstellen einer Group-Instanz aus Account-Daten
        return cls(
            public_key=public_key,
            insurance_vault=PublicKey(account_data.get('insurance_vault')),
            address_lookup_tables_list=[],  # Anpassen entsprechend
            mint_infos_map_by_token_index={},  # Anpassen entsprechend
            # Weitere Felder
        )

    async def reload_all(self, client: Any):
        # Implementieren Sie die Logik zum Laden zusätzlicher Daten
        pass

@dataclass
class MangoAccount:
    public_key: PublicKey
    owner: PublicKey
    sequence_number: int
    # Weitere Felder entsprechend TypeScript-Definitionen

    @classmethod
    def from_account(cls, public_key: PublicKey, account_data: Dict[str, Any]) -> 'MangoAccount':
        # Implementieren Sie die Logik zum Erstellen einer MangoAccount-Instanz aus Account-Daten
        return cls(
            public_key=public_key,
            owner=PublicKey(account_data.get('owner')),
            sequence_number=account_data.get('sequence_number', 0),
            # Weitere Felder
        )

@dataclass
class StubOracle:
    public_key: PublicKey
    val: float
    # Weitere Felder entsprechend TypeScript-Definitionen

    @classmethod
    def from_account(cls, public_key: PublicKey, account_data: Dict[str, Any]) -> 'StubOracle':
        return cls(
            public_key=public_key,
            val=account_data.get('val', 0.0),
            # Weitere Felder
        )

# Weitere Datenklassen können hier hinzugefügt werden

class HealthCheckKind:
    # Definieren Sie die möglichen Arten von Health Checks
    pass

class MangoSignatureStatus:
    # Implementieren Sie die Klasse entsprechend Ihrer Anwendung
    pass

# Weitere Typen und Klassen können hier hinzugefügt werden
