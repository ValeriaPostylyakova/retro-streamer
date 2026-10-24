class RedisKeyManager:
    @staticmethod
    def game_cache(hash_key: str) -> str:
        return f"game:render:cache:{hash_key}"

    @staticmethod
    def task_owner(task_id: str) -> str:
        return f"game:task:owner:{task_id}"

    @staticmethod
    def game_render_progress(task_id: str) -> str:
        return f"game:render:progress:{task_id}"
