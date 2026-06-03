"""Offline tests for the research-document adapter (res SPEC §2.1/§2.3, §3).

No third-party deps. Run with:
    python3 -m unittest discover -s validation -p 'test_*.py'   # from repo root
"""

import unittest

from document import parse_document, check_document, extract_section


CLEAN = """---
doc-id: 2026-06-03-activation-benchmarks
mode: strategic
caller: dir
code-read: false
---
## Question
What activation rate is realistic for B2B onboarding?

## Evidence
- Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762
- State of Onboarding 2025 — https://example.com/report.html (accessed 2026-06-03)
- owner/repo issue #47
"""

LEAKY = """---
mode: strategic
code-read: false
---
## Evidence
- acme/widgets @ a1b2c3d server/handler.py:L10-L42
"""

CODE_READ_TRUE = """---
mode: strategic
code-read: true
---
## Evidence
- A web source — https://example.com (accessed 2026-06-03)
"""

TECHNICAL = """---
mode: technical
caller: eng
code-read: true
---
## Evidence
- acme/widgets @ a1b2c3d server/handler.py:L10-L42
- https://example.com/post.html (accessed 2026-06-03)
"""


class TestParse(unittest.TestCase):
    def test_parses_mode_and_code_read(self):
        facts = parse_document(CLEAN)
        self.assertEqual(facts.mode, "strategic")
        self.assertFalse(facts.code_read)

    def test_parses_citations_from_evidence(self):
        facts = parse_document(CLEAN)
        self.assertEqual(len(facts.citations), 3)
        self.assertIn("arXiv:1706.03762", facts.citations[0])

    def test_code_read_true_parsed(self):
        facts = parse_document(CODE_READ_TRUE)
        self.assertTrue(facts.code_read)

    def test_missing_mode_rejected(self):
        with self.assertRaises(ValueError):
            parse_document("---\ncaller: dir\n---\n## Evidence\n- x\n")

    def test_extract_section_none_when_absent(self):
        self.assertIsNone(extract_section("## Question\nq\n", "Evidence"))


class TestCheckDocument(unittest.TestCase):
    def test_clean_strategic_passes(self):
        r = check_document(CLEAN)
        self.assertTrue(r.ok, r.violations)

    def test_leaky_strategic_fails(self):
        r = check_document(LEAKY)
        self.assertFalse(r.ok)
        self.assertTrue(any("code reference" in v for v in r.violations))

    def test_code_read_true_strategic_fails(self):
        r = check_document(CODE_READ_TRUE)
        self.assertFalse(r.ok)
        self.assertTrue(any("code-read: true" in v for v in r.violations))

    def test_technical_with_code_passes(self):
        r = check_document(TECHNICAL)
        self.assertTrue(r.ok, r.violations)

    def test_strategic_footprint_path_fails(self):
        r = check_document(CLEAN, footprint_paths=("notes/ok.md", "src/leaked.py"))
        self.assertFalse(r.ok)
        self.assertTrue(any("footprint" in v for v in r.violations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
