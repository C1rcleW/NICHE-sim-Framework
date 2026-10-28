"""Capture the three README screenshots from the real dashboard.

Usage:
    pip install -e ".[dev,e2e]"
    python -m playwright install chromium
    python tools/capture_dashboard_screenshots.py
    # Alternatively reuse installed Chrome:
    PLAYWRIGHT_CHANNEL=chrome python tools/capture_dashboard_screenshots.py
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_server(port: int) -> subprocess.Popen:
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
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"dashboard server exited with {process.returncode}")
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return process
        except httpx.HTTPError:
            time.sleep(0.1)
    process.terminate()
    raise RuntimeError("dashboard server did not become ready")


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture dashboard README screenshots")
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "screenshots"))
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    port = _free_port()
    server = _start_server(port)
    channel = os.environ.get("PLAYWRIGHT_CHANNEL") or None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel=channel)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            page.click("#runSimBtn")
            expect(page.locator("#statusText")).to_have_text(
                "Simulation complete", timeout=30_000,
            )
            page.wait_for_function("typeof Plotly !== 'undefined'", timeout=30_000)
            expect(page.locator("#timeseriesCard")).to_be_visible(timeout=10_000)
            page.screenshot(path=str(out_dir / "dashboard.png"), full_page=True)

            page.click('button[data-tab="fitting"]')
            page.select_option("#fitModel", "wellbeing")
            page.click("#fitRunBtn")
            expect(page.locator("#statusText")).to_contain_text("Fit done", timeout=120_000)
            expect(page.locator("#fitResultCard")).to_be_visible()
            page.screenshot(path=str(out_dir / "fitting.png"), full_page=True)

            page.click('button[data-tab="network"]')
            page.wait_for_function(
                "document.querySelectorAll('#networkCards .card').length === 2",
                timeout=10_000,
            )
            page.wait_for_timeout(500)
            page.screenshot(path=str(out_dir / "network.png"), full_page=True)
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    print(f"已生成截图: {out_dir / 'dashboard.png'}")
    print(f"已生成截图: {out_dir / 'fitting.png'}")
    print(f"已生成截图: {out_dir / 'network.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
