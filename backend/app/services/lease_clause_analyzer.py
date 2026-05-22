"""Phase B — voice clause-query transcript ↔ extracted lease-clause cross-validation.

Per the PDF spec for project_22:
    "Natural-language Q&A over lease portfolio; clause comparison engine;
     identifies ambiguous and conflicting terms; generates plain-language
     tenant briefings with talking points."

This service:
- Reads the latest voice clause-query transcript for a lease
- Extracts the topic the asset manager / tenant is asking about
  (e.g. assignment, sublet, CAM, renewal, escalation, default, indemnity)
- Cross-checks each topic against the lease's extracted clauses + OCR text
  of supporting lease documents
- Returns:
    topics            — topics detected in the voice question
    matches           — for each topic, the matching clause(s) + verbatim quote
    conflicts         — clauses that contradict each other (e.g. two different
                        notice windows) or contradict the voice question's
                        stated assumption
    ambiguities       — clauses that lack a specific number / window
    talking_points    — plain-language talking points the tenant rep can use

Falls back to a deterministic regex-based analyzer when MOCK_FRAUD_GPT=true
or when no OPENAI_API_KEY is set, so tests stay offline-safe.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import openai

from app.config import get_settings


# --- Topic patterns (voice query → lease-clause topic) -----------------------

_TOPIC_PATTERNS: Dict[str, List[str]] = {
    "assignment": [
        r"\bassign(ment|ing|ed)?\b",
        r"\btransfer(\s+the\s+lease)?\b",
    ],
    "sublet": [
        r"\bsublet(ting)?\b",
        r"\bsubleas\w+\b",
    ],
    "renewal": [
        r"\brenew(al|ing|ed)?\b",
        r"\b(option\s+to\s+)?extend\b",
    ],
    "rent_escalation": [
        r"\b(rent\s+)?escalat\w+\b",
        r"\b(annual\s+)?(rent\s+)?(increase|bump)\b",
        r"\bcpi\s+(adjustment|increase|index)\b",
    ],
    "cam_charges": [
        r"\bcam\b",
        r"\b(common\s+area|operating)\s+(maintenance|expenses)\b",
        r"\bpass[\s-]?through(s)?\b",
    ],
    "default": [
        r"\b(default|breach)\b",
        r"\bcure\s+period\b",
    ],
    "termination": [
        r"\bterminat\w+\b",
        r"\b(early\s+)?exit\b",
        r"\bsurrender\b",
    ],
    "indemnity": [
        r"\bindemnif\w+\b",
        r"\bhold\s+harmless\b",
    ],
    "maintenance": [
        r"\bmaintenance\b",
        r"\b(repair|hvac)\s+(responsibilit\w+|obligation)\b",
    ],
    "exclusive_use": [
        r"\bexclusiv\w+\s+(use|right|clause)\b",
        r"\b(competitor|competitive)\s+restriction\b",
    ],
}

# Numeric / window patterns to detect ambiguity (a clause that should specify
# a window but doesn't). Allows punctuation (parens, commas, hyphens) between
# the number and the unit so that "ninety (90) days" or "30-day" both match.
_WINDOW_RE = re.compile(
    r"\b(\d+)[\s\)\.\,\-]*?(day|month|year|business\s*day|biz\s*day)s?\b",
    re.IGNORECASE,
)
_PERCENT_RE = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*%")


def detect_topics(transcript: str) -> Dict[str, List[str]]:
    """Return {topic: [verbatim evidence span, ...]} for each topic the voice query touches."""
    out: Dict[str, list[str]] = {}
    if not transcript:
        return out
    for topic, patterns in _TOPIC_PATTERNS.items():
        evidence: list[str] = []
        for pat in patterns:
            for m in re.finditer(pat, transcript, flags=re.IGNORECASE):
                start = max(0, m.start() - 30)
                end = min(len(transcript), m.end() + 50)
                span = transcript[start:end].strip()
                if span and span not in evidence:
                    evidence.append(span)
        if evidence:
            out[topic] = evidence[:3]
    return out


def _topic_in_clause_text(topic: str, text: str) -> bool:
    if not text:
        return False
    for pat in _TOPIC_PATTERNS.get(topic, []):
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False


def _extract_windows(text: str) -> List[Tuple[int, str]]:
    """Return [(quantity, unit), ...] for every numeric window in the text."""
    out: list[tuple[int, str]] = []
    for m in _WINDOW_RE.finditer(text or ""):
        try:
            qty = int(m.group(1))
        except ValueError:
            continue
        unit = re.sub(r"\s+", " ", m.group(2).lower())
        out.append((qty, unit))
    return out


def _extract_percents(text: str) -> List[float]:
    out: list[float] = []
    for m in _PERCENT_RE.finditer(text or ""):
        try:
            out.append(float(m.group(1)))
        except ValueError:
            continue
    return out


def _normalise_unit(unit: str) -> str:
    u = unit.lower().strip().rstrip("s")
    if "business" in u:
        return "business day"
    return u


def _detect_conflicts(topic: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Two clauses disagreeing on the same topic (different windows or percents)."""
    conflicts: list[dict] = []
    relevant = [c for c in clauses if c["matches_topic"]]
    if len(relevant) < 2:
        return conflicts

    # Window conflict (e.g. one clause says 30 days, another says 90 days)
    bucket: dict[str, list[tuple[dict, int]]] = {}
    for c in relevant:
        for qty, unit in _extract_windows(c["text"]):
            key = _normalise_unit(unit)
            bucket.setdefault(key, []).append((c, qty))
    for unit, entries in bucket.items():
        qtys = {q for _, q in entries}
        if len(qtys) > 1:
            conflicts.append({
                "topic": topic,
                "conflict_type": "duration_window",
                "unit": unit,
                "values": sorted(qtys),
                "evidence": [
                    {"clause_id": e[0]["clause_id"], "qty": e[1], "snippet": e[0]["snippet"]}
                    for e in entries
                ],
            })

    # Percent conflict
    pct_bucket: list[tuple[dict, float]] = []
    for c in relevant:
        for pct in _extract_percents(c["text"]):
            pct_bucket.append((c, pct))
    if pct_bucket:
        unique = {p for _, p in pct_bucket}
        if len(unique) > 1:
            conflicts.append({
                "topic": topic,
                "conflict_type": "percent_value",
                "values": sorted(unique),
                "evidence": [
                    {"clause_id": e[0]["clause_id"], "pct": e[1], "snippet": e[0]["snippet"]}
                    for e in pct_bucket
                ],
            })

    return conflicts


def _detect_ambiguities(topic: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clauses on this topic that should specify a window/percent but don't."""
    needs_window = {"renewal", "termination", "default", "assignment", "sublet"}
    needs_percent = {"rent_escalation"}
    out: list[dict] = []
    for c in clauses:
        if not c["matches_topic"]:
            continue
        has_window = bool(_extract_windows(c["text"]))
        has_percent = bool(_extract_percents(c["text"]))
        problems: list[str] = []
        if topic in needs_window and not has_window:
            problems.append("missing notice/cure window")
        if topic in needs_percent and not has_percent:
            problems.append("missing rent escalation percentage")
        if problems:
            out.append({
                "topic": topic,
                "clause_id": c["clause_id"],
                "clause_type": c["clause_type"],
                "issues": problems,
                "snippet": c["snippet"],
            })
    return out


def _talking_points(topic: str, matches: List[Dict[str, Any]],
                    conflicts: List[Dict[str, Any]], ambiguities: List[Dict[str, Any]]) -> List[str]:
    points: list[str] = []
    if conflicts:
        points.append(
            f"FLAG conflicting {topic.replace('_', ' ')} terms in the lease — "
            "two clauses disagree on the controlling number; request a written clarification "
            "or rely on the tenant-favorable interpretation per standard construction principles."
        )
    if ambiguities:
        points.append(
            f"REQUEST that the landlord add specific window / percentage to the "
            f"{topic.replace('_', ' ')} clause — current language is ambiguous and tilts "
            "interpretation toward the drafter (landlord)."
        )
    if matches and not conflicts and not ambiguities:
        points.append(
            f"The {topic.replace('_', ' ')} clause is unambiguous in the current lease — "
            "quote the specific language back when the question comes up."
        )
    if not matches:
        points.append(
            f"No existing {topic.replace('_', ' ')} clause was found in the lease; this is "
            "either an open negotiation point or a gap. Escalate to counsel before relying on default state law."
        )
    return points


class LeaseClauseAnalyzer:
    """Cross-validate voice clause queries against the lease's clauses + OCR text."""

    def __init__(self) -> None:
        settings = get_settings()
        self.mock_mode = (
            os.environ.get("MOCK_FRAUD_GPT", "").lower() in {"1", "true", "yes"}
            or not getattr(settings, "OPENAI_API_KEY", "")
        )
        self.client = openai.AsyncOpenAI(api_key=getattr(settings, "OPENAI_API_KEY", "") or "sk-mock")
        self.model = settings.OPENAI_MODEL

    async def analyze(
        self,
        transcript: str,
        clauses: List[Tuple[str, str, str]],
        documents: List[Tuple[str, str, str]],
    ) -> Dict[str, Any]:
        """
        clauses: list of (clause_id, clause_type, extracted_text)
        documents: list of (document_id, filename, ocr_text)

        Returns {topics, matches, conflicts, ambiguities, talking_points, mode}.
        """
        if not (transcript or "").strip():
            return {
                "mode": "no_transcript",
                "topics": {},
                "matches": [],
                "conflicts": [],
                "ambiguities": [],
                "talking_points": [],
            }

        topics = detect_topics(transcript)
        all_matches: list[dict] = []
        all_conflicts: list[dict] = []
        all_ambiguities: list[dict] = []
        per_topic_points: dict[str, list[str]] = {}

        for topic in topics:
            # Score every clause for this topic — does the clause text touch the topic?
            scored: list[dict] = []
            for cid, ctype, ctext in clauses:
                snippet = (ctext or "")[:300]
                hit = _topic_in_clause_text(topic, ctext or "") or (
                    ctype and topic.replace("_", "") in ctype.lower().replace("_", "")
                )
                scored.append({
                    "clause_id": str(cid),
                    "clause_type": ctype,
                    "text": ctext or "",
                    "snippet": snippet,
                    "matches_topic": bool(hit),
                })

            matching = [c for c in scored if c["matches_topic"]]
            for c in matching:
                all_matches.append({
                    "topic": topic,
                    "clause_id": c["clause_id"],
                    "clause_type": c["clause_type"],
                    "snippet": c["snippet"],
                    "voice_quote": topics[topic][0] if topics[topic] else "",
                })

            t_conflicts = _detect_conflicts(topic, scored)
            t_ambiguities = _detect_ambiguities(topic, scored)
            all_conflicts.extend(t_conflicts)
            all_ambiguities.extend(t_ambiguities)
            per_topic_points[topic] = _talking_points(topic, matching, t_conflicts, t_ambiguities)

        # Flatten talking points (topic-tagged so the PDF can group them).
        talking_points: list[dict] = []
        for topic, points in per_topic_points.items():
            for p in points:
                talking_points.append({"topic": topic, "point": p})

        result: Dict[str, Any] = {
            "mode": "deterministic" if self.mock_mode else "gpt_attempted",
            "topics": topics,
            "matches": all_matches,
            "conflicts": all_conflicts,
            "ambiguities": all_ambiguities,
            "talking_points": talking_points,
        }

        if self.mock_mode:
            return result

        # Optional GPT enrichment — adds plain-language tenant talking points + a brief.
        try:
            import json
            doc_corpus = "\n---\n".join(t or "" for _, _, t in documents)
            clause_corpus = "\n---\n".join(f"[{ctype}] {ctext or ''}" for _, ctype, ctext in clauses)
            prompt = (
                "You are a senior commercial-real-estate tenant-rep attorney. The "
                "tenant has asked a verbal question. Given the question + the lease's "
                "extracted clauses + supporting OCR text, return: (a) one-paragraph "
                "plain-language answer, (b) 3-5 talking points the asset manager can use, "
                "(c) any conflicts or ambiguities you spotted that weren't already "
                "in the deterministic pre-pass. Return ONLY valid JSON: "
                "{\"answer\": str, \"talking_points\":[str], \"additional_conflicts\":[{topic,description}]}.\n\n"
                f"VOICE QUESTION:\n{transcript[:1500]}\n\n"
                f"LEASE CLAUSES:\n{clause_corpus[:2500]}\n\n"
                f"DOCUMENT OCR (truncated):\n{doc_corpus[:2000]}\n"
            )
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                timeout=20,
                response_format={"type": "json_object"},
            )
            payload = json.loads(resp.choices[0].message.content or "{}")
            if payload.get("answer"):
                result["plain_language_answer"] = payload["answer"]
            for p in payload.get("talking_points", []) or []:
                if isinstance(p, str) and p.strip():
                    result["talking_points"].append({"topic": "gpt", "point": p.strip()})
            for extra in payload.get("additional_conflicts", []) or []:
                if extra.get("description"):
                    result["conflicts"].append({
                        "topic": extra.get("topic", "other"),
                        "conflict_type": "gpt_flag",
                        "description": extra["description"],
                    })
            result["mode"] = "gpt"
        except Exception as e:
            result["error"] = str(e)[:200]
            result["mode"] = "fallback"
        return result
