# mango_client_py/accounts/bank.py

from dataclasses import dataclass
from solana.publickey import PublicKey
from typing import Dict, Any

@dataclass
class Bank:
    public_key: PublicKey
    mint: PublicKey
    token_index: int
    vault: PublicKey
    oracle: PublicKey
    fallback_oracle: PublicKey
    force_withdraw: bool
    # Weitere Felder entsprechend TypeScript-Definitionen

    @classmethod
    def from_account(cls, public_key: PublicKey, account_data: Dict[str, Any]) -> 'Bank':
        # Implementieren Sie die Logik zum Erstellen einer Bank-Instanz aus Account-Daten
        return cls(
            public_key=public_key,
            mint=PublicKey(account_data['mint']),
            token_index=account_data['token_index'],
            vault=PublicKey(account_data['vault']),
            oracle=PublicKey(account_data['oracle']),
            fallback_oracle=PublicKey(account_data['fallback_oracle']),
            force_withdraw=account_data.get('force_withdraw', False),
            # Weitere Felder
        )
