import pytest
import textwrap
from generator import load_spec, generate, _validate_spec, render_control


MINIMAL_SPEC = {
    "meta": {"standard": "ISO/IEC 42001:2023", "title": "Test Checklist", "version": "0.1"},
    "sections": [
        {
            "clause": "5",
            "title": "Leadership",
            "controls": [
                {
                    "id": "5.1",
                    "title": "Leadership and commitment",
                    "ref": "ISO/IEC 42001:2023, cl. 5.1",
                    "checks": [
                        {
                            "text": "AI policy is signed by top management",
                            "evidence_hint": "Signed policy document",
                        },
                        "Roles and responsibilities for AI governance are assigned",
                    ],
                }
            ],
        }
    ],
}


def test_generate_contains_standard_name():
    md = generate(MINIMAL_SPEC)
    assert "ISO/IEC 42001:2023" in md


def test_generate_contains_clause_heading():
    md = generate(MINIMAL_SPEC)
    assert "## Clause 5: Leadership" in md


def test_generate_check_row_in_table():
    md = generate(MINIMAL_SPEC)
    assert "AI policy is signed by top management" in md
    assert "[ ]" in md


def test_generate_evidence_hint_in_table():
    md = generate(MINIMAL_SPEC)
    assert "Signed policy document" in md


def test_clause_filter_keeps_only_requested_clause():
    spec = {
        "sections": [
            {
                "clause": "4",
                "title": "Context",
                "controls": [{"id": "4.1", "title": "Context", "checks": ["Check A"]}],
            },
            {
                "clause": "5",
                "title": "Leadership",
                "controls": [{"id": "5.1", "title": "Leadership", "checks": ["Check B"]}],
            },
        ]
    }
    md = generate(spec, clause_filter="5")
    assert "Check B" in md
    assert "Check A" not in md
    assert "Clause 4" not in md


def test_validate_spec_raises_on_missing_sections():
    with pytest.raises(ValueError, match="sections"):
        _validate_spec({})


def test_validate_spec_raises_on_control_without_checks():
    bad = {
        "sections": [
            {
                "clause": "5",
                "title": "Leadership",
                "controls": [{"id": "5.1", "title": "No checks", "checks": []}],
            }
        ]
    }
    with pytest.raises(ValueError, match="no checks"):
        _validate_spec(bad)


def test_load_spec_from_sample_file():
    spec = load_spec("sample_controls.yaml")
    assert "sections" in spec
    assert len(spec["sections"]) >= 6


def test_render_control_pipe_escaping():
    ctrl = {
        "id": "4.1",
        "title": "Test",
        "checks": [{"text": "A | B check", "evidence_hint": "Doc | section"}],
    }
    md = render_control(ctrl)
    assert "A \\| B check" in md
    assert "Doc \\| section" in md
