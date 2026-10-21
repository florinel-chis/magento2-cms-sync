"""
Seed profiles shared by the test fixtures and the standalone server, so the scenario the
tests assert on is the same one a developer sees in the UI.

* ``stock``     the four CMS pages a fresh Magento install ships with
* ``demo``      stock + three blocks + an "about-us" page (the "source")
* ``demo-dest`` stock + a drifted "footer_links_block" + a block only the destination has
"""
from __future__ import annotations

from .app import FakeMagento

PROFILES = ("none", "stock", "demo", "demo-dest")

FOOTER_SOURCE = '<ul><li><a href="/about-us">About us</a></li></ul>'
FOOTER_DEST = '<ul><li><a href="/about">About</a></li></ul>'
CONTACT = "<p>Call us: +40 000 000 000</p>"


def seed_profile(magento: FakeMagento, profile: str, extra_blocks: int = 0) -> None:
    if profile not in PROFILES:
        raise ValueError(f"unknown seed profile {profile!r}; choose from {PROFILES}")
    if profile != "none":
        magento.seed_stock_pages()
    if profile == "demo":
        magento.add_block("footer_links_block", "Footer Links", FOOTER_SOURCE)
        magento.add_block("contact-us-info", "Contact us info", CONTACT)
        magento.add_block("sale_coupon", "Sale coupon", "<p>Use code SPRING for 10% off.</p>")
        magento.add_page("about-us", "About us", "<p>We sell nice things.</p>", content_heading="About us")
    elif profile == "demo-dest":
        magento.add_block("footer_links_block", "Footer Links", FOOTER_DEST)
        magento.add_block("dest_only_block", "Only on destination", "<p>Not present on source.</p>")
    if extra_blocks:
        magento.seed_blocks(extra_blocks, prefix="generated")
