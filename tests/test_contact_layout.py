"""Regression guard: contact.html must not scroll sideways on narrow phones or small tablets.

Bug: at 320 to 350px and again at 770 to 790px the contact page was wider than the viewport
(scrollWidth 359 and 795). The grid children and the flex text column kept their min-content
width, and the unbreakable email address pushed the info cards past the container.

The browser check needs Playwright and a Chromium binary. Set CHROMIUM_PATH to a Chromium or
chrome-headless-shell executable when Playwright's own download is not installed. It skips
when neither is available.

Run: python3 -m unittest discover -s tests -v
"""
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "css" / "style.css").read_text(encoding="utf-8")

NARROW_WIDTHS = (320, 330, 340, 350, 360, 390, 768, 770, 780, 790, 800, 1024)


def rule(selector):
    match = re.search(r"(?m)^" + re.escape(selector) + r"\s*\{([^}]*)\}", CSS)
    return match.group(1) if match else ""


class ContactLayoutCss(unittest.TestCase):
    def test_grid_children_can_shrink(self):
        self.assertRegex(rule(".contact-content > *"), r"min-width:\s*0")

    def test_fixed_width_captcha_is_scaled_on_narrow_phones(self):
        self.assertRegex(CSS, r"@media \(max-width: 350px\)\s*\{\s*\.h-captcha\s*\{[^}]*scale\(")

    def test_info_text_column_can_shrink_and_wrap(self):
        self.assertRegex(rule(".info-item > div"), r"min-width:\s*0")
        self.assertRegex(rule(".info-item p"), r"overflow-wrap:\s*anywhere")


class ContactLayoutBrowser(unittest.TestCase):
    def test_no_horizontal_scroll(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright not installed")
        executable = os.environ.get("CHROMIUM_PATH") or None
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(executable_path=executable)
            except Exception as exc:  # no browser binary on this machine
                self.skipTest(f"no Chromium available: {exc.__class__.__name__}")
            try:
                overflowing = {}
                for width in NARROW_WIDTHS:
                    context = browser.new_context(viewport={"width": width, "height": 700})
                    context.route("**/*", lambda route: route.continue_()
                                  if route.request.url.startswith("file:") else route.abort())
                    page = context.new_page()
                    page.goto((ROOT / "contact.html").as_uri(), wait_until="domcontentloaded")
                    # Web fonts are blocked here, so use a worst-case unbreakable address: the layout
                    # must hold whatever the font and address length are.
                    page.evaluate("document.querySelector('.info-item p').textContent = "
                                  "'appskiesltd.support.team@example-mail.com'")
                    # The Web3Forms script injects a fixed 302px hCaptcha iframe; stand in for it offline.
                    page.evaluate("document.querySelector('.h-captcha').innerHTML = "
                                  "'<iframe style=\"width:302px;height:78px;border:0\"></iframe>'")
                    scroll_width = page.evaluate("document.documentElement.scrollWidth")
                    if scroll_width > width:
                        overflowing[width] = scroll_width
                    context.close()
            finally:
                browser.close()
        self.assertEqual(overflowing, {}, "contact.html is wider than the viewport at these widths")


if __name__ == "__main__":
    unittest.main()
