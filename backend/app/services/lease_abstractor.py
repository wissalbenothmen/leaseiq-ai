from __future__ import annotations
import json
import logging
from typing import Optional
from datetime import date, datetime
import asyncio
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


class LeaseAbstractor:
    """Service to extract key lease terms using GPT-4.1 Mini."""

    EXTRACTION_PROMPT_TEMPLATE = """
    Extract the following key lease terms from the provided lease document OCR text.
    Return a JSON object with these fields:
    - tenant_name: string
    - landlord_name: string
    - property_address: string
    - lease_type: string (gross, net, modified_gross, percentage)
    - term_start: date (YYYY-MM-DD format, null if not found)
    - term_end: date (YYYY-MM-DD format, null if not found)
    - base_rent: number (null if not found)
    - rent_escalation_pct: number (null if not found)
    - suite_number: string (null if not found)
    - square_footage: number (null if not found)
    - confidence_overall: number (0-100)

    Lease Document OCR Text:
    {ocr_text}

    Return ONLY valid JSON, no additional text.
    """

    def _rule_based_extract(self, ocr_text: str) -> dict:
        """Fallback rule-based extraction when AI is unavailable."""
        import re
        data: dict = {}
        text = ocr_text

        # Tenant name
        m = re.search(r'(?:tenant|lessee)[:\s]+([A-Z][A-Za-z0-9\s,\.]+?)(?:\n|,|;)', text)
        if m:
            data["tenant_name"] = m.group(1).strip()

        # Landlord name
        m = re.search(r'(?:landlord|lessor)[:\s]+([A-Z][A-Za-z0-9\s,\.]+?)(?:\n|,|;)', text)
        if m:
            data["landlord_name"] = m.group(1).strip()

        # Dates (YYYY-MM-DD or Month DD, YYYY)
        date_pattern = r'(\d{4}-\d{2}-\d{2}|\w+ \d{1,2},\s*\d{4})'
        matches = re.findall(date_pattern, text)
        if len(matches) >= 1:
            data.setdefault("term_start", matches[0])
        if len(matches) >= 2:
            data.setdefault("term_end", matches[1])

        # Base rent
        m = re.search(r'(?:base rent|monthly rent)[^\d]*\$?([\d,]+(?:\.\d{2})?)', text, re.IGNORECASE)
        if m:
            try:
                data["base_rent"] = float(m.group(1).replace(",", ""))
            except ValueError:
                pass

        return {
            "success": True,
            "data": data,
            "confidence": 30,
            "fallback": True,
        }

    async def extract_lease_terms(self, ocr_text: str) -> dict:
        """Extract lease terms from OCR text using configured OpenAI model.

        Uses JSON mode, request timeout, and bounded retry-with-backoff on
        transient errors. Falls back to regex extraction on terminal failure.
        """
        prompt = self.EXTRACTION_PROMPT_TEMPLATE.format(ocr_text=ocr_text[:8000])
        if len(ocr_text) > 8000:
            logger.warning("ocr_text truncated for AI extraction: original=%d kept=%d", len(ocr_text), 8000)

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                response = await _client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                    timeout=30.0,
                )
                result_text = response.choices[0].message.content.strip()
                extracted_data = json.loads(result_text)
                usage = getattr(response, "usage", None)
                logger.info(
                    "lease_abstractor.ok model=%s in_tokens=%s out_tokens=%s",
                    settings.OPENAI_MODEL,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                )
                return {
                    "success": True,
                    "data": extracted_data,
                    "confidence": extracted_data.get("confidence_overall", 0),
                }
            except json.JSONDecodeError as e:
                logger.error("lease_abstractor.json_decode_error: %s", e)
                return self._rule_based_extract(ocr_text)
            except Exception as e:
                last_err = e
                logger.warning("lease_abstractor.retry attempt=%d err=%s", attempt + 1, e)
                await asyncio.sleep(0.5 * (2 ** attempt))

        logger.error("lease_abstractor.exhausted err=%s", last_err)
        return self._rule_based_extract(ocr_text)


abstractor = LeaseAbstractor()
