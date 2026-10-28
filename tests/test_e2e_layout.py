"""Mise en page responsive : aucune page ne doit déborder horizontalement sur mobile."""

import os

import pytest

os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
pytest.importorskip('playwright')
from playwright.sync_api import sync_playwright  # noqa: E402

from tests.snapshots import pages, world  # noqa: E402, F401
from tests.test_e2e import login_as  # noqa: E402

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

MOBILE_WIDTH = 390


def test_no_horizontal_overflow_on_mobile(world, live_server):  # noqa: F811
    users = {'anon': None, 'student': world['student'], 'admin': world['admin'], 'teacher': world['teacher']}
    overflowing = []

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:
            pytest.skip(f'Chromium indisponible : {exc}')
        for who, items in pages(world).items():
            context = browser.new_context(viewport={'width': MOBILE_WIDTH, 'height': 844})
            page = context.new_page()
            page.live_server_url = live_server.url
            if users[who] is not None:
                login_as(page, users[who])
            for name, path in items:
                page.goto(live_server.url + path, wait_until='networkidle')
                width = page.evaluate('document.documentElement.scrollWidth')
                if width > MOBILE_WIDTH:
                    overflowing.append(f'{name} ({width}px)')
            context.close()
        browser.close()

    assert not overflowing, f'Débordement horizontal sur mobile : {overflowing}'
