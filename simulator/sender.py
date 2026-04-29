import time
import logging
import requests

logger = logging.getLogger(__name__)

GRAPHQL_URL = "http://localhost:8001/graphql/"
BATCH_SIZE = 10
MAX_RETRIES = 3

BATCH_MUTATION = """
mutation IngestBatch($inputs: [TelemetryInput!]!) {
    ingestBatchTelemetry(inputs: $inputs) {
        success
        created
        message
    }
}
"""

def send_batch(readings: list[dict], retries: int = 0) -> dict | None:
    try:
        resp = requests.post(
            GRAPHQL_URL,
            json={"query": BATCH_MUTATION, "variables": {"inputs": readings}},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise ValueError(data["errors"])
        return data["data"]["ingestBatchTelemetry"]
    except Exception as e:
        if retries < MAX_RETRIES:
            wait = 2 ** retries
            logger.warning(f"Send failed ({e}), retrying in {wait}s...")
            time.sleep(wait)
            return send_batch(readings, retries + 1)
        logger.error(f"Batch failed after {MAX_RETRIES} retries: {e}")
        return None