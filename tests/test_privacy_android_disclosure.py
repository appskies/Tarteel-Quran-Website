"""Regression guard for the shared privacy policy (privacy.html).

The page is shared by the live iOS app and the Android app. Bug: section 4 said the
Android version has no ads, attribution or analytics SDKs and does not access the
Android advertising ID. The Android binary ships LevelPlay, AppsFlyer, Firebase
Analytics and Crashlytics, and the merged manifest declares AD_ID.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "privacy.html"
HTML = PAGE.read_text(encoding="utf-8")

VOID = {"meta", "br", "hr", "img", "input", "link"}


class _Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def android_block() -> str:
    m = re.search(r'<div class="note" id="android-advertising">(.*?)\n  </div>', HTML, re.S)
    return m.group(1) if m else ""


class PrivacyAndroidDisclosure(unittest.TestCase):
    def has(self, needle, hay):
        self.assertTrue(needle in hay, f"missing: {needle!r}")

    def lacks(self, needle, hay):
        self.assertTrue(needle not in hay, f"must not appear: {needle!r}")

    def matches(self, pattern, hay):
        self.assertTrue(re.search(pattern, hay), f"no match: {pattern!r}")

    def test_false_android_claims_are_gone(self):
        flat = text_of(HTML).lower()
        for claim in (
            "includes no advertising, attribution or analytics sdks",
            "shows no ads",
            "does not access the android advertising id",
        ):
            self.lacks(claim, flat)

    def test_android_block_discloses_every_sdk(self):
        block = text_of(android_block())
        self.assertTrue(block, "missing <div id=android-advertising> block in section 4")
        for term in ("LevelPlay", "AppsFlyer", "Firebase Analytics", "Crashlytics", "advertising ID"):
            self.has(term, block)

    def test_android_block_states_consent_and_opt_out_facts(self):
        block = text_of(android_block())
        self.matches(r"no (ATT|App Tracking Transparency)", block)
        self.matches(r"does not (currently )?show (its own|an in-app) consent", block)
        self.has("Delete advertising ID", block)
        self.has("uninstall", block)

    def test_att_and_idfa_stay_ios_only(self):
        self.has("iOS-only", text_of(HTML))
        self.lacks("IDFA", text_of(android_block()))

    def test_other_android_statements_updated(self):
        flat = text_of(HTML)
        self.matches(r"Android advertising ID", flat)  # device-information list
        self.matches(r"On Android, Firebase also provides analytics and crash reporting", flat)
        self.has("overpass-api.de", flat)  # nearby-mosque location recipient

    def test_new_android_text_has_no_em_dash(self):
        self.assertTrue(android_block(), "missing android block")
        self.lacks("—", android_block())

    def test_premium_users_still_get_sdk_initialization_disclosed(self):
        block = text_of(android_block())
        self.matches(r"premium.*SDKs may still (start|initialize)", block)

    def section(self, n: int) -> str:
        m = re.search(rf"<h2>{n}\. .*?</h2>(.*?)(?=<h2>|</div>\s*</body>)", HTML, re.S)
        return text_of(m.group(1)) if m else ""

    def test_section5_legal_basis_matches_android_reality(self):
        s5 = self.section(5)
        self.assertTrue(s5, "section 5 not found")
        self.matches(r"Consent:.*iOS.*ATT", s5)
        self.matches(r"On Android.*does not (currently )?collect consent", s5)
        self.matches(r"Legitimate interests:.*Android.*(advertising|ads)", s5)

    def test_section8_sale_statement_is_qualified_for_android(self):
        s8 = self.section(8)
        self.matches(r"Android.*advertising ID.*(sale|sharing)", s8)
        self.matches(r"(CCPA|CPRA|some laws).*(sale|sharing)", s8)

    def test_section10_opt_out_wording_is_qualified_for_android(self):
        s10 = self.section(10)
        self.matches(r"Android.*no in-app.*opt-out", s10)
        self.matches(r"(?i)delete your advertising ID", s10)
        self.lacks("we honor recognized opt-out signals where applicable", s10)

    def test_last_updated_bumped(self):
        self.has("Last updated: October 3, 2026", text_of(HTML))

    def test_markup_is_balanced(self):
        p = _Balance()
        p.feed(HTML)
        self.assertEqual(p.errors, [])
        self.assertEqual(p.stack, [])


if __name__ == "__main__":
    unittest.main()
