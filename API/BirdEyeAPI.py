import requests

# # Birdeye API URL for fetching trending tokens on Solana
# BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/token_trending"

# # Headers required for the API request
# HEADERS = {
#     "accept": "application/json",
#     "x-chain": "solana"
# }

def get_trending_tokens_birdeye(limit=20):
#     """
#     Fetches the top trending tokens on Solana from Birdeye API.
    
#     :param limit: Number of trending tokens to fetch (default: 20)
#     :return: List of trending tokens with their details
#     """
#     try:
#         # API request parameters
#         params = {
#             "sort_by": "rank",
#             "sort_type": "asc",
#             "offset": 0,
#             "limit": limit
#         }

#         # Sending GET request to Birdeye API
#         response = requests.get(BIRDEYE_API_URL, headers=HEADERS, params=params)
        
#         if response.status_code == 200:
#             data = response.json()

#             trending_tokens = []
#             for token in data.get("data", []):  # Extract token list from API response
#                 token_info = {
#                     "name": token.get("name", "Unknown"),
#                     "symbol": token.get("symbol", "Unknown"),
#                     "address": token.get("address", "N/A"),
#                     "price": token.get("price", "N/A"),
#                     "volume_24h": token.get("volume_24h", "N/A"),
#                     "market_cap": token.get("market_cap", "N/A"),
#                     "rank": token.get("rank", "N/A"),
#                 }
#                 trending_tokens.append(token_info)
            
#             return trending_tokens
#         else:
#             print(f"Error fetching data: {response.status_code}, {response.text}")
#             return []
    
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return []


    url = "https://public-api.birdeye.so/defi/token_trending?sort_by=rank&sort_type=asc&offset=0&limit=20"

    headers = {
        "accept": "application/json",
        "x-chain": "solana"
    }

    response = requests.get(url, headers=headers)

    print(response.text)