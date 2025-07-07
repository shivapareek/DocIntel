from functools import lru_cache
from transformers import pipeline
import torch


def _auto_device() -> int:
    try:
        if torch.cuda.is_available():
            return 0
    except Exception:
        pass
    return -1


@lru_cache(maxsize=1)
def _get_summarizer():
    return pipeline(
        "summarization",
        model="sshleifer/distilbart-cnn-12-6",
        device=_auto_device(), 
    )


def generate_summary(
    text: str,
    max_tokens: int = 190,
    min_tokens: int = 140,
) -> str:
   
    text = text.strip()
    if not text:
        return ""

    text = text.replace("\n", " ")[:2000]  

    summarizer = _get_summarizer()
    result = summarizer(
        text,
        max_length=max_tokens,
        min_length=min_tokens,
        do_sample=False,
    )
    return result[0]["summary_text"].strip()
