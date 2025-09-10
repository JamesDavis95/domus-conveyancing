import sys
import logging
from redis import Redis
from rq import Worker, Queue
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("worker")

redis = Redis.from_url(settings.REDIS_URL)
queue = Queue("default", connection=redis)

if __name__ == "__main__":
    logger.info("Starting RQ worker, listening on 'default' queue")
    worker = Worker([queue], connection=redis)
    worker.work()
