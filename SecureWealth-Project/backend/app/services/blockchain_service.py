import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider

from backend.app.config import get_settings

logger = logging.getLogger("securewealth.blockchain")
settings = get_settings()

class BlockchainService:
    """
    Service for interacting with the SecureWealth Audit Ledger on Blockchain.
    Uses EthereumTesterProvider for simulation in development/hackathon environments.
    """

    def __init__(self):
        # In a real app, we'd use Web3.HTTPProvider(settings.BLOCKCHAIN_URL)
        # For the hackathon, we use EthereumTesterProvider for instant, local simulation.
        self.w3 = Web3(EthereumTesterProvider())
        self.account = self.w3.eth.accounts[0]
        self.contract_address = None
        self.contract_abi = self._get_audit_logger_abi()
        self.contract = None
        
        # PERSISTENT SIMULATED LEDGER (In-memory for prototype)
        # In a real app, these are fetched from the Smart Contract events
        self._simulated_ledger = [
            {
                "id": 1,
                "actor": self.account,
                "action_type": "LOGIN",
                "data_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "timestamp": int(time.time()) - 3600,
                "risk_label": "Low"
            }
        ]

    def _get_audit_logger_abi(self):
        # Minimal ABI for AuditLogger.sol
        return [
            {
                "inputs": [
                    {"internalType": "string", "name": "actionType", "type": "string"},
                    {"internalType": "string", "name": "dataHash", "type": "string"},
                    {"internalType": "string", "name": "riskLabel", "type": "string"}
                ],
                "name": "logEntry",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
                "name": "getEntry",
                "outputs": [
                    {"internalType": "address", "name": "actor", "type": "address"},
                    {"internalType": "string", "name": "actionType", "type": "string"},
                    {"internalType": "string", "name": "dataHash", "type": "string"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "string", "name": "riskLabel", "type": "string"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getEntryCount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    async def initialize(self):
        """Deploy the contract (for simulation) or connect to an existing one."""
        if not self.contract_address:
            # Simulated deployment
            logger.info("Deploying simulated AuditLogger contract...")
            self.contract_address = "0x" + "a" * 40 
            self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(self.contract_address), abi=self.contract_abi)
            logger.info(f"AuditLogger deployed at: {self.contract_address}")
        return self

    def _compute_hash(self, data: Any) -> str:
        """Compute a SHA-256 hash of the data."""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()

    async def log_action(self, action_type: str, payload: Any, risk_label: str = "Low") -> str:
        """
        Log a sensitive action to the blockchain.
        Returns the transaction hash (simulated).
        """
        data_hash = self._compute_hash(payload)
        
        try:
            logger.info(f"Logging {action_type} to blockchain. Hash: {data_hash}")
            
            # Simulated transaction hash
            tx_hash = f"0x{hashlib.sha256(str(time.time()).encode()).hexdigest()}"
            
            # Update the simulated ledger
            new_entry = {
                "id": len(self._simulated_ledger) + 1,
                "actor": self.account,
                "action_type": action_type,
                "data_hash": data_hash,
                "timestamp": int(time.time()),
                "risk_label": risk_label,
                "tx_hash": tx_hash
            }
            self._simulated_ledger.append(new_entry)
            
            return tx_hash
        except Exception as e:
            logger.error(f"Failed to log action to blockchain: {e}")
            raise

    async def get_audit_trail(self, limit: int = 10) -> List[Dict]:
        """Fetch the latest audit logs from the blockchain (simulated)."""
        # Return the last 'limit' items, newest first
        return sorted(self._simulated_ledger, key=lambda x: x['timestamp'], reverse=True)[:limit]

# Global instance
blockchain_service = BlockchainService()
