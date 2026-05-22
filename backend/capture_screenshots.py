"""Playwright screenshot harness — captures one canonical PNG per screen.

Run after `seed_data.py`, with backend on :8022 and frontend on :5022.
Output: ../project-audit/screenshots/*.png
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parent.parent / "project-audit" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

EMAIL = "admin@leaseiq.demo"
PASSWORD = "Admin123!"
BASE = "http://localhost:5022"

VIEWPORT = {"width": 1440, "height": 900}


async def login(page) -> None:
    await page.goto(f"{BASE}/login", wait_until="networkidle")
    await page.fill('input[type="email"]', EMAIL)
    await page.fill('input[type="password"]', PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_url("**/dashboard", timeout=15000)
    await page.wait_for_load_state("networkidle")


async def snap(page, slug: str, *, full_page: bool = False) -> None:
    path = OUT / f"{slug}.png"
    await page.wait_for_timeout(700)  # let charts settle
    await page.screenshot(path=path, full_page=full_page, type="png")
    print(f"  [OK] {slug}.png ({path.stat().st_size // 1024} KB)")


async def first_lease_id(context) -> str:
    api = context.request
    r = await api.post("http://localhost:8022/api/v1/auth/login", data={
        "username": EMAIL, "password": PASSWORD,
    })
    token = (await r.json())["access_token"]
    leases = await api.get("http://localhost:8022/api/v1/leases", headers={"Authorization": f"Bearer {token}"})
    return (await leases.json())[0]["id"]


async def main() -> int:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
        page = await context.new_page()

        # 01 — login screen (pre-auth)
        await page.goto(f"{BASE}/login", wait_until="networkidle")
        await page.wait_for_timeout(800)
        await snap(page, "01_login")

        # Login
        await login(page)

        # 02 — dashboard
        await snap(page, "02_dashboard", full_page=True)

        # 03 — leases list
        await page.goto(f"{BASE}/leases", wait_until="networkidle")
        await snap(page, "03_leases", full_page=True)

        # 04 — lease detail (first lease)
        lease_id = await first_lease_id(context)
        await page.goto(f"{BASE}/leases/{lease_id}", wait_until="networkidle")
        await page.wait_for_timeout(600)
        await snap(page, "04_lease_detail", full_page=True)

        # 05 — clauses (cross-portfolio with AI commentary)
        await page.goto(f"{BASE}/clauses", wait_until="networkidle")
        await page.wait_for_timeout(800)
        await snap(page, "05_clauses", full_page=True)

        # 06 — obligations
        await page.goto(f"{BASE}/obligations", wait_until="networkidle")
        await page.wait_for_timeout(400)
        await snap(page, "06_obligations", full_page=True)

        # 07 — analytics
        await page.goto(f"{BASE}/analytics", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await snap(page, "07_analytics", full_page=True)

        # 08 — branded API docs
        await page.goto("http://localhost:8022/api/docs", wait_until="networkidle")
        await page.wait_for_timeout(1200)
        await snap(page, "08_api_docs", full_page=True)

        await browser.close()

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
