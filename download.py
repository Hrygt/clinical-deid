# download.py (with debug)
from datasets import load_dataset
import json
import ast
from pathlib import Path
from collections import Counter

print("Downloading Nemotron-PII dataset...")
ds = load_dataset("nvidia/Nemotron-PII", split="train")
print(f"Total records: {len(ds):,}")

# Filter for healthcare
healthcare = ds.filter(lambda x: x['domain'] == 'Healthcare')
print(f"Healthcare records: {len(healthcare):,}")

# Check document types
doc_types = Counter(healthcare['document_type'])
print("\nHealthcare document types:")
for dt, count in doc_types.most_common():
    print(f"  {dt}: {count}")

# Debug: see what spans actually looks like
print(f"\nDebug - spans type: {type(healthcare[0]['spans'])}")
print(f"Debug - spans sample: {healthcare[0]['spans'][:200]}...")

# Check entity labels - try ast.literal_eval for Python-style strings
all_labels = set()
for record in healthcare:
    spans = record['spans']
    if isinstance(spans, str):
        spans = ast.literal_eval(spans)
    for span in spans:
        all_labels.add(span['label'])

print(f"\nEntity labels ({len(all_labels)} types):")
for label in sorted(all_labels):
    print(f"  {label}")

# Save healthcare subset
output_path = Path("data/nemotron_healthcare.jsonl")
output_path.parent.mkdir(exist_ok=True)

with open(output_path, "w") as f:
    for record in healthcare:
        spans = record['spans']
        if isinstance(spans, str):
            spans = ast.literal_eval(spans)
        row = {
            "uid": record["uid"],
            "domain": record["domain"],
            "document_type": record["document_type"],
            "text": record["text"],
            "spans": spans,
        }
        f.write(json.dumps(row) + "\n")

print(f"\nSaved to {output_path}")