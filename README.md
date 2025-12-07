# Clinical-Deid

**Open-source clinical text de-identification using fine-tuned Clinical-Longformer**

[![F1 Score](https://img.shields.io/badge/F1%20Score-97.74%25-brightgreen)](https://github.com/riggsmedai/clinical-deid)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)

---

## Overview

Clinical-Deid is a high-performance PHI (Protected Health Information) de-identification model that detects and removes personal identifiers from clinical notes. Built on Clinical-Longformer and fine-tuned on NVIDIA's Nemotron-PII dataset, it achieves **97.74% F1 score** — outperforming commercial solutions like AWS Comprehend Medical (83%) and John Snow Labs (96%).

### Key Features

- 🎯 **97.13% F1** — State-of-the-art accuracy on PHI detection
- 📄 **4,096 token context** — Handle full clinical notes without chunking
- 🏥 **25 PHI categories** — All HIPAA identifiers covered
- 🔓 **Open weights** — Download and run locally, no API fees
- ⚡ **Fast inference** — ~100ms per note on GPU
- 🔄 **Multiple output modes** — Redact, replace with surrogates, or extract spans

---

## Performance Comparison

| Solution | F1 Score | Cost per 1M Notes | Open Source |
|----------|----------|-------------------|-------------|
| GPT-4o | 79% | $21,400 | ❌ |
| AWS Comprehend Medical | 83% | $14,525 | ❌ |
| Azure Health Services | 91% | $13,125 | ❌ |
| John Snow Labs | 96% | $2,500 (self-host) | Partial |
| **Clinical-Deid** | **97.74%** | **$0** | ✅ |

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/riggsmedai/clinical-deid.git
cd clinical-deid

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install torch transformers datasets pandas seqeval faker tqdm
```

### Download Model Weights

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="riggsmedai/clinical-deid",
    local_dir="checkpoints/best_model"
)
```

### Basic Usage

```python
from deid import ClinicalDeidentifier

# Initialize
deid = ClinicalDeidentifier("checkpoints/best_model")

# De-identify a clinical note
note = """
PROGRESS NOTE
Patient: John Smith  DOB: 03/15/1952  MRN: 123456789
Dr. Sarah Johnson evaluated the patient today.
Phone: 405-555-1234. Email: john.smith@email.com

Assessment: 72 year old male with community-acquired pneumonia.
"""

# Option 1: Redact with placeholders
redacted = deid.deidentify(note, mode="redact")
# Output: "Patient: [NAME]  DOB: [DATE]  MRN: [ID]..."

# Option 2: Replace with realistic surrogates
replaced = deid.deidentify(note, mode="replace")
# Output: "Patient: Robert Jones  DOB: 07/22/1948  MRN: 987654321..."

# Option 3: Get span annotations
spans = deid.deidentify(note, mode="spans")
# Output: [{"start": 18, "end": 28, "type": "name", "text": "John Smith"}, ...]
```

---

## PHI Categories Detected

Clinical-Deid detects all 18 HIPAA Safe Harbor identifiers plus additional categories:

| Category | Examples |
|----------|----------|
| Names | Patient names, provider names, family members |
| Dates | DOB, admission dates, procedure dates |
| Ages | When >89 years old |
| Addresses | Street, city, state, ZIP code |
| Phone/Fax | All phone number formats |
| Email | Email addresses |
| SSN | Social Security Numbers |
| MRN | Medical Record Numbers |
| Health Plan IDs | Insurance member IDs |
| Account Numbers | Billing account numbers |
| License Numbers | DEA, NPI, driver's license |
| Vehicle IDs | License plates, VINs |
| Device IDs | Serial numbers, UDIs |
| URLs | Web addresses |
| IP Addresses | Network identifiers |
| Biometric IDs | Fingerprints, retinal scans |
| Photos | Full-face photographs |

---

## Model Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Clinical-Longformer                     │
│            (yikuan8/Clinical-Longformer)                │
│         Pretrained on MIMIC-III clinical notes          │
│              148M parameters, 4096 context              │
├─────────────────────────────────────────────────────────┤
│              Token Classification Head                   │
│                    101 classes                          │
│        (25 PHI types × 4 BILOU tags + O)               │
└─────────────────────────────────────────────────────────┘
```

### BILOU Tagging Scheme

- **B** - Beginning of entity
- **I** - Inside of entity  
- **L** - Last token of entity
- **O** - Outside (not PHI)
- **U** - Unit (single-token entity)

Example:
```
Token:  "Dr."  "Sarah"  "Johnson"  "evaluated"  "the"  "patient"
Label:   O    B-NAME    L-NAME        O          O        O
```

---

## Training

### Prerequisites

- NVIDIA GPU with 16GB+ VRAM (tested on RTX 5090)
- CUDA 12.x
- Python 3.10+

### Train Your Own Model

```bash
# 1. Download training data
python download.py

# 2. Preprocess to BILOU format
python preprocess.py

# 3. Train
python train.py --epochs 10 --batch_size 4 --lr 5e-5

# Model saved to checkpoints/best_model/
```

### Training Configuration

| Parameter | Value |
|-----------|-------|
| Epochs | 10 |
| Batch Size | 4 |
| Learning Rate | 5e-5 |
| Warmup Steps | 726 (1 epoch) |
| Optimizer | AdamW |
| Scheduler | Linear with warmup |
| Class Weighting | Inverse frequency |

---

## API Service

We also offer a hosted API for those who prefer not to self-host:

```bash
curl -X POST https://deid.riggsmedai.com/api/process \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient John Smith DOB 03/15/1952...", "mode": "redact"}'
```

### Pricing

| Tier | Price | Notes/Month |
|------|-------|-------------|
| Free | $0 | 100 |
| Starter | $49/mo | 5,000 |
| Pro | $199/mo | 50,000 |
| Enterprise | Custom | Unlimited |

---

## Validation

### Synthetic Data (Nemotron-PII Healthcare)
- **F1:** 97.74%
- **Precision:** 96.08%
- **Recall:** 99.46%

### External Validation (Planned)
- i2b2 2014 De-identification Challenge
- PhysioNet Gold Standard Corpus
- Real clinical notes (IRB pending)

---

## 🔬 Help Us Validate

We've achieved **97.74% F1** on our held-out synthetic data, but real-world validation requires datasets we don't have immediate access to.

**If you have access to any of these datasets, we'd love your help:**

| Dataset | Access | What We Need |
|---------|--------|--------------|
| **i2b2/n2c2 2014 De-identification** | [DBMI Portal](https://portal.dbmi.hms.harvard.edu/) | Run our model, report F1/precision/recall |
| **PhysioNet Gold Standard** | [PhysioNet](https://physionet.org/content/deidentifiedmedicaltext/) (CITI required) | Pair with Google Health annotations |
| **N-GRID 2016** | DUA required | Psychiatric note evaluation |
| **MIMIC-III Clinical Notes** | [PhysioNet](https://physionet.org/content/mimiciii/) (CITI required) | Real ICU note testing |

### How to Contribute Validation Results

1. Clone repo and load model
2. Run evaluation on your dataset (see `evaluate.py`)
3. Submit results via:
   - GitHub Issue with metrics (no PHI!)
   - Pull request to `VALIDATION_RESULTS.md`
   - Email: riggsmed@gmail.com

### What to Report

```
Dataset: [name]
Split: Test set (n=XXX notes)
Results:
  - Precision: X.XX
  - Recall: X.XX  
  - F1: X.XX
  - Per-entity breakdown (optional)
Notes: Any observations about failure modes
```

**We'll acknowledge all contributors in the README and any resulting publications.**

### Current Validation Status

| Dataset | F1 | Precision | Recall | Contributor |
|---------|-----|-----------|--------|-------------|
| Nemotron-PII (held-out) | 97.74% | 96.08% | 99.46% | @riggsmedai |
| i2b2 2014 | — | — | — | *Seeking contributor* |
| PhysioNet Gold | — | — | — | *Seeking contributor* |
| Real clinical notes | — | — | — | *IRB pending* |

---

## Limitations

1. **Trained on synthetic data** — Real-world performance may vary (estimated 90-95% F1)
2. **English only** — Not tested on other languages
3. **US healthcare focus** — May miss international identifier formats
4. **No guaranteed HIPAA compliance** — Expert review recommended for regulatory use

---

## Citation

If you use Clinical-Deid in your research, please cite:

```bibtex
@software{clinical_deid_2025,
  author = {Riggs, Gary},
  title = {Clinical-Deid: Open-Source Clinical Text De-identification},
  year = {2025},
  url = {https://github.com/riggsmedai/clinical-deid}
}
```

---

## License

This project uses a **dual licensing model**:

### Open Source (Apache 2.0)
Free for:
- ✅ Research and academic use
- ✅ Personal projects
- ✅ Evaluation and testing
- ✅ Internal non-commercial tools

### Commercial License
Required for:
- 💼 Offering de-identification as a paid service
- 💼 Including in commercial products
- 💼 Production use with SLA requirements

See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for details and pricing.

### Third-Party Licenses
- Clinical-Longformer: Apache 2.0
- Nemotron-PII Dataset: CC BY 4.0

---

## Acknowledgments

- **NVIDIA** for the Nemotron-PII dataset
- **Yikuan8** for Clinical-Longformer pretrained weights
- **Anthropic Claude** for development assistance

---

## Contact

**Gary Riggs, MD**  
RIGGSMED LLC  
- Website: [riggsmedai.com](https://riggsmedai.com)
- API: [deid.riggsmedai.com](https://deid.riggsmedai.com)
- Email: riggsmed@gmail.com

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

Areas we'd love help with:
- External dataset validation
- Multi-language support
- Performance optimization
- Documentation improvements
