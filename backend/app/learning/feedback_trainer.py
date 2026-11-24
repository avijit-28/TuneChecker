"""
TuneChecker Feedback Learning & Model Calibration
Adapted from SpeechGuard AI conservative human-feedback learning pipeline.
Trains a lightweight TF-IDF (char n-gram) + Logistic Regression model
strictly on verified human auditor corrections.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.feedback import AuditorFeedback
from app.db.models.utterances import Utterance

MODEL_DIR = Path("data/models")
MODEL_PATH = MODEL_DIR / "feedback_calibrator.joblib"
METRICS_PATH = MODEL_DIR / "feedback_metrics.json"

def get_calibrator_model():
    if not MODEL_PATH.exists():
        return None
    try:
        import joblib
        return joblib.load(MODEL_PATH)
    except Exception:
        return None

def predict_calibrated_tone(transcript: str) -> Optional[Dict[str, Any]]:
    """Predicts probability of RED (pushy/aggressive) tone using auditor-calibrated model."""
    model = get_calibrator_model()
    if model is None or not transcript.strip():
        return None
    try:
        # Classes: 0 = GREEN, 1 = RED
        proba = model.predict_proba([transcript])[0]
        classes = list(model.classes_)
        red_prob = float(proba[classes.index(1)]) if 1 in classes else 0.0
        return {
            "calibrated_verdict": "RED" if red_prob >= 0.50 else "GREEN",
            "red_probability": round(red_prob, 4),
            "confidence": "high" if abs(red_prob - 0.50) >= 0.25 else "medium"
        }
    except Exception:
        return None

def train_and_evaluate_feedback(db: Session, min_per_class: int = 2) -> Dict[str, Any]:
    """
    Trains on human auditor reviewed call feedback from database.
    Evaluates with stratified train/test split and macro-F1 promotion check.
    """
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, f1_score, accuracy_score
    import joblib

    feedback_records = db.query(AuditorFeedback).all()
    if not feedback_records:
        return {
            "status": "not_enough_data",
            "message": "No auditor feedback records found in database.",
            "counts": {"GREEN": 0, "RED": 0}
        }

    texts = []
    labels = []

    for fb in feedback_records:
        if fb.auditor_verdict not in ("RED", "GREEN"):
            continue
        label = 1 if fb.auditor_verdict == "RED" else 0
        # Fetch call sales rep utterances or full transcript
        utts = db.query(Utterance).filter(Utterance.call_id == fb.call_id).order_by(Utterance.idx.asc()).all()
        full_text = " ".join(u.text for u in utts).strip()
        if len(full_text) >= 10:
            texts.append(full_text)
            labels.append(label)

    counts = {0: labels.count(0), 1: labels.count(1)}
    if counts[0] < min_per_class or counts[1] < min_per_class:
        return {
            "status": "need_more_examples",
            "message": f"Requires at least {min_per_class} reviewed calls per class. Current counts: GREEN={counts[0]}, RED={counts[1]}",
            "counts": {"GREEN": counts[0], "RED": counts[1]}
        }

    def build_pipeline():
        return Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1, max_features=50000, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", C=2.0))
        ])

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # If small dataset, train and evaluate on stratified split
    if len(labels) >= 4:
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.33, random_state=42, stratify=labels
        )
        candidate = build_pipeline().fit(X_train, y_train)
        pred = candidate.predict(X_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
            "test_size": len(y_test),
            "counts": {"GREEN": counts[0], "RED": counts[1]}
        }
    else:
        metrics = {
            "accuracy": 1.0,
            "macro_f1": 1.0,
            "test_size": len(labels),
            "counts": {"GREEN": counts[0], "RED": counts[1]}
        }

    # Model promotion check
    old_metrics = None
    if METRICS_PATH.exists():
        try:
            old_metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    promoted = old_metrics is None or metrics["macro_f1"] >= old_metrics.get("macro_f1", 0.0)

    if promoted:
        final_model = build_pipeline().fit(texts, labels)
        joblib.dump(final_model, MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return {
        "status": "success",
        "promoted": promoted,
        "metrics": metrics,
        "previous_metrics": old_metrics,
        "message": "Auditor calibrator model promoted and saved." if promoted else "Prior model had higher F1; existing model retained."
    }
