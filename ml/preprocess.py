"""
preprocess.py
-------------
NLP text-normalization utilities shared by the training scripts and the
Flask inference app, so that training-time and inference-time preprocessing
always stay perfectly in sync.
"""

import re

URL_PATTERN = re.compile(r"http[s]?://\S+|www\.\S+")
EMAIL_PATTERN = re.compile(r"\S+@\S+")
NON_ALPHA_PATTERN = re.compile(r"[^a-zA-Z\s]")
MULTISPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Normalize raw input text before vectorization:
      1. Lowercase
      2. Replace URLs with a generic <url> token (presence of a link is itself
         a strong signal, so we keep a token rather than deleting it outright)
      3. Replace emails with a generic <email> token
      4. Strip punctuation / digits / special characters
      5. Collapse repeated whitespace
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = URL_PATTERN.sub(" urltoken ", text)
    text = EMAIL_PATTERN.sub(" emailtoken ", text)
    text = NON_ALPHA_PATTERN.sub(" ", text)
    text = MULTISPACE_PATTERN.sub(" ", text).strip()
    return text
