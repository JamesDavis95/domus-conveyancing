import os
from rq import Worker, Queue
from redis import Redis

# Ensure job functions are importable (e.g., in jobs.py)
try:
    import jobs  # noqa: F401
except Exception:
    # Optional: provide a tiny fallback job for sanity checks
    def echo(x): return x

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
QUEUE_NAME = os.getenv("RQ_QUEUE", "default")

def main():
    conn = Redis.from_url(REDIS_URL)
    # pass connection explicitly; works across RQ 1.x/2.x
    q = Queue(QUEUE_NAME, connection=conn)
    w = Worker([q], connection=conn)
    w.work(with_scheduler=True)

if __name__ == "__main__":
    main()
