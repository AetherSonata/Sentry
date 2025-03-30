from chains.wallets.phantom import PhantomWallet
from tasks.task_manager import TokenTaskManager
import asyncio

TEST_TOKENS = [ 
                    #   "CniPCE4b3s8gSUPhUiyMjXnytrEqUrMfSsnbBjLCpump",
                    #   "AQiE2ghyFbBsbsfHiTEbKWcCLTDgyGzceKEPWftZpump"
                    #   "FWAr6oWa6CHg6WUcXu8CqkmsdbhtEqL8t31QTonppump",         # Bullish scenario
                    #   "FtUEW73K6vEYHfbkfpdBZfWpxgQar2HipGdbutEhpump",
                    #   "EF3Ln1DkUB5azvqcaCJgG3RR2qSUJEXxLo1q4ZHzpump",           # Long Term scenario
                    #   "GYTd9XbZTfwicCV28LGkwiDF4DgpXTTAi2UeCajfpump",
                    #   "hV7MQkCpjvuTTnPJXPhPXzvmtMxk8A8ct1KPiRMpump",
                    #   "UL1jwqh3ARmdNTE5qUQyaXHDcrAZ988GZ6tp21Epump",
                    #   "5e41GfrQwTP74LgGt6WP9kw6xa1jQhAERCjnFKf74y52",
                    #   "FS4xcBxLJbrrdXE1R6zHvKw8no4zrQn2rRFuczvepump",           # dying scenario - good for testing
                    #   "9YnfbEaXPaPmoXnKZFmNH8hzcLyjbRf56MQP7oqGpump",             # flat scenario
                    #   "2yFiCwdLiUfxq9PcNXQvu16QdgBFniCJP8P8gEXNpump",
                    #   "H4phNbsqjV5rqk8u6FUACTLB6rNZRTAPGnBb8KXJpump",             # 12000 interval long term scenario
                    #   "9eXC6W3ZKnkNnCr9iENExRLJDYfPGLbc4m6qfJzJpump",
                    #   "2TUQ21D87yrbZM1F3RB93sbkiGXeTTfkb8wWqG2ipump",
                    #   "9pViBf84zD4ncn8Mj8rtdtojnRkxBpibPEjbaGW6pump",
                    # "3rdCUNNgj52frYdp3cJLwQ6xzJibjyjsPCtNMRUDpump",
                    "EQf2LYaw4zV3hb2UK5kCUSgFrLRJqUAaeVA9rMypump",
                    ]  


def collect_and_filter_candidates(testing_mode = True):
    if testing_mode:
        #collect data from testing data source
        trending_tokens = TEST_TOKENS
    else:
    #fetch trending tokens
        def fetch_trending_tokens():
            pass
        trending_tokens = fetch_trending_tokens()

    #filter tokens by criteria
    #filter by volume
    #filter by volatility
    #filter by market cap
    #filter by price
    #filter by sentiment

    return trending_tokens
        

async def main():
    testing_mode = True
    user_id = "user1"  # Single user for now
    wallet = PhantomWallet()
    sol_balance = await wallet.solanaUtils.fetch_sol_balance()
    print(f"Initial SOL Balance: {sol_balance}")

    task_manager = TokenTaskManager()
    initial_tokens = collect_and_filter_candidates(testing_mode)

    # Start monitoring initial tokens
    for token in initial_tokens:
        await task_manager.add_token(user_id, testing_mode, token, wallet)

    # Example: Dynamically add/remove tokens
    # await asyncio.sleep(10)  # Run for 10 seconds
    # await task_manager.add_token(user_id, testing_mode, "NEW_TOKEN", wallet)
    # await asyncio.sleep(10)
    # await task_manager.remove_token(user_id, initial_tokens[0])

    # Keep running indefinitely (or until interrupted)
    try:
        await asyncio.Future()  # Wait forever
    except KeyboardInterrupt:
        await task_manager.shutdown(user_id)
        await wallet.close()

if __name__ == "__main__":
    asyncio.run(main())
