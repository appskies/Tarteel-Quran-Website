"""Regression guard: the landing site must fit BOTH the iOS and the Android app.

Background: Google Play's reviewer flagged that the Play listing's contact website was an
iOS-only page titled "Tarteel - AI Quran Reader" (App Store rating, adhan reminders), while the
Android listing is "AiQuran: Quran, Prayer & Dua". The site is now "AI Quran" and every claim on
it must hold on both platforms (verified against the Android source at versionCode 10 and the
live iOS App Store listing).

Run: python3 -m unittest discover -s tests -v
"""
import html as htmllib
import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
CONTACT = (ROOT / "contact.html").read_text(encoding="utf-8")
DOWNLOAD_PATH = ROOT / "download" / "index.html"
DOWNLOAD = DOWNLOAD_PATH.read_text(encoding="utf-8") if DOWNLOAD_PATH.exists() else ""
MAIN_JS = (ROOT / "js" / "main.js").read_text(encoding="utf-8")

APP_STORE = "https://apps.apple.com/us/app/ai-quran-reader-athkar-tarteel/id6749589788"
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.skiestech.aiquran"
DOWNLOAD_URL = "https://tarteelquran.app/download/"


class _Links(HTMLParser):
    """Collects <a href>, <img src/alt/class>, <meta> and <script> facts from a page."""

    def __init__(self):
        super().__init__()
        self.hrefs, self.imgs, self.metas, self.scripts = [], [], [], []
        self._in_script = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "script":
            self._in_script = {"attrs": a, "body": ""}

    def handle_data(self, data):
        if self._in_script is not None:
            self._in_script["body"] += data

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script is not None:
            self.scripts.append(self._in_script)
            self._in_script = None


def parse(html):
    p = _Links()
    p.feed(html)
    return p


def visible_text(html):
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def head_text(html):
    """All <title> and <meta content> text, the part search engines and link previews show."""
    title = re.findall(r"<title>(.*?)</title>", html, re.S)
    metas = re.findall(r'<meta\b[^>]*\bcontent="([^"]*)"', html)
    return htmllib.unescape(" ".join(title + metas))


INDEX_P, CONTACT_P, DOWNLOAD_P = parse(INDEX), parse(CONTACT), parse(DOWNLOAD)
ALLOWED_TARTEEL = ("tarteelquran.app", "AI Quran Reader Athkar Tarteel", "ai-quran-reader-athkar-tarteel")


def strip_allowed(text):
    for ok in ALLOWED_TARTEEL:
        text = text.replace(ok, "")
    return text


def without_testimonials(html):
    return re.sub(r'<section class="testimonials".*?</section>', " ", html, flags=re.S)


class StoreLinks(unittest.TestCase):
    def store_hrefs(self, p, host):
        return [h for h in p.hrefs if host in h]

    def test_every_app_store_link_is_the_canonical_slug(self):
        for name, p in (("index", INDEX_P), ("contact", CONTACT_P), ("download", DOWNLOAD_P)):
            links = self.store_hrefs(p, "apps.apple.com")
            self.assertTrue(links, f"{name}: no App Store link")
            for h in links:
                self.assertTrue(h.startswith(APP_STORE), f"{name}: stale App Store link {h}")
                self.assertNotIn("ai-quran-reader-athkar-dua", h)
                self.assertNotIn("id6736780103", h)

    def test_main_js_uses_the_canonical_store_urls(self):
        self.assertTrue(APP_STORE in MAIN_JS, "main.js: App Store URL missing or stale")
        self.assertTrue(PLAY_STORE in MAIN_JS, "main.js: Google Play URL missing")
        self.assertTrue("ai-quran-reader-athkar-dua" not in MAIN_JS, "main.js: old App Store slug")

    def test_every_app_store_badge_is_paired_with_a_google_play_badge(self):
        for name, p, expected in (("index", INDEX_P, 4), ("contact", CONTACT_P, 1), ("download", DOWNLOAD_P, 1)):
            apple = self.store_hrefs(p, "apps.apple.com")
            play = self.store_hrefs(p, "play.google.com")
            self.assertEqual(len(apple), len(play), f"{name}: {len(apple)} App Store vs {len(play)} Play links")
            self.assertGreaterEqual(len(play), expected, f"{name}: expected >= {expected} badge locations")
            for h in play:
                self.assertTrue(h.startswith(PLAY_STORE), f"{name}: bad Play link {h}")

    def test_play_badge_is_the_unmodified_official_png(self):
        badge = ROOT / "Assets" / "google-play-badge.png"
        data = badge.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        # Official en_badge_web_generic.png: 646x250 including the required clear space.
        self.assertEqual((width, height), (646, 250))
        play_imgs = [i for p in (INDEX_P, CONTACT_P, DOWNLOAD_P) for i in p.imgs if "google-play-badge" in i.get("src", "")]
        self.assertGreaterEqual(len(play_imgs), 6)
        for i in play_imgs:
            self.assertEqual(i.get("alt"), "Get it on Google Play")

    def test_download_section_exposes_both_stores_on_index(self):
        play = self.store_hrefs(INDEX_P, "play.google.com")
        self.assertGreaterEqual(len(play), 4, "navbar, hero, download section and final CTA all need Play")


class BrandAndClaims(unittest.TestCase):
    def test_site_is_named_ai_quran(self):
        for html in (INDEX, CONTACT):
            head = head_text(html)
            self.assertIn("AI Quran", head)
            self.assertNotIn("Tarteel - AI Quran Reader", head)
        self.assertIn('<span class="navbar-name">AI Quran</span>', INDEX)
        self.assertIn('<span class="footer-name">AI Quran</span>', INDEX)
        self.assertIn("Download AI Quran", visible_text(INDEX))

    def test_tarteel_is_not_used_as_a_brand(self):
        for name, html in (("index", INDEX), ("contact", CONTACT), ("download", DOWNLOAD)):
            text = strip_allowed(visible_text(without_testimonials(html)) + " " + head_text(html))
            self.assertNotRegex(text, r"(?i)tarteel", f"{name}: 'Tarteel' outside the allowed store name / domain")

    def test_store_names_are_mentioned(self):
        text = visible_text(INDEX)
        self.assertIn("AI Quran Reader Athkar Tarteel", text)
        self.assertIn("AiQuran: Quran, Prayer & Dua", text)

    def test_no_claims_that_are_false_on_android(self):
        flat = (visible_text(without_testimonials(INDEX)) + " " + head_text(INDEX)).lower()
        # The one allowed mention is the honest disclaimer that reminders do not play an adhan.
        flat = flat.replace("do not play an adhan", "")
        banned = {
            "adhan": "Android reminders use the default notification sound, not an adhan",
            "never miss a prayer": "reminders are best effort and subject to device settings",
            "app store rating": "iOS-only rating",
            "based on app store reviews": "iOS-only rating",
            "4.8": "stale iOS rating (live rating is lower)",
            "khatmah tracker": "neither app has a Khatmah tracker, only reading goals",
            "comprehensive tafsir": "tafsir is AI-written, not a classical tafsir book",
            "no internet required": "both apps need a connection to start",
            "proper tajweed": "unverifiable",
            "tarteel style": "third-party brand",
        }
        for needle, why in banned.items():
            self.assertNotIn(needle, flat, f"{needle!r} must not appear: {why}")
        # "Athkar" only inside the App Store listing name.
        self.assertNotIn("athkar", flat.replace("ai quran reader athkar tarteel", ""))

    def test_translation_claims_state_the_arabic_exception(self):
        # Both apps hide the translation when the device language is Arabic
        # (Android AyahRow.kt isArabicLocale, iOS AyahCell.swift isArabic), so "a translation
        # alongside" is only true with that exception. The Play listing states it too.
        flat = visible_text(INDEX).lower()
        self.assertGreaterEqual(flat.count("device language is arabic"), 2,
                                "feature card and translations card must both carry the Arabic exception")

    def test_offline_claim_is_scoped(self):
        flat = visible_text(INDEX)
        self.assertIn("needs an internet connection to start", flat)

    def test_reminders_do_not_promise_an_adhan_sound(self):
        flat = visible_text(INDEX)
        self.assertIn("notification sound", flat)
        self.assertRegex(flat, r"(?i)not an adhan|do not play an adhan|no adhan")

    def test_ai_and_premium_are_disclosed(self):
        flat = visible_text(INDEX)
        self.assertRegex(flat, r"(?i)AI answers can be inaccurate")
        self.assertRegex(flat, r"(?i)fatwa")
        self.assertRegex(flat, r"(?i)Premium")

    def test_testimonials_have_no_platform_label_or_user_count(self):
        # Owner decision 2026-10-19: keep the testimonials, without an iPhone or Android
        # label and without an unverifiable "thousands of users" count.
        section = re.search(r'<section class="testimonials".*?</section>', INDEX, re.S).group(0)
        heading = re.search(r'<h2 class="section-title">(.*?)</h2>\s*<p class="section-subtitle">(.*?)</p>', section, re.S)
        self.assertIsNotNone(heading, "testimonials heading/subtitle missing")
        label = " ".join(heading.groups())
        self.assertEqual(heading.group(1).strip(), "What Our Users Say")
        self.assertNotRegex(label, r"(?i)iphone|android|thousands")

    def test_social_image_is_absolute(self):
        content = {m.get("property") or m.get("name"): m.get("content") for m in INDEX_P.metas}
        self.assertTrue(content["og:image"].startswith("https://tarteelquran.app/"))
        self.assertTrue(content["twitter:image"].startswith("https://tarteelquran.app/"))

    def test_structured_data_covers_both_platforms(self):
        blocks = [s["body"] for s in INDEX_P.scripts if s["attrs"].get("type") == "application/ld+json"]
        self.assertEqual(len(blocks), 1, "expected one JSON-LD block")
        data = json.loads(blocks[0])
        self.assertEqual(data["@type"], "SoftwareApplication")
        self.assertEqual(data["name"], "AI Quran")
        self.assertEqual(data["operatingSystem"], "iOS, Android")
        urls = {o["url"] for o in data["offers"]}
        self.assertEqual(urls, {APP_STORE, PLAY_STORE})
        self.assertNotIn("aggregateRating", data)


class DownloadPage(unittest.TestCase):
    def test_page_exists_and_is_noindex(self):
        self.assertTrue(DOWNLOAD_PATH.exists(), "download/index.html is missing")
        robots = [m for m in DOWNLOAD_P.metas if m.get("name") == "robots"]
        self.assertTrue(robots and "noindex" in robots[0]["content"])

    def test_both_badges_work_without_javascript(self):
        self.assertIn(APP_STORE, " ".join(DOWNLOAD_P.hrefs))
        self.assertIn(PLAY_STORE, " ".join(DOWNLOAD_P.hrefs))
        self.assertNotIn("<noscript>", DOWNLOAD, "badges must be visible without a noscript wrapper")

    def test_redirects_by_user_agent(self):
        body = "".join(s["body"] for s in DOWNLOAD_P.scripts)
        self.assertRegex(body, r"iPhone|iPad|iPod")
        self.assertRegex(body, r"Android", "Android UA must route to Google Play")
        self.assertIn("location.replace", body)
        self.assertIn(APP_STORE, body)
        self.assertIn(PLAY_STORE, body)
        # iPadOS 13+ reports a desktop Mac UA; touch points tell it apart.
        self.assertIn("maxTouchPoints", body)

    def test_tiktok_redirect_is_platform_aware(self):
        # Bug guard: the ?from=tiktok redirect used to send every visitor, Android included, to the App Store.
        self.assertIsNone(re.search(r"window\.location\.href\s*=\s*APP_STORE_URL", MAIN_JS))
        self.assertTrue("Android" in MAIN_JS, "main.js must route Android to Google Play")


class QrCode(unittest.TestCase):
    QR = ROOT / "Assets" / "qr-code-download.png"

    def test_qr_is_a_real_png(self):
        self.assertEqual(self.QR.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertFalse((ROOT / "Assets" / "qr-code-5.png").exists(), "old App Store only QR must be gone")
        srcs = [i.get("src") for i in INDEX_P.imgs]
        self.assertIn("Assets/qr-code-download.png", srcs)
        self.assertNotIn("Assets/qr-code-5.png", srcs)

    def test_qr_label(self):
        self.assertIn("Scan to download on iPhone or Android", visible_text(INDEX))

    @unittest.skipUnless(shutil.which("zbarimg"), "zbarimg not installed")
    def test_qr_decodes_to_the_download_page(self):
        out = subprocess.run(["zbarimg", "--quiet", "--raw", str(self.QR)], capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), DOWNLOAD_URL)


class ContactPage(unittest.TestCase):
    def test_contact_is_platform_neutral(self):
        text = visible_text(CONTACT) + " " + head_text(CONTACT)
        self.assertNotIn("Tarteel", text)
        self.assertNotIn("mzstatic.com", CONTACT, "no hot-linked iOS app icon / badge")
        self.assertNotIn("toolbox.marketingtools.apple.com", CONTACT)
        self.assertIn("AI Quran", text)


class LegalPagesUntouched(unittest.TestCase):
    def test_privacy_and_terms_keep_their_cross_platform_text(self):
        privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("Quran AI (AI Quran Reader)", privacy)
        self.assertIn("android-advertising", privacy)


if __name__ == "__main__":
    unittest.main()
