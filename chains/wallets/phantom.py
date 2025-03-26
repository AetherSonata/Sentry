# chains/solana/wallets/phantom.py
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
import base58
from dotenv import load_dotenv
import os

class PhantomWallet:
    def __init__(self, rpc_endpoint="https://api.mainnet-beta.solana.com"):
        """Initialize Phantom wallet and connect to Solana."""
        # Load private key from .env
        load_dotenv()
        private_key = os.getenv("PHANTOM_PRIVATE_KEY")
        if not private_key:
            raise ValueError("PHANTOM_PRIVATE_KEY not found in .env")

        # Convert private key to Keypair
        self.keypair = Keypair.from_bytes(base58.b58decode(private_key))
        self.public_key = self.keypair.pubkey()

        # Connect to Solana RPC
        self.client = AsyncClient(rpc_endpoint)
        print(f"Connected to Solana with Phantom wallet: {self.public_key}")

    def get_keypair(self):
        """Return the Keypair for signing transactions."""
        return self.keypair

    def get_public_key(self):
        """Return the public key as a string."""
        return str(self.public_key)

    async def is_connected(self):
        """Check if the RPC connection is active."""
        return await self.client.is_connected()

    async def close(self):
        """Close the RPC connection."""
        await self.client.close_connection()