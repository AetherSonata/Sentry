import asyncio
from collections import defaultdict
from actions.token_init import initialize_token_environment

class TokenTaskManager:
    def __init__(self):
        # Dictionary: user_id -> {token: task}
        self.tasks = defaultdict(dict)

    async def add_token(self, user_id, testing_mode, token, wallet):
        """Start monitoring a token for a user."""
        if token in self.tasks[user_id]:
            print(f"Token {token} already monitored for user {user_id}")
            return
        
        # Create a task for this token
        task = asyncio.create_task(initialize_token_environment(testing_mode, token, wallet))
        self.tasks[user_id][token] = task
        print(f"Started monitoring {token} for user {user_id}")

    async def remove_token(self, user_id, token):
        """Stop monitoring a token for a user."""
        if token not in self.tasks[user_id]:
            print(f"Token {token} not monitored for user {user_id}")
            return
        
        task = self.tasks[user_id].pop(token)
        task.cancel()
        try:
            await task  # Wait for cancellation
        except asyncio.CancelledError:
            print(f"Stopped monitoring {token} for user {user_id}")

    async def shutdown(self, user_id):
        """Stop all tasks for a user."""
        for token, task in self.tasks[user_id].items():
            task.cancel()
        await asyncio.gather(*self.tasks[user_id].values(), return_exceptions=True)
        self.tasks[user_id].clear()
        print(f"Shutdown monitoring for user {user_id}")