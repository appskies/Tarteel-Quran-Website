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
        # Outdated pin updated: the no-consent statement now applies to earlier test builds only.
        self.matches(r"version code 7 and earlier.*do not show (their own|an in-app) consent", block)
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
        # Outdated pin updated: earlier builds had no prompt, version code 8 and later has one.
        self.matches(r"version code 7 and earlier.*(do not|did not) show (their own|a) consent", s5)
        # Legitimate interests must NOT be claimed for advertising, attribution or analytics.
        self.matches(r"(?i)do not rely on legitimate interests for (advertising|ads)", s5)
        self.assertIsNone(re.search(r"Legitimate interests:[^.]*Improving", s5), "old LI wording")

    def test_section8_sale_statement_is_qualified_for_android(self):
        s8 = self.section(8)
        self.matches(r"Android.*advertising ID.*(sale|sharing)", s8)
        self.matches(r"(CCPA|CPRA|some laws).*(sale|sharing)", s8)

    def test_section10_opt_out_wording_is_qualified_for_android(self):
        s10 = self.section(10)
        # Outdated pin updated: the in-app opt-out now exists from version code 8; earlier builds have none.
        self.matches(r"version code 7 and earlier.*no in-app.*opt-out", s10)
        self.matches(r"(?i)delete your advertising ID", s10)
        self.lacks("we honor recognized opt-out signals where applicable", s10)

    def test_last_updated_bumped(self):
        # Pin updated: October 5 -> October 6, 2026 (AI report paragraph).
        self.has("Last updated: October 6, 2026", text_of(HTML))
        self.lacks("October 5, 2026", text_of(HTML))
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
        self.matches(r"notice.*(iOS|AIProxy).*Android.*accept.*nothing is sent until you accept", self.flat)
        self.matches(r"(?i)declining keeps your draft and sends nothing", self.flat)
        self.matches(r"iOS and Android you also accept a notice before your first message", self.flat)
        self.lacks("does not show a separate AI consent")

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
        # Outdated pin updated: "we are adding" became the actual behaviour (see PrivacyConsentBuilds).
        self.matches(r"(?i)version 1\.0\.15 and later.*consent form", s5)

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


class PrivacyConsentBuilds(unittest.TestCase):
    """The consent controls ship in iOS 1.0.15 and Android version code 8. The policy must be
    true for old and new builds, so every new behaviour is scoped to a version label.
    Evidence (file:line) is in the PR description."""

    flat = text_of(HTML)

    def section(self, n):
        m = re.search(rf"<h2>{n}\. .*?</h2>(.*?)(?=<h2>|</div>\s*</body>)", HTML, re.S)
        return text_of(m.group(1)) if m else ""

    def m(self, pattern, hay=None):
        hay = self.flat if hay is None else hay
        self.assertTrue(re.search(pattern, hay, re.S), f"no match: {pattern!r}")

    def lacks(self, needle, hay=None):
        hay = self.flat if hay is None else hay
        self.assertTrue(needle not in hay, f"must not appear: {needle!r}")

    def test_ai_report_storage_is_disclosed(self):
        body = text_of(HTML)
        self.assertIn("Reporting an AI response", body)
        self.m(r"deleted automatically about 90 days", body)
        self.assertIn("without your Firebase user ID", body)
        self.assertIn("capped at 20 per day", body)
        self.assertIn("except for an AI reply you choose to report", body)

    def test_version_labels_are_defined(self):
        s1 = self.section(1)
        self.m(r"iOS version 1\.0\.15 and later", s1)
        self.m(r"Android version code 8 and later", s1)
        self.m(r"closed testing", s1)

    def test_future_commitments_are_replaced_by_behaviour(self):
        for old in ("Before public release we will add", "we will add a Google-certified",
                    "We are adding a consent prompt", "Until that prompt is released",
                    "does not currently show its own consent", "does not yet show a consent prompt",
                    "currently no in-app opt-out", "does not currently include an in-app switch",
                    "does not use Google's User Messaging Platform"):
            self.lacks(old)

    def test_section4_ump_form_ios_and_android(self):
        s4 = self.section(4)
        for t in ("User Messaging Platform", "Consent", "Do not consent", "Manage options",
                  "EEA, UK and Switzerland"):
            self.assertIn(t, s4)
        self.m(r"iOS version 1\.0\.15 and later.*before any ads, attribution, analytics or crash", s4)
        self.m(r"Android version code 8 and later.*before any ads, attribution, analytics or crash", s4)
        self.m(r"(?i)nothing starts until you answer", s4)
        self.m(r"(?i)fails? closed|nothing starts if the form", s4)
        self.m(r"before the ATT prompt", s4)
        self.m(r"(?i)skips? (the )?ATT.*(declin|do not consent)|(declin|do not consent).*skips? (the )?ATT", s4)

    def test_section4_purpose_mapping_and_sdk_gating(self):
        s4 = self.section(4)
        self.m(r"(?i)purpose 1", s4)
        self.m(r"(?i)purposes? 3 and 4", s4)
        self.m(r"(?i)purpose 7", s4)
        self.m(r"(?i)purpose 9", s4)  # iOS analytics
        self.m(r"LevelPlay.*GDPR consent", s4)
        self.m(r"AppsFlyer.*(DMA|consent) ", s4)
        self.m(r"(?i)consent mode", s4)
        self.m(r"Crashlytics.*(consent)", s4)
        self.m(r"RevenueCat.*(AdServices).*(attribution consent)", s4)

    def test_section4_earlier_versions_still_described(self):
        s4 = self.section(4)
        self.m(r"iOS versions? before 1\.0\.15", s4)
        self.m(r"Android version code 7 and earlier", s4)
        self.m(r"(?i)before (you answer|the) (the )?ATT prompt", s4)  # old iOS behaviour kept

    def test_section4_privacy_choices_and_toggle(self):
        s4 = self.section(4)
        self.m(r"Settings › Privacy choices", s4)
        self.m(r"Settings › Do not sell or share my personal information", s4)
        self.m(r"(?i)on by default", s4)
        self.m(r"(?i)never changed it|did not change it|until you change it", s4)
        self.m(r"(?i)outside the EEA, UK and Switzerland", s4)
        # Both platforms behave the same: an untouched toggle does not override UMP inside consent regions
        self.m(r"(?i)both platforms.*(inside|in) the EEA, UK and Switzerland.*(does not|do not) override", s4)
        self.lacks("Android difference", self.flat)
        self.lacks("starts on in every region", self.flat)

    def test_section4_toggle_effects(self):
        s4 = self.section(4)
        self.m(r"(?i)LevelPlay.*(CCPA|do-not-sell|do not sell)", s4)
        self.m(r"(?i)AppsFlyer.*(stopped|anonymi[sz]ed)", s4)
        self.m(r"(?i)ad storage, ad user data and ad personali[sz]ation.*denied", s4)
        self.m(r"(?i)Firebase Analytics and Crashlytics (still )?(keep )?run(ning)? outside the EEA", s4)

    def test_section5_legal_basis_new_builds(self):
        s5 = self.section(5)
        self.m(r"iOS version 1\.0\.15 and later.*consent form.*(EEA|Switzerland)", s5)
        self.m(r"Android version code 8 and later.*consent form", s5)
        self.m(r"(?i)consent.*(ads|advertising).*(attribution).*(analytics)", s5)
        self.m(r"(?i)withdraw.*Privacy choices", s5)
        self.m(r"ATT.*(is not|not) (GDPR|legal) consent", s5)

    def test_section8_toggle_is_the_opt_out(self):
        s8 = self.section(8)
        self.m(r"Do not sell or share my personal information", s8)
        self.m(r"(?i)on by default", s8)
        self.m(r"(?i)earlier versions.*(no|do not).*(switch|toggle)", s8)

    def test_section10_ccpa_opt_out_in_app(self):
        s10 = self.section(10)
        self.m(r"Opt out:.*Settings › Do not sell or share my personal information", s10)
        self.m(r"iOS version 1\.0\.15 and later and Android version code 8 and later", s10)
        self.m(r"Settings › Privacy choices", s10)

    def test_levelplay_toggle_wording_does_not_overclaim(self):
        s4 = self.section(4)
        self.lacks("ads are not personalized", s4)
        self.m(r"LevelPlay.*passes (that|the) (do-not-sell )?signal to its ad networks.*under their own policies", s4)

    def test_levelplay_gdpr_consent_purposes_per_platform(self):
        s4 = self.section(4)
        self.m(r"iOS version 1\.0\.15 and later.*LevelPlay's GDPR consent[^.]*purposes 1, 3 and 4", s4)
        self.m(r"Android version code 8 and later.*LevelPlay's GDPR consent[^.]*purposes 1, 3, 4 and 7", s4)

    def test_ump_listed_as_third_party_service(self):
        s9 = self.section(9)
        self.m(r"Google User Messaging Platform.*consent form", s9)
        self.m(r"(?i)IP address", s9.split("Google User Messaging Platform")[1][:700])
        self.m(r"(?i)device identifiers.*(form|interaction).*diagnostic", s9.split("Google User Messaging Platform")[1][:700])

    def test_section3_consistent_with_consent(self):
        s3 = self.section(3)
        self.m(r"(?i)Advertising:.*personali[sz]ed ads.*(permit|consent).*(see §4)", s3)
        self.m(r"(?i)Analytics.*(consent)", s3)

    def test_section6_consent_records_stay_on_device(self):
        s6 = self.section(6)
        self.m(r"(?i)consent choices.*(TCF|IAB).*Do not sell or share.*(stored )?on your device", s6)
        self.m(r"(?i)Delete My Data does not (remove|delete) (them|these)", s6)
        self.m(r"(?i)(uninstall|delet\w+ the App).*remove", s6)

    def test_ios_version_label_is_not_1013(self):
        # 1.0.13 is the live build without the consent form; 1.0.14 reverts it.
        self.lacks("1.0.13")
        self.lacks("version code 6")

    def test_no_em_dash_anywhere_new_text(self):
        self.lacks("\u2014")
        self.lacks("&mdash;")
        self.lacks("\u2013")

    def test_markup_still_balanced(self):
        p = _Balance()
        p.feed(HTML)
        self.assertEqual((p.errors, p.stack), ([], []))


if __name__ == "__main__":
    unittest.main()
