import logging
from concurrent.futures import ThreadPoolExecutor
from app.config import settings
from app.pipeline.orchestrator import run_pipeline_for_call

logger = logging.getLogger(__name__)

# Single thread pool executor to enforce MAX_CONCURRENT_JOBS limit
_executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_JOBS, thread_name_prefix="pipeline_worker")

def queue_call_processing(call_id: str, start_stage: str = "validation"):
    logger.info(f"Queuing call {call_id} for processing starting at {start_stage}")
    _executor.submit(run_pipeline_for_call, call_id, start_stage)
