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
TERMS = (Path(__file__).resolve().parent.parent / "terms.html").read_text(encoding="utf-8")

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
        self.matches(r"Analytics and Crashlytics on both platforms", flat)  # no longer Android-only
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
        self.matches(r"Android \(pre-release test build\).*does not yet show a consent prompt", s5)
        # Legitimate interests must NOT be claimed for advertising, attribution or analytics.
        self.matches(r"(?i)do not rely on legitimate interests for (advertising|ads)", s5)
        self.assertIsNone(re.search(r"Legitimate interests:[^.]*Improving", s5), "old LI wording")

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
        self.has("Last updated: October 4, 2026", text_of(HTML))
        self.lacks("October 3, 2026", text_of(HTML))

    def test_markup_is_balanced(self):
        p = _Balance()
        p.feed(HTML)
        self.assertEqual(p.errors, [])
        self.assertEqual(p.stack, [])


class PrivacyMatchesCurrentCode(unittest.TestCase):
    """Each test pins one statement that an audit found to be false or missing.

    Evidence for every statement is in the PR description (file:line in the Android
    and iOS repos). Never weaken these to make a build green: change the code facts first.
    """

    flat = text_of(HTML)

    def has(self, needle, hay=None):
        hay = self.flat if hay is None else hay
        self.assertTrue(needle in hay, f"missing: {needle!r}")

    def lacks(self, needle, hay=None):
        hay = self.flat if hay is None else hay
        self.assertTrue(needle not in hay, f"must not appear: {needle!r}")

    def matches(self, pattern, hay=None):
        hay = self.flat if hay is None else hay
        self.assertTrue(re.search(pattern, hay), f"no match: {pattern!r}")

    def section(self, n):
        m = re.search(rf"<h2>{n}\. .*?</h2>(.*?)(?=<h2>|</div>\s*</body>)", HTML, re.S)
        return text_of(m.group(1)) if m else ""

    # 1. Android email IS written to Firebase
    def test_android_email_is_stored_in_firebase(self):
        for claim in ("kept on your device only", "not written to Firebase",
                      "onboarding email remains on your device only",
                      "it does not store your onboarding email"):
            self.lacks(claim)
        s21 = self.section(2)
        self.matches(r"On both iOS and Android.*Firebase.*userEmails", s21)
        self.matches(r"(?i)created and updated timestamps", s21)
        self.matches(r"On Android a copy is also kept on your device.*support emails", s21)

    # 2. Android HAS in-app deletion
    def test_android_in_app_deletion_is_described(self):
        self.lacks("there is no in-app account-deletion option")
        self.lacks("On Android, request deletion of your Firebase guest account")
        s6 = self.section(6)
        self.matches(r"On Android.*Settings › Delete My Data", s6)
        self.matches(r"userEmails", s6)
        self.matches(r"ReferralManagerUsers|referral record", s6)
        self.matches(r"(?i)does not (delete|remove).*(RevenueCat|AppsFlyer)", s6)
        self.matches(r"(?i)referral redemption record", s6)
        self.matches(r"(?i)analytics.*(held|retained) by", s6)
        self.matches(r"(?i)AI usage counters", s6)
        s10 = self.section(10)
        self.matches(r"On Android.*Settings › Delete My Data", s10)
        self.matches(r"deletion reference", s10)

    def test_terms_describe_android_deletion(self):
        flat = text_of(TERMS)
        self.lacks("On Android, you may terminate your account at any time by emailing", flat)
        self.matches(r"On iOS and Android.*Settings › Delete My Data", flat)

    # 3. Referral is live on Android
    def test_referral_is_live_on_android(self):
        s21 = self.section(2)
        self.matches(r"On Android, the App has a referral feature", s21)
        self.has("first six characters of your Firebase UID", s21)
        self.has("ReferralManagerUsers", s21)
        self.matches(r"(?i)(server|Cloud Function).*records.*referr", s21)
        self.lacks("Earlier App versions may have associated referral credits")

    # 4. SDK start timing
    def test_sdk_start_timing_is_accurate(self):
        block = text_of(android_block())
        self.lacks("keeps these SDKs off until it finishes a start-up check")
        self.matches(r"later launches.*(as the app (process )?starts|when the app (launches|starts))", block)
        self.matches(r"first launch.*home screen", block)

    # 5. AD_ID
    def test_ad_id_statement_is_sourced(self):
        block = text_of(android_block())
        self.has("com.google.android.gms.permission.AD_ID", block)
        self.matches(r"(merged release manifest|bundled SDKs).*declare", block)

    # 6. Raw coordinates go to OS geocoders; last-known stored on device
    def test_location_geocoder_disclosure(self):
        s2 = self.section(2)
        self.matches(r"raw coordinates.*(Android Geocoder|geocoder)", s2)
        self.has("CLGeocoder", s2)
        self.has("fused location", s2)
        self.matches(r"last-known (city|location).*(on your device|stored on your device)", s2)
        self.matches(r"only the city and country.*AlAdhan|AlAdhan.*only the city and country", s2)
        self.has("Apple MapKit", self.flat)
        self.lacks("rather than your raw coordinates")

    # Undisclosed items
    def test_recitation_audio_hosts_disclosed(self):
        s2 = self.section(2)
        self.has("everyayah.com", s2)
        self.matches(r"everyayah\.com.*IP address", s2)

    def test_firebase_services_that_run_from_launch(self):
        s2 = self.section(2)
        for term in ("Firebase Installations", "App Check", "Cloud Messaging"):
            self.has(term, s2)
        self.matches(r"(?i)not (switched off|controlled) by (any )?(analytics|consent)", s2)

    def test_analytics_user_properties_disclosed(self):
        s2 = self.section(2)
        self.matches(r"user properties such as .*premium.*language.*install cohort", s2)

    def test_unity_ad_quality_disclosed_on_both_platforms(self):
        self.has("Ad Quality", text_of(android_block()))
        self.matches(r"Ad Quality", self.section(9))

    def test_ios_stable_client_id_and_moderation(self):
        s9 = self.section(9)
        self.has("Keychain", s9)
        self.matches(r"(?i)survive[s]? (deleting and reinstalling|reinstall)", s9)
        self.has("omni-moderation", s9)
        self.matches(r"(?i)moderation.*(your message|messages).*(repl(y|ies)|responses)", s9)

    def test_ai_is_premium_only_and_special_category(self):
        s2 = self.section(2)
        self.matches(r"(?i)AI assistant is (available only to|only available to) premium subscribers", s2)
        self.matches(r"(?i)religious beliefs.*special[- ]category", self.flat)
        self.matches(r"(?i)optional.*only when you choose to send a message", self.flat)
        self.matches(r"(?i)explicit action", self.flat)
        self.matches(r"Android.*notice.*accept.*before your first (AI )?message", self.flat)
        self.matches(r"iOS.*does not show a separate AI consent", self.flat)

    def test_ios_attribution_before_att_is_disclosed(self):
        self.has("AdServices", self.section(4))
        self.matches(r"before (you answer|the) (the )?ATT prompt", self.section(4))
        self.matches(r"(?i)AppsFlyer ID.*RevenueCat.*(at launch|when the app (starts|launches))", self.section(4))
        self.lacks("before starting these advertising and attribution SDKs, we show")

    def test_ios_firebase_not_described_as_non_tracking(self):
        self.lacks("they are not used by us to track you across other companies")
        self.has("privacy manifest", self.section(4))
        self.has("tracking domains", self.section(4))
        self.matches(r"ATT.*(is not|not) (GDPR|legal) consent", self.flat)

    def test_cloud_function_logs_and_retention(self):
        s9 = self.section(9)
        self.matches(r"Cloud Functions.*logs.*Firebase UID", s9)
        self.matches(r"30 days", s9)

    def test_skies_free_itunes_lookup_and_mapkit(self):
        s9 = self.section(9)
        self.has("itunes.apple.com", s9)
        self.has("MapKit", s9)

    def test_international_transfers_section(self):
        s9 = self.section(9)
        self.has("International Data Transfers", HTML)
        self.matches(r"United States", s9)
        self.matches(r"rely on the safeguards .*such as", s9)
        self.has("Standard Contractual Clauses", s9)
        self.has("Data Privacy Framework", s9)
        self.lacks("certified under the EU-US Data Privacy Framework")

    def test_legal_basis_interim_android_text(self):
        s5 = self.section(5)
        for phrase in ("Google Play closed testing", "Unity LevelPlay", "AppsFlyer",
                       "Google-certified consent management platform",
                       "Do not sell or share my personal information",
                       "EEA, UK or Switzerland"):
            self.has(phrase, s5)
        self.matches(r"(?i)iOS.*ATT.*controls.*IDFA.*personali[sz]ed ads", s5)
        self.matches(r"(?i)we are adding a consent prompt for (users in the )?EEA", s5)

    def test_section8_covers_both_platforms(self):
        s8 = self.section(8)
        self.matches(r"(?i)iOS.*IDFA.*only if you allow", s8)

    def test_no_em_dashes_in_legal_pages(self):
        self.lacks("\u2014", HTML)
        self.lacks("\u2014", TERMS)
        self.lacks("&mdash;", HTML)

    def test_terms_do_not_claim_blanket_consent(self):
        flat = text_of(TERMS)
        self.lacks("you consent to the collection and use of your information as described", flat)
        self.has("Last updated: October 4, 2026", flat)


if __name__ == "__main__":
    unittest.main()
