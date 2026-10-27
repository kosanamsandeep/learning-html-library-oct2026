#askit_embeddings_from_interactions


from __future__ import annotations

import json
import logging
import uuid
from datetime import timedelta
import pendulum
import requests
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


# -------------------------------
# CONFIG (Airflow Variables)
# -------------------------------
TOKEN_URL = Variable.get("TOKEN_URL")
API_URL = Variable.get("API_URL")

CLIENT_ID = Variable.get("client_id")
CLIENT_SECRET = Variable.get("client_secret")


default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}


# -------------------------------
# COMMON FUNCTIONS
# -------------------------------
def get_access_token(**kwargs):
    logger.info("Requesting access token from TOKEN_URL=%s", TOKEN_URL)
    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=60,
    )

    if response.status_code != 200:
        logger.error(
            "Token API failed with status=%s body=%s",
            response.status_code,
            response.text[:1000],
        )
        raise RuntimeError(f"Token API failed: {response.text}")

    token = response.json().get("access_token")
    if not token:
        raise ValueError("Token not received")

    kwargs["ti"].xcom_push(key="token", value=token)
    logger.info("Token fetched successfully and pushed to XCom")
    print("Token fetched")


def _get_embedding_service_url() -> str:
    return Variable.get("askit_canvasai_embedding_svc_url")


def _load_json_config(**kwargs):
    """Load local embedding configuration from Airflow Variables."""
    ti = kwargs.get("ti")
    if ti is None:
        raise RuntimeError("Airflow context missing `ti` (task instance).")

    cfg_raw = Variable.get("askit_embeddings_config_interactions")
    logger.info(
        "Loading local embedding config from Airflow Variable askit_embeddings_config_interactions"
    )
    try:
        cfg = json.loads(cfg_raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Airflow Variable `askit_embeddings_config_interactions` must contain valid JSON content."
        ) from exc

    for key in ("spaceId", "flowId", "spaceName", "userName", "userRole"):
        if key not in cfg:
            raise ValueError(f"Missing required config key: {key}")

    cfg.setdefault("isFromDatahub", True)
    cfg.setdefault("vectorStorageType", "ChromaDB")
    cfg.setdefault("clearEmbeding", False)
    cfg.setdefault("clearIndexing", False)
    cfg.setdefault("runEmbedding", True)
    cfg.setdefault("runIndexing", False)
    cfg.setdefault("requestUrl", _get_embedding_service_url())
    cfg.setdefault("correlationId", str(uuid.uuid4()))

    ti.xcom_push(key="run_config", value=cfg)
    logger.info(
        "Local embedding config loaded and pushed to XCom with spaceId=%s flowId=%s spaceName=%s runEmbedding=%s runIndexing=%s requestUrl=%s",
        cfg["spaceId"],
        cfg["flowId"],
        cfg["spaceName"],
        cfg["runEmbedding"],
        cfg["runIndexing"],
        cfg["requestUrl"],
    )


def _validate_core_service(**kwargs):
    ti = kwargs.get("ti")
    if ti is None:
        raise RuntimeError("Airflow context missing `ti` (task instance).")

    cfg = ti.xcom_pull(key="run_config", task_ids="load_json_config")
    if not isinstance(cfg, dict):
        raise RuntimeError(
            "Missing XCom `run_config` from task `load_json_config` (got None)."
        )

    core_url = Variable.get("canvasai_core_svc_url")
    headers = {
        "Content-Type": "application/json",
        "Correlation-Id": cfg["correlationId"],
    }

    response = requests.get(core_url.rstrip("/") + "/ping", headers=headers, timeout=30)
    response.raise_for_status()
    logger.info(
        "Core service ping passed: url=%s status=%s correlationId=%s",
        core_url.rstrip("/") + "/ping",
        response.status_code,
        cfg["correlationId"],
    )


def _trigger_local_file_embedding(**kwargs):
    """Trigger the local-file embedding API for already uploaded files."""
    ti = kwargs.get("ti")
    if ti is None:
        raise RuntimeError("Airflow context missing `ti` (task instance).")

    cfg = ti.xcom_pull(key="run_config", task_ids="load_json_config")
    if not isinstance(cfg, dict):
        raise RuntimeError(
            "Missing XCom `run_config` from task `load_json_config` (got None)."
        )

    logger.info(
        "Preparing local embedding request for spaceId=%s flowId=%s correlationId=%s",
        cfg["spaceId"],
        cfg["flowId"],
        cfg["correlationId"],
    )

    payload = {
        "spaceId": cfg["spaceId"],
        "flowId": cfg["flowId"],
        "isFromDatahub": cfg["isFromDatahub"],
        "vectorStorageType": cfg["vectorStorageType"],
        "userName": cfg["userName"],
        "userRole": cfg["userRole"],
        "spaceName": cfg["spaceName"],
        "clearEmbeding": cfg["clearEmbeding"],
        "clearIndexing": cfg["clearIndexing"],
        "runEmbedding": cfg["runEmbedding"],
        "runIndexing": cfg["runIndexing"],
    }

    token = ti.xcom_pull(task_ids="get_token", key="token")
    if not token:
        raise ValueError("Token not found in XCom from task `get_token`")
    request_url = cfg.get("requestUrl") or _get_embedding_service_url()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Correlation-Id": cfg["correlationId"],
    }

    logger.info(
        "Triggering interactions embedding via url=%s payload=%s token_prefix=%s",
        request_url,
        json.dumps(payload),
        token[:12],
    )

    # Fire-and-forget to avoid gateway timeouts on long backend processing.
    connect_timeout_s = 10
    read_timeout_s = 10

    try:
        response = requests.post(
            request_url,
            json=payload,
            headers=headers,
            timeout=(connect_timeout_s, read_timeout_s),
        )
    except requests.exceptions.ReadTimeout:
        logger.exception(
            "Embedding request did not respond within %ss (read-timeout). "
            "Assuming it was accepted and is running in the backend. correlationId=%s url=%s",
            read_timeout_s,
            cfg["correlationId"],
            request_url,
        )
        ti.xcom_push(key="embedding_submit_mode", value="fire_and_forget_timeout")
        ti.xcom_push(key="correlation_id", value=cfg["correlationId"])
        return
    except requests.exceptions.ConnectTimeout:
        logger.exception(
            "Failed to connect to embedding service within %ss. correlationId=%s url=%s",
            connect_timeout_s,
            cfg["correlationId"],
            request_url,
        )
        raise
    except requests.exceptions.ConnectionError:
        logger.exception(
            "Connection error while submitting embedding request. correlationId=%s url=%s",
            cfg["correlationId"],
            request_url,
        )
        raise

    try:
        response.raise_for_status()
    except Exception:
        logger.exception(
            "Interactions embedding trigger failed: status=%s body=%s",
            response.status_code,
            response.text[:1000],
        )
        raise

    try:
        response_body = response.json()
    except ValueError:
        logger.exception(
            "Failed to parse embedding service response as JSON: status=%s body=%s",
            response.status_code,
            response.text[:1000],
        )
        response_body = {}

    logger.info(
        "Interactions embedding trigger succeeded: status=%s response=%s dag_run_id=%s",
        response.status_code,
        response.text[:1000],
        response_body.get("dag_run_id"),
    )
    if response_body.get("dag_run_id"):
        ti.xcom_push(key="triggered_dag_run_id", value=response_body["dag_run_id"])

    ti.xcom_push(key="embedding_submit_mode", value="waited_for_response")
    ti.xcom_push(key="correlation_id", value=cfg["correlationId"])


with DAG(
    dag_id="askit_embeddings_from_interactions",
    # Run daily at 4:00 AM America/New_York (EDT/EST with DST handled by Airflow).
    schedule_interval="0 4 * * *",
    start_date=pendulum.datetime(2023, 1, 1, tz="America/New_York"),
    catchup=False,
    default_args=default_args,
    tags=["embeddings", "local-files", "askit"],
) as dag:
    load_json_config = PythonOperator(
        task_id="load_json_config",
        python_callable=_load_json_config,
        provide_context=True,
    )

    validate_core_service = PythonOperator(
        task_id="validate_core_service",
        python_callable=_validate_core_service,
        provide_context=True,
    )

    get_token = PythonOperator(
        task_id="get_token",
        python_callable=get_access_token,
    )

    trigger_local_file_embedding = PythonOperator(
        task_id="trigger_local_file_embedding",
        python_callable=_trigger_local_file_embedding,
        provide_context=True,
    )

    load_json_config >> validate_core_service >> get_token >> trigger_local_file_embedding