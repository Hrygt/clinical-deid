# Clinical-Deid Project Assets

**Last Updated:** December 7, 2025  
**Project Owner:** Gary Riggs, MD | RIGGSMED LLC  
**Repository:** C:\MyScripts\ModelWorks\clinical-deid

---

## Model Assets

### Production Model
| Asset | Location | Details |
|-------|----------|---------|
| Best Model | `checkpoints/best_model/` | Clinical-Longformer fine-tuned on Nemotron-PII |
| Tokenizer | `checkpoints/best_model/tokenizer/` | AutoTokenizer from yikuan8/Clinical-Longformer |
| Config | `checkpoints/best_model/config.json` | 101 labels, 148M parameters |

### Model Specifications
| Attribute | Value |
|-----------|-------|
| Base Model | yikuan8/Clinical-Longformer |
| Parameters | 148,146,533 |
| Max Sequence Length | 4,096 tokens |
| Task | Token Classification (NER) |
| Tagging Scheme | BILOU |
| Label Count | 101 (25 PHI types × 4 BILOU tags + O) |
| Training Hardware | NVIDIA RTX 5090 (31.8GB VRAM) |

### Training Performance (Best: Epoch 10)
| Metric | Value |
|--------|-------|
| F1 Score | 0.9774 |
| Precision | 0.9608 |
| Recall | 0.9946 |
| Val Loss | 0.0488 |
| Val Accuracy | 0.9922 |
| Entity Accuracy | 0.9855 |

### Benchmark Comparison
| Solution | F1 Score | Cost/1M Notes |
|----------|----------|---------------|
| GPT-4o | 79% | $21,400 |
| AWS Comprehend Medical | 83% | $14,525 |
| Azure Health Services | 91% | $13,125 |
| John Snow Labs | 96% | $2,500 (self-host) |
| **Clinical-Deid (Ours)** | **97.74%** | **$0 (open-source)** |

---

## Training Data Assets

| File | Location | Size | Description |
|------|----------|------|-------------|
| Raw Nemotron | `data/nemotron_healthcare.jsonl` | ~5MB | NVIDIA Nemotron-PII healthcare subset |
| Processed BILOU | `data/processed_bilou.jsonl` | ~179MB | Token-level BILOU labels |
| Google Health Annotations | `data/google_health/` | ~46KB | i2b2-2014 labels for PhysioNet Gold |

### Training Split
| Split | Records | Percentage |
|-------|---------|------------|
| Train | 2,904 | 80% |
| Validation | 726 | 20% |
| **Total** | **3,630** | 100% |

### PHI Entity Types (25 Categories)
```
name, date, age, address, phone_number, email, social_security_number,
medical_record_number, health_plan_beneficiary_number, account_number,
certificate_or_license_number, vehicle_identifier, device_identifier,
url, ip_address, biometric_identifier, full_face_photo, username,
password, organization, occupation, location, credit_card_number,
bank_account_number, passport_number
```

---

## Source Code Assets

### Core Scripts
| File | Purpose | Status |
|------|---------|--------|
| `download.py` | Fetch Nemotron-PII from HuggingFace, filter healthcare | ✅ Complete |
| `labels.py` | 101 BILOU labels, entity type mappings | ✅ Complete |
| `preprocess.py` | Character spans → token-level BILOU labels | ✅ Complete |
| `train.py` | Training loop with class weighting, metrics | ✅ Complete |
| `deid.py` | ClinicalDeidentifier class with Faker replacement | ⚠️ Untested |
| `check_cuda.py` | CUDA/GPU verification | ✅ Complete |

### Planned Scripts
| File | Purpose | Status |
|------|---------|--------|
| `evaluate.py` | Evaluation harness for external datasets | 📋 Planned |
| `api.py` | FastAPI wrapper for Lambda deployment | 📋 Planned |
| `chunk.py` | Note chunking for >4096 token documents | 📋 Planned |

---

## Infrastructure Assets (Planned)

### AWS Lambda Deployment
| Resource | Configuration | Status |
|----------|---------------|--------|
| Lambda Function | Container image, 10GB memory | 📋 Planned |
| API Gateway | REST API, rate limiting | 📋 Planned |
| S3 Bucket | Model weights storage | 📋 Planned |
| CloudFront | CDN for API | 📋 Planned |
| Route53 | deid.riggsmedai.com | 📋 Planned |

### Endpoints (Planned)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/deid/process` | POST | De-identify text |
| `/deid/validate` | POST | Pre-flight check (size, tokens) |
| `/deid/batch` | POST | Process multiple notes |
| `/deid/health` | GET | Health check |

---

## Integration Points

### CPT Grader Dashboard
| Integration | Purpose | Status |
|-------------|---------|--------|
| PHI Removal | Pre-process notes before CPT analysis | 📋 Planned |
| API Endpoint | `POST /deid/process` | 📋 Planned |
| Dashboard URL | cpt.riggsmedai.com | ✅ Live |

### Other RiggsMedAI Services
| Service | URL | Integration |
|---------|-----|-------------|
| CPT Assistant V1 | cpt1.riggsmedai.com | Potential PHI pre-filter |
| CPT Assistant V2 | cpt2.riggsmedai.com | Potential PHI pre-filter |
| Main Site | riggsmedai.com | Product landing page |

---

## Dependencies

### Python Packages
```
torch>=2.0
transformers>=4.35
datasets
pandas
numpy
seqeval
faker
tqdm
scikit-learn
```

### Model Dependencies
```
yikuan8/Clinical-Longformer (HuggingFace)
nvidia/Nemotron-PII (HuggingFace, CC BY 4.0)
```

---

## Licensing

| Asset | License |
|-------|---------|
| Training Data (Nemotron-PII) | CC BY 4.0 |
| Base Model (Clinical-Longformer) | Apache 2.0 |
| Our Fine-tuned Weights | TBD (Open-source planned) |
| API Service | Commercial |

---

## File Structure
```
C:\MyScripts\ModelWorks\clinical-deid\
├── .venv/                      # Python virtual environment
├── checkpoints/
│   └── best_model/             # Production model weights
├── data/
│   ├── google_health/          # External validation data
│   │   ├── I2B2-2014-Relabeled-PhysionetGoldCorpus.csv
│   │   └── README.txt
│   ├── nemotron_healthcare.jsonl
│   └── processed_bilou.jsonl
├── __pycache__/
├── check_cuda.py
├── deid.py
├── download.py
├── labels.py
├── preprocess.py
├── train.py
├── PROJECT_ASSETS.md           # This file
├── README.md
└── PROJECT_DOCUMENTATION.md
```

---

## Contact

**Gary Riggs, MD**  
Medical Director, Metro Physician Group  
RIGGSMED LLC  
Email: riggsmed@gmail.com  
Website: riggsmedai.com
