# iso-42001-checklist-gen

Generates an auditor-friendly Markdown checklist from a YAML control spec aligned
with ISO/IEC 42001:2023 (AI Management Systems).

## What it does

- Reads a YAML file that describes ISO 42001 controls, grouped by clause.
- Emits a Markdown document with a table of contents, one section per clause,
  and a checklist table per control.
- Each row in a table has columns for: check text, a status checkbox, an evidence
  hint (pre-filled from the spec), and a free-text notes column.
- A `--clause` flag lets you emit only a single clause (useful during phased audits).

The output is designed to be pasted into a wiki or printed as a PDF so an
auditor can tick boxes, record evidence, and note findings during a walkthrough.

## How to run

```bash
pip install -r requirements.txt

# Full checklist to stdout
python generator.py sample_controls.yaml

# Write to a file
python generator.py sample_controls.yaml -o checklist.md

# Single-clause slice (e.g. only clause 8 - Operation)
python generator.py sample_controls.yaml --clause 8
```

## YAML spec format

```yaml
meta:
  standard: "ISO/IEC 42001:2023"
  title:    "My AI Management System Checklist"
  version:  "1.0"
  scope:    "Customer-facing recommendation systems"

sections:
  - clause: "5"
    title:  "Leadership"
    controls:
      - id:    "5.2"
        title: "AI policy"
        ref:   "ISO/IEC 42001:2023, cl. 5.2"
        checks:
          - text: "Policy includes commitment to responsible AI"
            evidence_hint: "AI policy, objectives section"
          - text: "Policy is reviewed annually"
            evidence_hint: "Policy revision history"
```

`checks` entries can be plain strings or `{text, evidence_hint}` mappings.
All fields except `sections[*].clause`, `sections[*].title`, `controls[*].id`,
`controls[*].title`, and `controls[*].checks` are optional.

## Running the tests

```bash
python -m pytest test_generator.py -v
```

9 tests cover: Markdown structure, clause filtering, validation errors, pipe
escaping, and loading the bundled sample spec.

## Findings

- The YAML-to-Markdown approach makes it easy to version-control the control
  spec alongside code and diff it across audit cycles.
- Evidence hints travel with each check, reducing auditor setup time.
- The `--clause` filter is handy for splitting work across audit team members.

## Scope

- Generates static Markdown only; no scoring, no tracking of findings across runs.
- The bundled `sample_controls.yaml` covers clauses 4-10 with a representative
  subset of controls - it is NOT a complete ISO 42001 control set and should not
  be treated as authoritative.
- Does not generate Annex A controls (those require licensing the standard text).

## Out of scope

- PDF rendering (pipe through Pandoc if needed).
- Database or web UI for tracking audit results.
- Automatic mapping from code artefacts to control evidence.
