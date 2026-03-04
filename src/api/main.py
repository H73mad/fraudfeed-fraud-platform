import json
import math
import re
from ipaddress import ip_address
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from src.config import METRICS_PATH, MODEL_PATH, PROJECT_ROOT

app = FastAPI(title="Fraud Risk Scoring API", version="0.1.0")
STATIC_DIR = PROJECT_ROOT / "src" / "api" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_model_cache = None


class TransactionRequest(BaseModel):
    amount: float = Field(gt=0)
    channel: str = Field(pattern="^(web|mobile|pos)$")
    card_present: int = Field(ge=0, le=1)
    hour: int = Field(ge=0, le=23)


class ScoreResponse(BaseModel):
    fraud_probability: float
    fraud_label: int
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    threshold: float
    reasons: list[str]


class BatchTransactionRequest(BaseModel):
    transactions: list[TransactionRequest] = Field(min_length=1, max_length=200)
    threshold: float = Field(default=0.5, ge=0.1, le=0.95)


class BatchScoreResponse(BaseModel):
    total_transactions: int
    flagged_transactions: int
    results: list[ScoreResponse]


class UrlCheckRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


class CheckResponse(BaseModel):
    fraud_probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reasons: list[str]


def _to_features(payload: TransactionRequest) -> pd.DataFrame:
    base = {
        "amount": float(payload.amount),
        "card_present": float(payload.card_present),
        "hour": float(payload.hour),
        "is_night": float(1 if payload.hour <= 5 or payload.hour >= 23 else 0),
        "channel_mobile": 0.0,
        "channel_pos": 0.0,
        "channel_web": 0.0,
    }
    base[f"channel_{payload.channel}"] = 1.0
    return pd.DataFrame([base])


def _get_model():
    global _model_cache
    if _model_cache is None:
        if not Path(MODEL_PATH).exists():
            return None
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def _risk_level(probability: float, threshold: float) -> str:
    if probability >= max(0.8, threshold):
        return "HIGH"
    if probability >= max(0.5, threshold * 0.85):
        return "MEDIUM"
    return "LOW"


def _risk_level_from_prob(probability: float) -> str:
    if probability >= 0.8:
        return "HIGH"
    if probability >= 0.5:
        return "MEDIUM"
    return "LOW"


def _reason_codes(payload: TransactionRequest) -> list[str]:
    reasons = []
    if payload.amount >= 200:
        reasons.append("High transaction amount")
    if payload.card_present == 0:
        reasons.append("Card not present")
    if payload.hour <= 5 or payload.hour >= 23:
        reasons.append("Transaction at unusual hour")
    if payload.channel == "web":
        reasons.append("Web channel has elevated risk")

    return reasons[:3] if reasons else ["No strong risk signals"]


def _score(payload: TransactionRequest, threshold: float = 0.5) -> ScoreResponse:
    model = _get_model()
    if model is None:
        score = 0.08
        if payload.amount >= 200:
            score += 0.28
        if payload.card_present == 0:
            score += 0.2
        if payload.hour <= 5 or payload.hour >= 23:
            score += 0.18
        if payload.channel == "web":
            score += 0.1
        fraud_probability = max(0.01, min(score, 0.99))
    else:
        features = _to_features(payload)
        fraud_probability = float(model.predict_proba(features)[0, 1])

    fraud_label = int(fraud_probability >= threshold)
    return ScoreResponse(
        fraud_probability=fraud_probability,
        fraud_label=fraud_label,
        risk_level=_risk_level(fraud_probability, threshold),
        threshold=threshold,
        reasons=_reason_codes(payload),
    )


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _byte_entropy(content: bytes) -> float:
    if not content:
        return 0.0
    frequencies = [0] * 256
    for value in content:
        frequencies[value] += 1
    entropy = 0.0
    length = len(content)
    for count in frequencies:
        probability = _safe_div(count, length)
        if probability > 0:
            entropy -= probability * math.log2(probability)
    return entropy


def _url_fraud_probability(raw_url: str) -> tuple[float, list[str]]:
    reasons = []
    score = 0.05
    url_text = raw_url.strip()

    try:
        parsed = urlparse(url_text)
    except Exception:
        return 0.95, ["Malformed URL structure"]

    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").lower()

    if parsed.scheme != "https":
        score += 0.16
        reasons.append("URL does not use HTTPS")

    if "@" in url_text:
        score += 0.18
        reasons.append("Contains '@' redirection pattern")

    if len(url_text) >= 90:
        score += 0.12
        reasons.append("Unusually long URL")

    suspicious_keywords = ["verify", "login", "reset", "wallet", "secure", "update", "account"]
    keyword_hits = [keyword for keyword in suspicious_keywords if keyword in path]
    if keyword_hits:
        score += min(0.2, 0.04 * len(keyword_hits))
        reasons.append("Sensitive keyword pattern in URL path")

    if re.search(r"xn--", host):
        score += 0.18
        reasons.append("Possible punycode homograph domain")

    if host.count("-") >= 3:
        score += 0.08
        reasons.append("Domain has many hyphens")

    try:
        ip_address(host)
        score += 0.2
        reasons.append("Host uses raw IP address")
    except ValueError:
        pass

    if host.count(".") >= 4:
        score += 0.09
        reasons.append("Excessive subdomain depth")

    top_domains = ["google.com", "microsoft.com", "amazon.com", "apple.com", "paypal.com"]
    if any(domain in host for domain in top_domains) and host not in top_domains:
        score += 0.1
        reasons.append("Domain resembles trusted brand")

    probability = max(0.01, min(score, 0.99))
    if not reasons:
        reasons.append("No strong phishing indicators detected")

    return probability, reasons[:4]


def _file_fraud_probability(filename: str, content: bytes) -> tuple[float, list[str]]:
    reasons = []
    score = 0.05
    name = filename.lower()
    extension = Path(name).suffix

    suspicious_extensions = {".exe", ".dll", ".scr", ".bat", ".cmd", ".js", ".vbs", ".ps1", ".jar"}
    if extension in suspicious_extensions:
        score += 0.3
        reasons.append(f"Executable/script extension detected ({extension})")

    if ".pdf.exe" in name or ".docx.exe" in name or ".jpg.exe" in name:
        score += 0.3
        reasons.append("Double-extension disguise pattern detected")

    size = len(content)
    if size == 0:
        score += 0.3
        reasons.append("Empty file payload")
    elif size > 15 * 1024 * 1024:
        score += 0.08
        reasons.append("Unusually large upload")

    entropy = _byte_entropy(content[:200000])
    if entropy > 7.4:
        score += 0.18
        reasons.append("High entropy content (packed/encrypted pattern)")

    suspicious_markers = [b"powershell", b"cmd.exe", b"wscript", b"downloadstring", b"base64,"]
    lower_content = content[:200000].lower()
    marker_hits = sum(marker in lower_content for marker in suspicious_markers)
    if marker_hits > 0:
        score += min(0.22, 0.06 * marker_hits)
        reasons.append("Suspicious script markers found")

    probability = max(0.01, min(score, 0.99))
    if not reasons:
        reasons.append("No high-risk file indicators detected")

    return probability, reasons[:4]


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_exists": Path(MODEL_PATH).exists()}


@app.get("/metrics")
def metrics() -> dict:
    if not Path(METRICS_PATH).exists():
        raise HTTPException(status_code=404, detail="Metrics not found. Train model first.")
    return json.loads(Path(METRICS_PATH).read_text(encoding="utf-8"))


@app.post("/score", response_model=ScoreResponse)
def score_transaction(payload: TransactionRequest) -> ScoreResponse:
    return _score(payload, threshold=0.5)


@app.post("/score/batch", response_model=BatchScoreResponse)
def score_batch(payload: BatchTransactionRequest) -> BatchScoreResponse:
    results = [_score(transaction, threshold=payload.threshold) for transaction in payload.transactions]
    flagged_transactions = sum(result.fraud_label for result in results)
    return BatchScoreResponse(
        total_transactions=len(results),
        flagged_transactions=flagged_transactions,
        results=results,
    )


@app.post("/check/url", response_model=CheckResponse)
def check_url(payload: UrlCheckRequest) -> CheckResponse:
    probability, reasons = _url_fraud_probability(payload.url)
    return CheckResponse(
        fraud_probability=probability,
        risk_level=_risk_level_from_prob(probability),
        reasons=reasons,
    )


@app.post("/check/file", response_model=CheckResponse)
async def check_file(file: UploadFile = File(...)) -> CheckResponse:
    content = await file.read()
    probability, reasons = _file_fraud_probability(file.filename or "uploaded_file", content)
    return CheckResponse(
        fraud_probability=probability,
        risk_level=_risk_level_from_prob(probability),
        reasons=reasons,
    )
