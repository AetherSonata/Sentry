# chains/solana_utils.py
import asyncio
from solana.rpc.async_api import AsyncClient  # Correct AsyncClient import
import aiohttp
from solders.transaction import Transaction   # Correct Transaction import
from solana.rpc.types import TokenAccountOpts
import base58

class SolanaUtils:
    def __init__(self, keypair, rpc_endpoint="https://api.mainnet-beta.solana.com"):
        """Initialize utils with a Keypair and RPC endpoint."""
        self.keypair = keypair
        self.public_key = keypair.pubkey()
        self.client = AsyncClient(rpc_endpoint)
        self.session = aiohttp.ClientSession()

    async def fetch_sol_balance(self):
        """Fetch the SOL balance of the connected wallet."""
        balance = await self.client.get_balance(self.public_key)
        sol_balance = balance.value / 1_000_000_000  # Convert lamports to SOL
        print(f"SOL Balance: {sol_balance}")
        return sol_balance


    async def fetch_token_balance(self, token_mint_address):
        """Fetch the balance of a specific SPL token."""
        opts = TokenAccountOpts(program_id="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")  # SPL Token Program
        response = await self.client.get_token_accounts_by_owner(self.public_key, opts)
        for account in response.value:
            token_info = await self.client.get_token_account_balance(account.pubkey)
            if token_info.value.mint == token_mint_address:
                amount = token_info.value.ui_amount
                print(f"Token Balance ({token_mint_address}): {amount}")
                return amount
        print(f"No balance found for {token_mint_address}")
        return 0

    async def place_buy_order(self, token_mint_address, amount_in_sol, slippage_bps=500):
        """Place a buy order for a meme coin using SOL via Jupiter API."""
        quote_url = (
            f"https://quote-api.jup.ag/v6/quote?"
            f"inputMint=So11111111111111111111111111111111111111112&"  # SOL
            f"outputMint={token_mint_address}&"
            f"amount={int(amount_in_sol * 1_000_000_000)}&"  # SOL to lamports
            f"slippageBps={slippage_bps}"
        )
        async with self.session.get(quote_url) as resp:
            quote = await resp.json()

        swap_url = "https://quote-api.jup.ag/v6/swap"
        payload = {"userPublicKey": str(self.public_key), "quoteResponse": quote}
        async with self.session.post(swap_url, json=payload) as resp:
            swap_data = await resp.json()
            serialized_tx = swap_data["swapTransaction"]

        tx = Transaction.deserialize(base58.b58decode(serialized_tx))
        tx.sign(self.keypair)
        tx_id = await self.client.send_transaction(tx)
        print(f"Buy Order Tx ID: {tx_id.value}")
        return tx_id.value

    async def place_sell_order(self, token_mint_address, amount_to_sell, slippage_bps=500):
        """Place a sell order for a meme coin back to SOL via Jupiter API."""
        quote_url = (
            f"https://quote-api.jup.ag/v6/quote?"
            f"inputMint={token_mint_address}&"
            f"outputMint=So11111111111111111111111111111111111111112&"  # SOL
            f"amount={int(amount_to_sell * 1_000_000)}&"  # Adjust decimals (e.g., 6)
            f"slippageBps={slippage_bps}"
        )
        async with self.session.get(quote_url) as resp:
            quote = await resp.json()

        swap_url = "https://quote-api.jup.ag/v6/swap"
        payload = {"userPublicKey": str(self.public_key), "quoteResponse": quote}
        async with self.session.post(swap_url, json=payload) as resp:
            swap_data = await resp.json()
            serialized_tx = swap_data["swapTransaction"]

        tx = Transaction.deserialize(base58.b58decode(serialized_tx))
        tx.sign(self.keypair)
        tx_id = await self.client.send_transaction(tx)
        print(f"Sell Order Tx ID: {tx_id.value}")
        return tx_id.value

    async def close(self):
        """Clean up resources."""
        await self.session.close()
        await self.client.close_connection()

    def run_sync(self, coro):
        """Run an async coroutine synchronously."""
        return asyncio.run(coro)