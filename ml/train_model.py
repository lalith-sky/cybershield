"""
train_model.py
---------------
Trains a TF-IDF + Logistic Regression classifier for either:
  - Fake Job Offer Detection   (dataset: data/job_scam_dataset.csv)
  - Phishing Email Detection   (dataset: data/phishing_email_dataset.csv)

Usage:
    python train_model.py job
    python train_model.py phishing
"""

import sys
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.preprocess import clean_text

CONFIGS = {
    "job": {
        "dataset": "../data/job_scam_dataset.csv",
        "model_out": "../models/job_scam_model.pkl",
        "vectorizer_out": "../models/job_scam_vectorizer.pkl",
        "metrics_out": "../models/job_scam_metrics.json",
        "positive_label_name": "Fraudulent Job Offer",
        "negative_label_name": "Genuine Job Offer",
    },
    "phishing": {
        "dataset": "../data/phishing_email_dataset.csv",
        "model_out": "../models/phishing_model.pkl",
        "vectorizer_out": "../models/phishing_vectorizer.pkl",
        "metrics_out": "../models/phishing_metrics.json",
        "positive_label_name": "Phishing Email",
        "negative_label_name": "Legitimate Email",
    },
}


def train(task: str):
    cfg = CONFIGS[task]
    print(f"\n=== Training model: {task} ===")

    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    df = pd.read_csv(cfg["dataset"])
    df["clean_text"] = df["text"].apply(clean_text)

    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"]
    )

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=5.0,
    )
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    # 5-fold CV on the full pipeline (vectorizer refit per fold -> no leakage)
    pipe = make_pipeline(
        TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced", C=5.0))
    cv = cross_val_score(pipe, df["clean_text"], df["label"], cv=5, scoring="f1")

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "f1_score": round(f1_score(y_test, y_pred), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "positive_label_name": cfg["positive_label_name"],
        "negative_label_name": cfg["negative_label_name"],
        "cv_f1_mean": None, "cv_f1_std": None,
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }

    metrics["cv_f1_mean"] = round(float(cv.mean()), 4)
    metrics["cv_f1_std"] = round(float(cv.std()), 4)
    print(classification_report(y_test, y_pred,
                                 target_names=[cfg["negative_label_name"], cfg["positive_label_name"]]))
    print("Metrics:", json.dumps(metrics, indent=2))

    joblib.dump(model, cfg["model_out"])
    joblib.dump(vectorizer, cfg["vectorizer_out"])
    with open(cfg["metrics_out"], "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved model -> {cfg['model_out']}")
    print(f"Saved vectorizer -> {cfg['vectorizer_out']}")
    print(f"Saved metrics -> {cfg['metrics_out']}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CONFIGS:
        print("Usage: python train_model.py [job|phishing]")
        sys.exit(1)
    train(sys.argv[1])
