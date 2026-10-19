"""Regression guard: the contact page logo and favicon must load.

Bug: contact.html pointed its navbar logo, footer logo and favicon at an
is1-ssl.mzstatic.com App Store icon URL that now returns 404, so the live page
showed broken-image alt text instead of the logo. The site ships its own icon
in Assets/app-icon.png (index.html already uses it).

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTACT = (ROOT / "contact.html").read_text(encoding="utf-8")


class ContactLogo(unittest.TestCase):
    def test_no_app_store_cdn_images(self):
        self.assertNotIn("mzstatic.com", CONTACT)

    def test_logo_favicon_use_local_icon_that_exists(self):
        for cls in ("navbar-logo", "footer-logo"):
            m = re.search(r'<img src="([^"]+)"[^>]*class="' + cls + '"', CONTACT)
            self.assertIsNotNone(m, f"{cls} img missing")
            self.assertTrue((ROOT / m.group(1)).is_file(), f"{cls} src {m.group(1)} not in repo")
        icon = re.search(r'<link rel="icon"[^>]*href="([^"]+)"', CONTACT)
        self.assertIsNotNone(icon, "favicon link missing")
        self.assertTrue((ROOT / icon.group(1)).is_file(), f"favicon {icon.group(1)} not in repo")


if __name__ == "__main__":
    unittest.main()
