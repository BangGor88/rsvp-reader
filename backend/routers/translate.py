import os
import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.llm_service import get_model

router = APIRouter(prefix="/translate", tags=["translate"])

LANGUAGE_MAP = {
    "English": "English",
    "German": "German",
    "French": "French",
    "Spanish": "Spanish",
    "Chinese": "Mandarin Chinese",
    "Japanese": "Japanese",
    "Swedish": "Swedish",
    "Indonesian": "Indonesian",
}

CHUNK_WORDS = int(os.getenv("LLAMA_CHUNK_WORDS", "300"))

# BCP-47 codes for translategemma's structured chat format.
LANGUAGE_CODE_MAP = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Mandarin Chinese": "zh",
    "Japanese": "ja",
    "Swedish": "sv",
    "Indonesian": "id",
}

# Source language code for translategemma.  Override via env var if needed.
_SOURCE_LANG = os.getenv("TRANSLATE_SOURCE_LANG", "")


def _detect_source_lang(text: str) -> str:
    """Heuristic BCP-47 source language detection from character frequency."""
    if _SOURCE_LANG:
        return _SOURCE_LANG
    # Swedish-specific: å is extremely rare outside Nordic languages.
    if re.search(r"[åÅ]", text):
        return "sv"
    if re.search(r"[äÄöÖüÜß]", text):
        return "de"
    if re.search(r"[àâçéèêëîïôùûÿæœ]", text, re.IGNORECASE):
        return "fr"
    if re.search(r"[áéíóúüñ¿¡]", text, re.IGNORECASE):
        return "es"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    return "en"


class TranslateRequest(BaseModel):
    text: str
    target_language: str
    focus_word: str | None = None
    focus_word_index: int | None = Field(default=None, ge=0)
    highlight_focus: bool = False


def _inject_focus_markers(text: str, start: int, end: int) -> str:
    return f"{text[:start]}[[[{text[start:end]}]]]{text[end:]}"


def _strip_focus_markers(text: str) -> str:
    return text.replace("[[[", "").replace("]]]", "").replace("[[", "").replace("]]", "")


def _find_candidate_match(text: str, token: str, occurrence_index: int) -> re.Match[str] | None:
    matches = list(re.finditer(re.escape(token), text, flags=re.IGNORECASE))
    if not matches:
        return None

    # If the translated sentence has fewer repeated tokens than expected,
    # use the closest available occurrence instead of failing highlight.
    bounded_index = min(occurrence_index, len(matches) - 1)
    return matches[bounded_index]


def _find_first_candidate_match(text: str, token: str) -> re.Match[str] | None:
    return _find_candidate_match(text, token, 0)


def _is_trailing_match(text: str, match: re.Match[str]) -> bool:
    return not text[match.end() :].strip()


def _levenshtein_distance(left: str, right: str) -> int:
    left = left.lower()
    right = right.lower()
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            replace_cost = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def _find_best_token_match(text: str, focus_word: str, allow_trailing_exact: bool = False) -> re.Match[str] | None:
    focus_lower = focus_word.lower()
    best_match: re.Match[str] | None = None
    best_score: tuple[int, int, int] | None = None

    for match in re.finditer(r"\b[\w'-]+\b", text, flags=re.UNICODE):
        token = match.group(0)
        token_lower = token.lower()
        if not token_lower:
            continue

        is_exact = token_lower == focus_lower
        is_trailing = _is_trailing_match(text, match)
        if is_exact and is_trailing and not allow_trailing_exact:
            continue

        score = (
            _levenshtein_distance(token_lower, focus_lower),
            1 if is_trailing else 0,
            match.start(),
        )
        if best_score is None or score < best_score:
            best_score = score
            best_match = match

    if best_match is None:
        return None

    max_distance = max(3, len(focus_lower) // 2)
    if best_score is not None and best_score[0] > max_distance:
        return None

    if not allow_trailing_exact and best_match.group(0).lower() == focus_lower and _is_trailing_match(text, best_match):
        return None

    return best_match


def _find_best_token_span(text: str, focus_word: str) -> re.Match[str] | None:
    focus_lower = focus_word.lower()
    exact_spans: list[re.Match[str]] = []
    loose_spans: list[re.Match[str]] = []

    for match in re.finditer(r"\b[\w'-]+\b", text, flags=re.UNICODE):
        token = match.group(0)
        token_lower = token.lower()
        if token_lower == focus_lower:
            exact_spans.append(match)
        elif focus_lower in token_lower:
            loose_spans.append(match)

    if loose_spans:
        return loose_spans[0]
    if exact_spans:
        return exact_spans[0]
    return None


def _find_position_token_match(
    source_chunk: str,
    translated: str,
    focus_word_index: int,
) -> re.Match[str] | None:
    translated_tokens = list(re.finditer(r"\b[\w'-]+\b", translated, flags=re.UNICODE))
    if not translated_tokens:
        return None

    source_tokens = list(re.finditer(r"\b[\w'-]+\b", source_chunk, flags=re.UNICODE))
    if not source_tokens:
        bounded = min(max(0, focus_word_index), len(translated_tokens) - 1)
        return translated_tokens[bounded]

    source_last_index = max(0, len(source_tokens) - 1)
    target_last_index = len(translated_tokens) - 1

    if source_last_index == 0:
        target_index = 0
    else:
        bounded_focus_index = min(max(0, focus_word_index), source_last_index)
        relative_position = bounded_focus_index / source_last_index
        target_index = int(relative_position * target_last_index)

    return translated_tokens[target_index]


def _strip_trailing_focus_word(text: str, focus_word: str) -> str:
    matches = list(re.finditer(r"\b[\w'-]+\b", text, flags=re.UNICODE))
    if len(matches) < 2:
        return text

    last_match = matches[-1]
    if last_match.group(0).lower() != focus_word.lower():
        return text

    prefix = text[: last_match.start()].rstrip()
    suffix = text[last_match.end():].lstrip()
    return f"{prefix}{suffix}"


# Patterns the model sometimes prepends before the actual translation.
_META_PREFIXES = re.compile(
    r"^(the (sentence|text|following)[^:]*:|translation:|here(?: is| are)[^:]*:|translated?[^:]*:)",
    re.IGNORECASE,
)


def _strip_meta_commentary(text: str) -> str:
    """Remove model meta-commentary that precedes the actual translation."""
    cleaned = _META_PREFIXES.sub("", text).strip()
    # Also drop a leading newline the model sometimes emits after stripping.
    return cleaned.lstrip("\n").strip()


def _identify_focus_span(model, source_chunk: str, translated: str, focus_word: str, target: str) -> str:
    """Translate the focus word alone to find its equivalent in the full translation."""
    target_code = LANGUAGE_CODE_MAP.get(target, target[:2].lower())
    source_code = _detect_source_lang(focus_word) or _detect_source_lang(source_chunk)
    completion = model.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_code,
                        "target_lang_code": target_code,
                        "text": focus_word,
                    }
                ],
            }
        ],
        max_tokens=16,
        temperature=0.0,
        repeat_penalty=1.1,
    )
    candidate = completion["choices"][0]["message"]["content"].strip()
    # Take only the first word (model may add punctuation/extra words)
    candidate = candidate.strip('"\'`*').split()[0] if candidate.split() else ""
    return candidate


def _is_reasonable_focus_candidate(candidate: str) -> bool:
    if re.search(r"[.!?;:\n]", candidate):
        return False

    token_matches = list(re.finditer(r"\b[\w'-]+\b", candidate, flags=re.UNICODE))
    if not token_matches:
        return False

    # Alignment helper occasionally returns an entire sentence; keep only short word/phrase candidates.
    return len(token_matches) <= 4


def _parse_translation_alternatives(raw: str, focus_word: str, limit: int = 5) -> list[str]:
    if not raw:
        return []

    cleaned = raw.strip()
    if not cleaned:
        return []

    parts = re.split(r"[,;\n\r]+", cleaned)
    results: list[str] = []
    seen: set[str] = set()

    for part in parts:
        candidate = part.strip()
        candidate = re.sub(r"^[-*\d.)\s]+", "", candidate)
        candidate = candidate.strip("\"'` ")
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if not candidate:
            continue
        if len(candidate) > 48:
            continue

        token_count = len(re.findall(r"\b[\w'-]+\b", candidate, flags=re.UNICODE))
        if token_count == 0 or token_count > 4:
            continue

        normalized = candidate.lower()
        if normalized == focus_word.lower():
            continue
        if normalized in seen:
            continue

        seen.add(normalized)
        results.append(candidate)
        if len(results) >= limit:
            break

    return results


def _suggest_translation_alternatives(
    model,
    source_chunk: str,
    translated_chunk: str,
    focus_word: str,
    target: str,
) -> list[str]:
    # Use raw completion — the translategemma chat template only supports
    # the structured translation format and cannot answer open Q&A.
    prompt = (
        f'"glad" in {target}: happy, joyful, pleased, delighted, cheerful\n'
        f'"{focus_word}" in {target}:'
    )
    completion = model.create_completion(
        prompt=prompt,
        max_tokens=48,
        temperature=0.2,
        repeat_penalty=1.1,
        stop=["\n"],
    )
    raw = completion["choices"][0]["text"].strip()
    return _parse_translation_alternatives(raw, focus_word, limit=5)


def _ensure_focus_highlight(
    model,
    translated: str,
    source_chunk: str,
    target: str,
    focus_word: str,
    focus_word_index: int = 0,
) -> str:
    normalized = _strip_focus_markers(translated).strip()
    if not normalized:
        return translated

    normalized = _strip_trailing_focus_word(normalized, focus_word)
    if not normalized:
        return translated

    # 1. Cheap regex match first — avoids an extra LLM round-trip in most cases.
    span_match = _find_best_token_match(normalized, focus_word)
    if span_match:
        return _inject_focus_markers(normalized, span_match.start(), span_match.end())

    # 2. Direct focus-word lookup (handles cognates / proper nouns unchanged).
    token = focus_word.strip()
    if token:
        match = _find_candidate_match(normalized, token, focus_word_index)
        if match:
            return _inject_focus_markers(normalized, match.start(), match.end())

    # 3. LLM alignment call — only when regex heuristics could not find the span.
    llm_token = _identify_focus_span(model, source_chunk, normalized, focus_word, target)
    if llm_token and _is_reasonable_focus_candidate(llm_token):
        match = _find_candidate_match(normalized, llm_token, focus_word_index)
        if match and not (_is_trailing_match(normalized, match) and llm_token.lower() == focus_word.lower()):
            return _inject_focus_markers(normalized, match.start(), match.end())

    # 4. Position-based fallback.
    position_match = _find_position_token_match(source_chunk, normalized, focus_word_index)
    if position_match:
        return _inject_focus_markers(normalized, position_match.start(), position_match.end())

    return normalized


@lru_cache(maxsize=256)
def _translate_chunk_cached(chunk: str, target: str) -> str:
    """Cached, focus-word-free translation of a text chunk."""
    model = get_model()
    word_count = len(chunk.split())
    max_tokens = max(32, word_count * 4)
    target_code = LANGUAGE_CODE_MAP.get(target, target[:2].lower())
    source_code = _detect_source_lang(chunk)
    completion = model.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "source_lang_code": source_code,
                        "target_lang_code": target_code,
                        "text": chunk,
                    }
                ],
            }
        ],
        max_tokens=max_tokens,
        temperature=0.2,
        repeat_penalty=1.3,
    )
    raw = completion["choices"][0]["message"]["content"].strip()
    return _strip_meta_commentary(raw)


def _translate_chunk(
    model,
    chunk: str,
    target: str,
    focus_word: str | None = None,
    focus_word_index: int | None = None,
    highlight_focus: bool = False,
) -> str:
    # Keep the translation prompt clean of any focus-word instructions.
    # Mentioning the source-language focus word in the prompt causes small
    # models to echo it back untranslated.  Focus highlighting is always
    # resolved afterwards by _ensure_focus_highlight.
    translated = _translate_chunk_cached(chunk, target)
    if highlight_focus and focus_word:
        return _ensure_focus_highlight(
            model,
            translated,
            chunk,
            target,
            focus_word,
            focus_word_index=focus_word_index or 0,
        )
    return translated


@router.post("")
def translate_text(req: TranslateRequest):
    target = LANGUAGE_MAP.get(req.target_language)
    if not target:
        return {"translated": req.text}

    try:
        model = get_model()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    words = req.text.split()
    if not words:
        return {"translated": ""}

    chunks = [
        " ".join(words[i : i + CHUNK_WORDS])
        for i in range(0, len(words), CHUNK_WORDS)
    ]

    translated_parts = [
        _translate_chunk(
            model,
            chunk,
            target,
            focus_word=req.focus_word,
            focus_word_index=req.focus_word_index,
            highlight_focus=req.highlight_focus,
        )
        for chunk in chunks
    ]

    translated_text = " ".join(translated_parts)
    alternatives: list[str] = []
    if req.focus_word and translated_text:
        alternatives = _suggest_translation_alternatives(
            model,
            req.text,
            translated_text,
            req.focus_word,
            target,
        )

    return {
        "translated": translated_text,
        "translation_alternatives": alternatives,
    }
