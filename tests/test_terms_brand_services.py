"""Regression guard: terms.html names the product AI Quran and lists only real features.

Owner decision 2026-10-19: apply the brand and feature-list pass to terms.html.
Section 3 used to promise Adhan call-to-prayer notifications, a Khatmah tracker,
offline access and Tajweed recitations, none of which either app has, and the page
branded the product "Tarteel" (a third party's brand). Legal clauses stay as they are.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TERMS = (ROOT / "terms.html").read_text(encoding="utf-8")


def section(number):
    m = re.search(r"<h2>%d\.[^<]*</h2>(.*?)</div>" % number, TERMS, re.S)
    assert m, f"section {number} missing"
    return re.sub(r"<[^>]+>", " ", m.group(1))


class TermsBrandAndServices(unittest.TestCase):
    def test_no_tarteel_brand(self):
        self.assertNotRegex(TERMS, r"Tarteel")

    def test_title_and_intro_use_ai_quran(self):
        self.assertIn("<title>Terms of Service - AI Quran</title>", TERMS)
        self.assertIn('Welcome to AI Quran ("App" or "Service")', TERMS)

    def test_section3_lists_no_missing_features(self):
        text = section(3).lower()
        for claim in ("adhan", "call to prayer", "khatmah", "offline", "tajweed", "athkar"):
            self.assertNotIn(claim, text, f"section 3 still claims {claim}")

    def test_section3_lists_real_features(self):
        text = section(3).lower()
        for feature in ("114 surahs", "recitation", "prayer times", "qibla", "dua", "tasbih", "99 names", "reading goals", "ai assistant"):
            self.assertIn(feature, text, f"section 3 lacks {feature}")


if __name__ == "__main__":
    unittest.main()
