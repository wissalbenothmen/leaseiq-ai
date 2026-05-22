from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, date, timedelta, timezone
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


class CriticalDateExtractor:
    """Service to extract and normalize critical dates from lease documents."""

    EXTRACTION_PROMPT_TEMPLATE = """
    Extract all critical dates and deadlines from the following lease document.
    Lease commencement date is: {commencement_date}

    Return a JSON array with objects containing:
    - date_type: string (expiry, renewal_option, rent_review, option_exercise, notice_deadline)
    - date_value: date (YYYY-MM-DD format, calculated from commencement_date if relative)
    - notice_days_required: integer (days' notice required before this date, null if not applicable)
    - description: string

    Lease Document Text (excerpt):
    {lease_text}

    Return ONLY valid JSON array, no additional text.
    """

    async def extract_critical_dates(
        self, lease_text: str, commencement_date: date
    ) -> dict:
        """Extract critical dates from lease text."""
        try:
            prompt = self.EXTRACTION_PROMPT_TEMPLATE.format(
                commencement_date=commencement_date.isoformat(),
                lease_text=lease_text[:6000],
            )
            response = await _client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            result_text = response.choices[0].message.content.strip()
            critical_dates = json.loads(result_text)
            return {
                "success": True,
                "dates": critical_dates,
                "extraction_count": len(critical_dates),
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in date extractor: {e}")
            return self._rule_based_extract(lease_text, commencement_date)
        except Exception as e:
            logger.error(f"Error extracting critical dates: {e}")
            return self._rule_based_extract(lease_text, commencement_date)

    def _rule_based_extract(self, lease_text: str, commencement_date: date) -> dict:
        """Fallback rule-based date extraction when AI is unavailable."""
        import re
        dates = []
        text_lower = lease_text.lower()

        # Look for expiration/lease end dates (e.g., "December 31, 2025")
        pattern = r'(?:expir(?:ation|y)|expiration|lease end|lease expir)\D{0,30}?(\w+ \d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2})'
        for match in re.finditer(pattern, text_lower):
            try:
                raw = match.group(1).strip()
                from datetime import datetime as dt
                for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
                    try:
                        parsed = dt.strptime(raw, fmt).date()
                        dates.append({
                            "date_type": "expiry",
                            "date_value": parsed.isoformat(),
                            "notice_days_required": None,
                            "description": "Lease expiration date",
                        })
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Look for notice requirements (e.g., "12 months notice")
        notice_pattern = r'(\d+)\s*months?\s*notice'
        for match in re.finditer(notice_pattern, text_lower):
            months = int(match.group(1))
            if dates:
                dates[0]["notice_days_required"] = months * 30

        # Always return at least one entry (commencement)
        if not dates:
            dates.append({
                "date_type": "commencement",
                "date_value": commencement_date.isoformat(),
                "notice_days_required": None,
                "description": "Lease commencement date",
            })

        return {"success": True, "dates": dates, "extraction_count": len(dates)}

    def calculate_days_until(self, target_date: date) -> int:
        """Calculate days from today until target date."""
        return (target_date - datetime.now(timezone.utc).date()).days

    def is_upcoming(self, target_date: date, threshold_days: int = 90) -> bool:
        """Check if date is within threshold days."""
        days_until = self.calculate_days_until(target_date)
        return 0 <= days_until <= threshold_days


extractor = CriticalDateExtractor()
