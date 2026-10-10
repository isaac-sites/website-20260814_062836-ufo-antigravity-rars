"""Falsifier for the ufo-death-claims permalink collision cure.

Before the cure, three permalinks were claimed by six documents:
``/death-records/`` by two leaf articles (a *leaf-leaf* collision), and two
``ufo-and-antigravity-1a6484`` truncated slugs by two ``*_index.md``
documents each. The cure keeps each shared route's live winner, gives the
shadowed leaf a ``-<basename frag>`` suffix per the content-page law, and
gives each shadowed index a ``-<index title>`` suffixed permalink. Body and
nav links attributed to the shadowed leaf were retargeted by link-text
identity.
"""
import io
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
PERMALINK = re.compile(r"^permalink:\s*[\"']?([^\s\"'#]+)[\"']?\s*$", re.M)


def page_permalinks():
    out = {}
    for p in PAGES.glob("*.md"):
        m = FRONT_MATTER.match(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        pm = PERMALINK.search(m.group(1))
        if pm:
            out[p.name] = pm.group(1)
    return out


SHARED_SLUGS = {
    "/death-records/",
    "/ufo-and-antigravity-1a6484/",
    "/ufo-and-antigravity-1a6484-research/",
}

EXPECTED_CURED = {
    "/death-records-608437/",
    "/ufo-and-antigravity-1a6484-contemporary-records/",
    "/ufo-and-antigravity-1a6484-research-field-drift/",
}


class TestPermalinkUniqueness(unittest.TestCase):
    def test_all_permalinks_unique(self):
        pls = page_permalinks()
        counts = Counter(pls.values())
        dups = {k: v for k, v in counts.items() if v > 1}
        owners = {k: sorted(n for n, v in pls.items() if v == k) for k in dups}
        self.assertEqual({}, owners)

    def test_shared_slugs_claimed_by_one_document(self):
        pls = page_permalinks()
        for slug in SHARED_SLUGS:
            owners = sorted(n for n, v in pls.items() if v == slug)
            self.assertEqual(1, len(owners), f"{slug} claimed by {owners}")

    def test_expected_cured_routes_exist(self):
        pls = set(page_permalinks().values())
        self.assertEqual(set(), EXPECTED_CURED - pls)

    def test_ning_li_links_point_at_cured_leaf(self):
        # Links whose heading is the shadowed leaf's title must target the
        # cured route; links to the Amy Eskridge winner keep /death-records/.
        ning_bad, amy_bad = [], []
        for p in PAGES.glob("*.md"):
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if "'/death-records" not in ln:
                    continue
                if "Ning Li" in ln and "'/death-records-608437/'" not in ln:
                    ning_bad.append((p.name, ln.strip()[:80]))
                if "Amy Eskridge" in ln and "'/death-records-608437/'" in ln:
                    amy_bad.append((p.name, ln.strip()[:80]))
        self.assertEqual([], ning_bad)
        self.assertEqual([], amy_bad)

    def test_nav_death_records_entry_points_at_cured_leaf(self):
        nav = (ROOT / "_data" / "navigation.yml").read_text(encoding="utf-8")
        for m in re.finditer(r"title_full: ([^\n]*)\n\s*url: (/death-records[^\n]*)", nav):
            if "Ning Li" in m.group(1):
                self.assertEqual("/death-records-608437/", m.group(2).strip())

    def test_manifest_canonical_urls_for_cured_entries(self):
        manifest = json.loads(io.open(ROOT / "phoenix-manifest.json", encoding="utf-8").read())
        cured = {
            "ufo-and-antigravity-1a6484-family-testimony-569-522999-ning-li-death-record-608437": "/death-records-608437/",
            "ufo-and-antigravity-1a6484-research-field-drift-4cd429:index": "/ufo-and-antigravity-1a6484-research-field-drift/",
            "ufo-and-antigravity-1a6484-contemporary-vs-late-69fa7b:index": "/ufo-and-antigravity-1a6484-contemporary-records/",
        }
        bad = []
        for page in manifest.get("pages", []):
            lid = page.get("logical_id")
            if lid in cured:
                route = "/" + (page.get("canonical_url") or "").split("/")[-2] + "/"
                if route != cured[lid]:
                    bad.append((lid, route, cured[lid]))
        self.assertEqual([], bad)


if __name__ == "__main__":
    unittest.main()
