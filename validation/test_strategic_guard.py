"""Offline tests for the res strategic-mode guard (res SPEC §2.2, §3.2, D4, §10).

No third-party deps, no network. Run with:
    python3 -m unittest discover -s validation -p 'test_*.py'   # from repo root
    cd validation && python3 -m unittest test_strategic_guard -v
"""

import unittest

from strategic_guard import (
    ResearchDocumentFacts,
    check,
    looks_like_code_reference,
)


class TestCodeReferenceHeuristic(unittest.TestCase):
    def test_flags_repo_at_commit_with_path_and_lines(self):
        self.assertTrue(looks_like_code_reference("acme/widgets @ a1b2c3d server/handler.py:L10-L42"))

    def test_flags_plain_code_path_with_line_ref(self):
        self.assertTrue(looks_like_code_reference("src/server.py:L10"))

    def test_flags_bare_code_path(self):
        self.assertTrue(looks_like_code_reference("pkg/main.go"))

    def test_flags_repo_at_commit(self):
        self.assertTrue(looks_like_code_reference("acme/widgets @ a1b2c3d4e5f6"))

    def test_allows_arxiv_paper(self):
        self.assertFalse(looks_like_code_reference(
            "Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762"))

    def test_allows_plain_web_url(self):
        self.assertFalse(looks_like_code_reference(
            "State of AI Report — https://example.com/report.html (accessed 2026-06-03)"))

    def test_allows_pdf_and_md(self):
        self.assertFalse(looks_like_code_reference("https://example.com/paper.pdf"))
        self.assertFalse(looks_like_code_reference("notes/summary.md"))

    def test_allows_planning_tier_repo_issue_ref(self):
        # `owner/repo issue #N` is a planning-tier citation, NOT a code path.
        self.assertFalse(looks_like_code_reference("owner/repo issue #47"))

    def test_allows_mission_section(self):
        self.assertFalse(looks_like_code_reference("MISSION §Success looks like"))

    def test_flags_vcs_blob_url_to_code(self):
        # A web link is normally allowed, but a blob/raw link to a code file is caught.
        self.assertTrue(looks_like_code_reference(
            "https://github.com/acme/widgets/blob/main/server/handler.py"))
        self.assertTrue(looks_like_code_reference(
            "https://github.com/acme/widgets/blob/main/server/handler.py#L10"))

    def test_allows_vcs_blob_url_to_doc(self):
        # A blob link to a non-code file (README.md) is not a code reference.
        self.assertFalse(looks_like_code_reference(
            "https://github.com/acme/widgets/blob/main/README.md"))

    def test_empty_is_not_code(self):
        self.assertFalse(looks_like_code_reference("   "))


class TestStrategicContract(unittest.TestCase):
    def test_clean_strategic_doc_passes(self):
        doc = ResearchDocumentFacts(
            "strategic", code_read=False,
            citations=(
                "Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762",
                "https://example.com/report.html (accessed 2026-06-03)",
                "owner/repo issue #47",
                "MISSION §Success looks like",
            ),
        )
        r = check(doc)
        self.assertTrue(r.ok, r.violations)
        self.assertEqual(r.violations, ())

    def test_strategic_doc_citing_code_fails(self):
        doc = ResearchDocumentFacts(
            "strategic", code_read=False,
            citations=("acme/widgets @ a1b2c3d server/handler.py:L10-L42",),
        )
        r = check(doc)
        self.assertFalse(r.ok)
        self.assertEqual(len(r.violations), 1)
        self.assertIn("code reference", r.violations[0])

    def test_strategic_doc_with_code_read_true_fails(self):
        doc = ResearchDocumentFacts("strategic", code_read=True)
        r = check(doc)
        self.assertFalse(r.ok)
        self.assertIn("code-read: true", r.violations[0])

    def test_strategic_footprint_with_code_path_fails(self):
        doc = ResearchDocumentFacts(
            "strategic", code_read=False,
            citations=(),
            footprint_paths=("notes/landscape-2026-06-03.md", "src/leaked.py"),
        )
        r = check(doc)
        self.assertFalse(r.ok)
        self.assertTrue(any("footprint" in v for v in r.violations))

    def test_strategic_accumulates_multiple_violations(self):
        doc = ResearchDocumentFacts(
            "strategic", code_read=True,
            citations=("src/a.py:L1", "pkg/b.go"),
        )
        r = check(doc)
        self.assertFalse(r.ok)
        self.assertEqual(len(r.violations), 3)  # code_read + 2 code citations


class TestTechnicalContract(unittest.TestCase):
    def test_technical_doc_citing_code_passes(self):
        doc = ResearchDocumentFacts(
            "technical", code_read=True,
            citations=("acme/widgets @ a1b2c3d server/handler.py:L10-L42",),
        )
        r = check(doc)
        self.assertTrue(r.ok, r.violations)

    def test_technical_doc_citing_code_but_code_read_false_is_inconsistent(self):
        doc = ResearchDocumentFacts(
            "technical", code_read=False,
            citations=("src/server.py:L10",),
        )
        r = check(doc)
        self.assertFalse(r.ok)
        self.assertIn("code-read: false", r.violations[0])


class TestValidation(unittest.TestCase):
    def test_bad_mode_rejected(self):
        with self.assertRaises(ValueError):
            ResearchDocumentFacts("hybrid", code_read=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
