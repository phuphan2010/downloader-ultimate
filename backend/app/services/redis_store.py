"""Redis storage client for API keys and Jobs persistent state."""
import json
from typing import Dict, List, Optional
import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get active Redis client instance with fallback to None."""
    global _redis_client
    if _redis_client is None:
        try:
            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, decode_responses=True)
            r.ping()
            _redis_client = r
        except Exception as e:
            logger.warning("redis_connect_failed_using_memory_fallback", error=str(e))
            _redis_client = None
    return _redis_client


class RedisStore:
    """Redis KV store for jobs and API keys with in-memory fallback."""

    def __init__(self):
        self.memory_jobs: Dict[str, Dict] = {}
        self.memory_keys: Dict[str, Dict] = {}

    def save_job(self, job_id: str, job_data: Dict) -> None:
        r = get_redis_client()
        if r:
            try:
                r.set(f"job:{job_id}", json.dumps(job_data))
                r.sadd("jobs_index", job_id)
                return
            except Exception as e:
                logger.error("redis_save_job_failed", job_id=job_id, error=str(e))
        self.memory_jobs[job_id] = job_data

    def get_job(self, job_id: str) -> Optional[Dict]:
        r = get_redis_client()
        if r:
            try:
                data = r.get(f"job:{job_id}")
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.error("redis_get_job_failed", job_id=job_id, error=str(e))
        return self.memory_jobs.get(job_id)

    def list_jobs(self, api_key: Optional[str] = None) -> List[Dict]:
        r = get_redis_client()
        jobs = []
        if r:
            try:
                job_ids = r.smembers("jobs_index")
                for jid in job_ids:
                    jdata = r.get(f"job:{jid}")
                    if jdata:
                        job_obj = json.loads(jdata)
                        if api_key is None or job_obj.get("api_key") == api_key:
                            jobs.append(job_obj)
                return jobs
            except Exception as e:
                logger.error("redis_list_jobs_failed", error=str(e))

        for jdata in self.memory_jobs.values():
            if api_key is None or jdata.get("api_key") == api_key:
                jobs.append(jdata)
        return jobs

    def save_api_key(self, hashed_key: str, key_data: Dict) -> None:
        r = get_redis_client()
        if r:
            try:
                r.set(f"apikey:{hashed_key}", json.dumps(key_data))
                r.sadd("apikeys_index", hashed_key)
                return
            except Exception as e:
                logger.error("redis_save_key_failed", error=str(e))
        self.memory_keys[hashed_key] = key_data

    def get_all_api_keys(self) -> Dict[str, Dict]:
        r = get_redis_client()
        keys_dict = {}
        if r:
            try:
                hashed_keys = r.smembers("apikeys_index")
                for hk in hashed_keys:
                    data = r.get(f"apikey:{hk}")
                    if data:
                        keys_dict[hk] = json.loads(data)
                return keys_dict
            except Exception as e:
                logger.error("redis_get_keys_failed", error=str(e))

        return self.memory_keys

    def check_rate_limit(self, identifier: str, limit: int = 10, window_sec: int = 60) -> bool:
        """Check sliding window rate limit for an identifier (API Key / IP)."""
        import time
        r = get_redis_client()
        if r:
            try:
                key = f"ratelimit:{identifier}:{int(time.time() // window_sec)}"
                current = r.incr(key)
                if current == 1:
                    r.expire(key, window_sec)
                return current <= limit
            except Exception as e:
                logger.error("redis_rate_limit_failed", error=str(e))
                return True
        return True


redis_store = RedisStore()
