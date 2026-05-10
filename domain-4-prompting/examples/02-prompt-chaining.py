"""Prompt chaining vs single mega-prompt — show the accuracy gap.

CCA-F trap: stuffing a 5-step pipeline into one giant prompt because "the
context window is huge anyway." Doesn't matter — model attention degrades
with task count per turn. Chain narrow prompts instead.

Pipeline (extract → normalize → validate → enrich):
  1. EXTRACT — pull raw fields from a free-form medical note
  2. NORMALIZE — map drug names to a canonical RxNorm-like list
  3. VALIDATE — flag impossible values (negative dose, future date)
  4. ENRICH — add ICD-10 codes for diagnoses

Run: uv run domain-4-prompting/examples/02-prompt-chaining.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.client import client


NOTE = """\
Pt: J. Smith, 47M. Seen 2026-04-12 for hypertension f/u.
Takes lisnoprl 10mg daily, atorvastatn 20mg q hs.
BP today 142/91, weight 89 kg. Started on metformin 500mg bid for new T2DM dx.
"""

# Canonical drug list — in real life this is RxNorm; here it's a tiny lookup.
DRUG_CANON = {
    "lisinopril": ["lisinopril", "lisnoprl", "lisinapril"],
    "atorvastatin": ["atorvastatin", "atorvastatn", "atorvastat"],
    "metformin": ["metformin", "metformine", "metaformin"],
}

ICD10 = {
    "hypertension": "I10",
    "type 2 diabetes": "E11.9",
    "t2dm": "E11.9",
}


def call(model: str, system: str, user: str) -> str:
    resp = client.messages.create(
        model=model,
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def parse_json_block(text: str) -> dict:
    # Strip code-fences if model wrapped the JSON.
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


# --- Step 1: EXTRACT --------------------------------------------------------
# Single narrow task: pull fields. Cheaper model is fine.
extracted_text = call(
    "claude-haiku-4-5",
    "Extract clinical fields from the medical note. Return ONLY a JSON object with keys: "
    "patient (string), date (YYYY-MM-DD), medications (list of {name, dose, frequency}), "
    "vitals (object), diagnoses (list of strings). No prose, no code fence.",
    NOTE,
)
extracted = parse_json_block(extracted_text)
print("1. EXTRACT:")
print(json.dumps(extracted, indent=2))


# --- Step 2: NORMALIZE ------------------------------------------------------
# Code does the lookup; we don't ask the LLM to do dictionary lookups it might
# fabricate. This is the M1 "deterministic when possible" mental model.
def canonicalize(name: str) -> str:
    name_lower = name.lower()
    for canon, aliases in DRUG_CANON.items():
        if name_lower in aliases:
            return canon
    return name_lower  # leave unchanged if unknown


for med in extracted["medications"]:
    raw = med["name"]
    med["name_canonical"] = canonicalize(raw)
    if med["name_canonical"] != raw.lower():
        med["normalized_from"] = raw

print("\n2. NORMALIZE:")
print(json.dumps(extracted["medications"], indent=2))


# --- Step 3: VALIDATE -------------------------------------------------------
# Programmatic checks first; if anything fails we DON'T proceed to step 4.
validation_errors = []
for med in extracted["medications"]:
    dose_str = str(med.get("dose", ""))
    # super-naive parse — for the example
    if not any(c.isdigit() for c in dose_str):
        validation_errors.append(f"{med['name']}: missing numeric dose ({dose_str!r})")

import re
date_match = re.match(r"^\d{4}-\d{2}-\d{2}$", extracted.get("date", ""))
if not date_match:
    validation_errors.append(f"date format invalid: {extracted.get('date')!r}")

print("\n3. VALIDATE:")
if validation_errors:
    print("  ❌", validation_errors)
    raise SystemExit(1)
print("  ✅ all checks passed")


# --- Step 4: ENRICH ---------------------------------------------------------
# Hybrid: dict lookup for known dx, fall back to LLM for the rest.
enriched_dx = []
unknown = []
for dx in extracted["diagnoses"]:
    code = ICD10.get(dx.lower())
    if code:
        enriched_dx.append({"diagnosis": dx, "icd10": code, "source": "lookup"})
    else:
        unknown.append(dx)

if unknown:
    enrichment = call(
        "claude-sonnet-4-6",
        "For each diagnosis term, return the most likely ICD-10 code. JSON only: "
        "{<term>: <code>}. No prose.",
        json.dumps(unknown),
    )
    for term, code in parse_json_block(enrichment).items():
        enriched_dx.append({"diagnosis": term, "icd10": code, "source": "llm"})

extracted["diagnoses_enriched"] = enriched_dx
print("\n4. ENRICH:")
print(json.dumps(enriched_dx, indent=2))

print("\n=== Why chain instead of one prompt ===")
print(
    "- Each step has a narrow output → easier to validate and retry just that step\n"
    "- Cheap model on extraction, expensive only where reasoning helps\n"
    "- Code wins where deterministic (canonicalize, regex date check) — saves tokens\n"
    "- A failure in step 3 doesn't waste the step 4 LLM call"
)
