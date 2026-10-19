"""Regression guard: the contact form's submit button must be styled.

Bug: contact.html uses <button class="btn btn-primary"> but css/style.css only had
`.btn-primary:disabled`, so on production the button rendered as the default grey
browser button (2px outset border) in the middle of the dark teal/gold page.

Run: python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
CONTACT = (ROOT / "contact.html").read_text(encoding="utf-8")


def rule_bodies(selector):
    """Declaration blocks of every top-level rule whose selector list contains `selector` exactly."""
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS):
        parts = [s.strip() for s in sel.split(",")]
        if selector in parts:
            out.append(body)
    return out


class ContactSubmitButton(unittest.TestCase):
    def test_contact_uses_the_button_classes(self):
        self.assertRegex(CONTACT, r'<button type="submit" class="btn btn-primary">')

    def test_btn_primary_has_a_base_style(self):
        bodies = rule_bodies(".btn-primary")
        self.assertTrue(bodies, ".btn-primary has no base rule (only :disabled)")
        joined = " ".join(bodies)
        for prop in ("background", "color", "padding", "border", "border-radius", "cursor"):
            self.assertRegex(joined, rf"(?<![\w-]){prop}\s*:", f".btn-primary lacks {prop}")

    def test_btn_primary_overrides_the_default_outset_border(self):
        joined = " ".join(rule_bodies(".btn-primary"))
        self.assertRegex(joined, r"border\s*:\s*(none|0)")

    def test_disabled_state_is_kept(self):
        self.assertTrue(rule_bodies(".btn-primary:disabled"))


if __name__ == "__main__":
    unittest.main()
