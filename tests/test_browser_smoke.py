"""Opt-in Playwright smoke test for the real dashboard.

Run with:
    pip install -e ".[dev,e2e]"
    python -m playwright install chromium
    RUN_BROWSER_TESTS=1 python -m pytest tests/test_browser_smoke.py -q
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.browser

if os.environ.get("RUN_BROWSER_TESTS") != "1":
    pytest.skip("设置 RUN_BROWSER_TESTS=1 才运行真实浏览器测试", allow_module_level=True)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def dashboard_url():
    port = _free_port()
    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "family_abm.web.app:app",
            "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f"dashboard server exited with {process.returncode}")
            try:
                if httpx.get(url, timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            pytest.fail("dashboard server did not become ready")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_real_browser_dashboard_flow(dashboard_url: str) -> None:
    try:
        from playwright.sync_api import expect, sync_playwright
    except ImportError as exc:  # pragma: no cover - CI installs the e2e extra
        pytest.fail(f"RUN_BROWSER_TESTS=1 需要 Playwright：{exc}")

    page_errors: list[str] = []
    channel = os.environ.get("PLAYWRIGHT_CHANNEL") or None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, channel=channel)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        try:
            page.goto(dashboard_url, wait_until="load")
            page.click("#runSimBtn")
            expect(page.locator("#statusText")).to_have_text(
                "Simulation complete", timeout=30_000,
            )
            expect(page.locator(".agent-chip")).to_have_count(5)
            expect(page.locator("#tab-charts")).to_be_visible()

            page.click('button[data-tab="fitting"]')
            expect(page.locator("#fitControlCard")).to_be_visible()
            expect(page.locator("#fitModel")).to_have_value("wellbeing")

            page.click('button[data-tab="network"]')
            page.wait_for_function(
                "document.querySelectorAll('#networkCards .card').length === 2",
                timeout=10_000,
            )

            page.click("#langBtn")
            page.click('#langDrop .lang-item[data-lang="zh"]')
            expect(page.locator("#statusText")).to_have_text("仿真完成", timeout=10_000)
            expect(page.locator(".family-card h3").first).to_contain_text("家庭")
        finally:
            browser.close()

    assert not page_errors, f"浏览器页面错误：{page_errors}"
