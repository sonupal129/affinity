import redis, pickle

class RedisClient:

    def __init__(self):
        self.client = redis.Redis(host="localhost", port=6379)

    def get(self, key):
        try:
            return pickle.loads(self.client.get(key))
        except:
            return None

    def set(self, key, value, ttl=None):
        pik = pickle.dumps(value)
        self.client.set(key, pik)
        if ttl:
            self.client.expire(key, ttl)
        return True


client = RedisClient()