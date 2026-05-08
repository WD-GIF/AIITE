"""Unit tests for Crossref normalization (no network)."""

from __future__ import annotations

import unittest

from literature.crossref import normalize_doi_input, work_to_reference_dict


class TestNormalizeDoi(unittest.TestCase):
    def test_strip_doi_org_prefix(self) -> None:
        self.assertEqual(
            normalize_doi_input("https://doi.org/10.1234/foo.bar"),
            "10.1234/foo.bar",
        )
        self.assertEqual(
            normalize_doi_input("http://dx.doi.org/10.1234/foo.bar"),
            "10.1234/foo.bar",
        )


class TestWorkToReference(unittest.TestCase):
    def test_minimal_work(self) -> None:
        work = {
            "title": ["Example Paper"],
            "author": [{"given": "A", "family": "Smith"}],
            "issued": {"date-parts": [[2020, 3, 1]]},
            "container-title": ["Journal of Examples"],
            "DOI": "10.1000/xyz",
            "type": "journal-article",
        }
        ref = work_to_reference_dict(work, ref_id=7)
        self.assertEqual(ref["id"], 7)
        self.assertEqual(ref["authors"], ["A Smith"])
        self.assertEqual(ref["title"], "Example Paper")
        self.assertEqual(ref["year"], 2020)
        self.assertEqual(ref["venue"], "Journal of Examples")
        self.assertEqual(ref["doi"], "10.1000/xyz")
        self.assertEqual(ref["url"], "https://doi.org/10.1000/xyz")

    def test_landing_url_prefers_doi_resolver(self) -> None:
        work = {
            "title": ["T"],
            "author": [],
            "DOI": "10.1000/abc",
            "link": [
                {
                    "URL": "https://publisher.example/paper.pdf",
                    "content-type": "application/pdf",
                }
            ],
        }
        ref = work_to_reference_dict(work, ref_id=1)
        self.assertEqual(ref["url"], "https://doi.org/10.1000/abc")


if __name__ == "__main__":
    unittest.main()
