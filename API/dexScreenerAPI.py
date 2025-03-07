import requests

# Dexscreener API endpoint for Solana trending pairs
DEX_API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

def get_trending_tokens():
    """Fetch trending Solana tokens from Dexscreener API."""
    try:
        response = requests.get(DEX_API_URL)
        if response.status_code == 200:
            data = response.json()
            
            trending_tokens = []
            for pair in data.get("pairs", []):
                base_token = pair["baseToken"]
                token_info = {
                    "name": base_token["name"],
                    "symbol": base_token["symbol"],
                    "mint": base_token["address"],
                    "price": base_token.get("price", "N/A")
                }
                trending_tokens.append(token_info)
            
            return trending_tokens
        else:
            print(f"Error fetching data: {response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
