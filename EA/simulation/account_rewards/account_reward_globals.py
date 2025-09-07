_account_reward_cache_version = 0
def get_account_reward_cache_version():
    return _account_reward_cache_version

def increment_account_reward_cache_version():
    global _account_reward_cache_version
    _account_reward_cache_version += 1
