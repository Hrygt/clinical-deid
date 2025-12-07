---
license: apache-2.0
language:
- en
library_name: transformers
tags:
- medical
- clinical
- ner
- de-identification
- phi
- hipaa
- healthcare
- token-classification
datasets:
- nvidia/Nemotron-PII
base_model: yikuan8/Clinical-Longformer
metrics:
- f1
- precision
- recall
pipeline_tag: token-classification
---

# Clinical-Deid: Clinical Text De-identification

**97.74% F1** on PHI detection — outperforms AWS Comprehend Medical (83%) and John Snow Labs (96%)

## Model Description

Clinical-Deid is a fine-tuned [Clinical-Longformer](https://huggingface.co/yikuan8/Clinical-Longformer) model for detecting and removing Protected Health Information (PHI) from clinical notes. It uses BILOU tagging to identify 25 PHI entity types.

### Key Features

- 🎯 **97.74% F1 Score** — State-of-the-art accuracy
- 📄 **4,096 token context** — Handle full clinical notes
- 🏥 **25 PHI categories** — All HIPAA identifiers covered
- ⚡ **Fast inference** — ~100ms per note on GPU

## Performance

| Metric | Value |
|--------|-------|
| **F1 Score** | 97.74% |
| **Precision** | 96.08% |
| **Recall** | 99.46% |

### Comparison

| Solution | F1 Score | Cost/1M Notes |
|----------|----------|---------------|
| GPT-4o | 79% | $21,400 |
| AWS Comprehend Medical | 83% | $14,525 |
| Azure Health Services | 91% | $13,125 |
| John Snow Labs | 96% | $2,500 |
| **Clinical-Deid** | **97.74%** | **$0** |

## Usage

```python
from transformers import AutoModelForTokenClassification, AutoTokenizer
import torch

# Load model
model = AutoModelForTokenClassification.from_pretrained("riggsmedai/clinical-deid")
tokenizer = AutoTokenizer.from_pretrained("riggsmedai/clinical-deid")

# Example clinical note
text = """
PROGRESS NOTE
Patient: John Smith  DOB: 03/15/1952  MRN: 123456789
Dr. Sarah Johnson evaluated the patient today.
Assessment: 72 year old male with pneumonia.
"""

# Tokenize and predict
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=4096)
with torch.no_grad():
    outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=-1)[0]

# Get labels
id2label = model.config.id2label
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

for token, pred in zip(tokens, predictions):
    label = id2label[pred.item()]
    if label != "O":
        print(f"{token}: {label}")
```

## PHI Categories Detected

| Category | BILOU Labels |
|----------|--------------|
| Names | B/I/L/U-name |
| Dates | B/I/L/U-date |
| Ages | B/I/L/U-age |
| Addresses | B/I/L/U-address |
| Phone Numbers | B/I/L/U-phone_number |
| Email | B/I/L/U-email |
| SSN | B/I/L/U-social_security_number |
| MRN | B/I/L/U-medical_record_number |
| ... and 17 more | |

Total: 101 labels (25 entity types × 4 BILOU tags + O)

## Training Details

- **Base model**: yikuan8/Clinical-Longformer
- **Training data**: NVIDIA Nemotron-PII healthcare subset (3,630 records)
- **Epochs**: 10
- **Best checkpoint**: Epoch 10
- **Hardware**: NVIDIA RTX 5090 (32GB VRAM)

## Limitations

1. **Trained on synthetic data** — Real-world F1 may be 90-95%
2. **English only** — Not tested on other languages
3. **US healthcare focus** — May miss international formats

## Citation

```bibtex
@software{clinical_deid_2025,
  author = {Riggs, Gary},
  title = {Clinical-Deid: Clinical Text De-identification},
  year = {2025},
  url = {https://huggingface.co/riggsmedai/clinical-deid}
}
```

## License

Apache 2.0 — See [COMMERCIAL_LICENSE.md](https://github.com/riggsmedai/clinical-deid/blob/main/COMMERCIAL_LICENSE.md) for commercial use terms.

## Links

- **GitHub**: [github.com/riggsmedai/clinical-deid](https://github.com/riggsmedai/clinical-deid)
- **API**: [deid.riggsmedai.com](https://deid.riggsmedai.com)
- **Contact**: riggsmed@gmail.com
