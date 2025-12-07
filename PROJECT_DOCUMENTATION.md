# Clinical-Deid Project Documentation

**Internal Roadmap & Implementation Guide**

**Owner:** Gary Riggs, MD | RIGGSMED LLC  
**Created:** December 7, 2025  
**Status:** Active Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Vision](#project-vision)
3. [Technical Architecture](#technical-architecture)
4. [Development Roadmap](#development-roadmap)
5. [AWS Deployment](#aws-deployment)
6. [Web Application](#web-application)
7. [CPT Dashboard Integration](#cpt-dashboard-integration)
8. [Commercial Strategy](#commercial-strategy)
9. [Validation & Compliance](#validation--compliance)
10. [Risk Assessment](#risk-assessment)

---

## Executive Summary

Clinical-Deid is an open-source PHI de-identification system that achieves 97.13% F1 score, outperforming AWS Comprehend Medical (83%) and matching John Snow Labs (96%). The project follows a hybrid business model: open-source weights for community adoption, commercial API for enterprise revenue.

### Key Metrics (as of December 7, 2025)

| Metric | Value |
|--------|-------|
| Model F1 Score | 97.74% |
| Precision | 96.08% |
| Recall | 99.46% |
| Training Data | 3,630 records |
| Parameters | 148M |
| Context Length | 4,096 tokens |

### Competitive Position

```
                        ACCURACY
                           ↑
               98% │      ★ Clinical-Deid (97.74%)
                   │        John Snow Labs (96%)
               95% │
                   │
               92% │      Azure (91%)
                   │
               88% │
                   │
               84% │      AWS Comprehend (83%)
                   │
               80% │      GPT-4o (79%)
                   │
                   └──────────────────────────────→ COST
                       $0    $5K   $10K   $15K   $20K  /1M notes
```

---

## Project Vision

### Mission Statement

Democratize clinical text de-identification by providing an open-source, state-of-the-art model that enables healthcare organizations to protect patient privacy without vendor lock-in or prohibitive costs.

### Goals

1. **Open Source Leadership** — Become the default open-source solution for clinical de-identification
2. **Revenue Generation** — Build sustainable API business serving healthcare organizations
3. **Integration Hub** — Power de-identification across RiggsMedAI products
4. **Research Enablement** — Enable researchers to safely work with clinical text

### Success Metrics

| Timeframe | Metric | Target |
|-----------|--------|--------|
| Q1 2026 | GitHub Stars | 500+ |
| Q1 2026 | API Users (Free) | 100+ |
| Q2 2026 | Paying Customers | 10+ |
| Q2 2026 | Monthly API Revenue | $2,000+ |
| Q4 2026 | External Validation F1 | >92% |

---

## Technical Architecture

### Model Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    INFERENCE PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Text ──▶ Tokenizer ──▶ Model ──▶ Predictions ──▶ Output
│                    │            │            │              │
│           Clinical-Longformer   │    BILOU Labels    Post-Process
│           (4096 context)        │    (101 classes)   (Merge, Replace)
│                                 │                           │
│                         Token Classification                │
│                         (Fine-tuned on Nemotron-PII)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### BILOU Tagging

| Tag | Meaning | Example |
|-----|---------|---------|
| B | Begin | "B-NAME" for "John" in "John Smith" |
| I | Inside | "I-NAME" for middle tokens |
| L | Last | "L-NAME" for "Smith" in "John Smith" |
| O | Outside | Non-PHI tokens |
| U | Unit | Single-token entity ("U-AGE" for "72") |

### PHI Entity Types (25)

**HIPAA Safe Harbor (18):**
- Names, dates, ages >89, addresses, phone, fax, email
- SSN, MRN, health plan ID, account numbers
- License/certificate numbers, vehicle IDs, device IDs
- URLs, IP addresses, biometric IDs, photos

**Extended (7):**
- Username, password, organization, occupation
- Location (general), credit card, bank account, passport

### Processing Limits

| Input | Limit | Handling |
|-------|-------|----------|
| Max tokens | 4,096 | Chunking with overlap |
| Max characters | ~16,000 | Chunking with overlap |
| Max file size | 1 MB | Reject with 413 |
| Chunk overlap | 200 tokens | Prevent split entities |

---

## Development Roadmap

### Phase 1: Core Model ✅ (December 7, 2025) - COMPLETE

- [x] Download and filter Nemotron-PII healthcare subset
- [x] Implement BILOU preprocessing pipeline
- [x] Fine-tune Clinical-Longformer
- [x] Achieve >95% F1 on validation set (97.74% achieved)
- [x] Basic inference script (deid.py)
- [x] Manual testing on realistic notes
- [x] Complete training through epoch 10
- [x] Export final model weights
- [x] Publish to GitHub: https://github.com/Hrygt/clinical-deid
- [x] Publish to HuggingFace: https://huggingface.co/riggsmed/clinical-deid
- [x] LinkedIn announcement

### Phase 2: Lambda Deployment (December 2025 - January 2026)

- [ ] Create Lambda container image
- [ ] Implement validation layer (size, token limits)
- [ ] Build chunking logic for long documents
- [ ] Set up API Gateway with rate limiting
- [ ] Deploy to deid.riggsmedai.com
- [ ] Add authentication (API keys)
- [ ] Implement usage tracking

### Phase 3: Web Application (January 2026)

- [ ] Landing page with live demo
- [ ] User registration and API key management
- [ ] Usage dashboard
- [ ] Documentation site
- [ ] Pricing page with Stripe integration

### Phase 4: Integrations (February 2026)

- [ ] CPT Dashboard integration
- [ ] Batch processing endpoint
- [ ] Webhook notifications
- [ ] Python SDK
- [ ] JavaScript SDK

### Phase 5: Validation & Compliance (Q1-Q2 2026)

- [ ] i2b2 2014 benchmark evaluation
- [ ] PhysioNet Gold Standard evaluation
- [ ] Real clinical note validation (IRB)
- [ ] Security audit
- [ ] SOC 2 preparation

### Phase 6: Scale & Monetize (Q2-Q3 2026)

- [ ] Enterprise features (SSO, SLA)
- [ ] On-premise deployment option
- [ ] Partner integrations (EHR vendors)
- [ ] Marketing launch

---

## AWS Deployment

### Architecture

```
                            ┌──────────────────┐
                            │   CloudFront     │
                            │   CDN + WAF      │
                            └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │   API Gateway    │
                            │   (REST API)     │
                            │   Rate Limiting  │
                            └────────┬─────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
     │   Validation    │   │   De-ID Lambda   │   │   Auth Lambda   │
     │   Lambda        │   │   (Container)    │   │   (API Keys)    │
     │   (256MB)       │   │   (10GB RAM)     │   │   (256MB)       │
     └─────────────────┘   └────────┬─────────┘   └─────────────────┘
                                    │
                           ┌────────▼────────┐
                           │   S3 Bucket     │
                           │   Model Weights │
                           │   (Warm Start)  │
                           └─────────────────┘
```

### API Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/health` | GET | Health check | None |
| `/validate` | POST | Pre-flight check | API Key |
| `/process` | POST | De-identify text | API Key |
| `/batch` | POST | Process multiple | API Key |

### Request/Response Format

**POST /process**

Request:
```json
{
  "text": "Patient John Smith DOB 03/15/1952...",
  "mode": "redact",  // redact | replace | spans
  "options": {
    "preserve_structure": true,
    "replacement_consistency": true
  }
}
```

Response:
```json
{
  "success": true,
  "result": "Patient [NAME] DOB [DATE]...",
  "metadata": {
    "tokens_processed": 234,
    "entities_found": 12,
    "processing_time_ms": 87
  }
}
```

**POST /validate**

Request:
```json
{
  "text": "...",
  "check_only": true
}
```

Response:
```json
{
  "ok": true,
  "estimated_tokens": 2340,
  "chunks_required": 1,
  "estimated_cost": 0.001
}
```

### Error Codes

| Code | Error | Message |
|------|-------|---------|
| 400 | Bad Request | "No text provided" |
| 401 | Unauthorized | "Invalid API key" |
| 413 | Payload Too Large | "Max 1MB per request" |
| 422 | Unprocessable | "Text exceeds token limit" |
| 429 | Rate Limited | "Rate limit exceeded" |
| 500 | Server Error | "Processing failed" |

### Lambda Configuration

| Setting | Value |
|---------|-------|
| Runtime | Container (Python 3.11) |
| Memory | 10,240 MB |
| Timeout | 60 seconds |
| Ephemeral Storage | 2,048 MB |
| Architecture | x86_64 |
| Provisioned Concurrency | 2 (for warm starts) |

### Cost Estimation

| Resource | Monthly Cost |
|----------|--------------|
| Lambda (100K invocations) | ~$15 |
| API Gateway | ~$5 |
| S3 (model storage) | ~$1 |
| CloudFront | ~$5 |
| **Total** | **~$26/month** |

---

## Web Application

### Pages

1. **Landing Page** (deid.riggsmedai.com)
   - Hero: "De-identify clinical notes in seconds"
   - Live demo: Paste note → See redacted output
   - Benchmarks vs competitors
   - CTA: "Get Free API Key"

2. **Documentation** (/docs)
   - Quick start guide
   - API reference
   - Code examples (Python, JavaScript, cURL)
   - Best practices

3. **Dashboard** (/dashboard)
   - API key management
   - Usage statistics
   - Billing history
   - Settings

4. **Pricing** (/pricing)
   - Tier comparison
   - Calculator
   - FAQ

### Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Tailwind |
| Backend | FastAPI |
| Auth | Clerk or Auth0 |
| Payments | Stripe |
| Hosting | Vercel or AWS Amplify |
| Database | DynamoDB |

---

## CPT Dashboard Integration

### Integration Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CPT Dashboard  │────▶│  De-ID API      │────▶│  CPT DNN Model  │
│  cpt.riggsmed   │     │  (internal)     │     │  (inference)    │
│  ai.com         │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                        │                        │
       │   Upload Note          │   Cleaned Note         │   CPT Code
       │   ──────────▶          │   ──────────▶          │   ◀──────────
       │                        │                        │
```

### Implementation

1. **Pre-processing Step**
   - Before note reaches CPT model
   - Remove PHI to prevent data leakage
   - Preserve clinical content for coding

2. **API Call**
   ```python
   # In CPT Dashboard backend
   async def preprocess_note(note_text: str) -> str:
       response = await deid_client.process(
           text=note_text,
           mode="redact"
       )
       return response.result
   ```

3. **Configuration**
   - Toggle: Enable/disable de-identification
   - Mode: Redact vs Replace
   - Internal API (no rate limits)

---

## Commercial Strategy

### Business Model

**Hybrid Open-Core:**
- Open source: Model weights, inference code
- Commercial: Hosted API, support, SLA

### Pricing Tiers

| Tier | Price | Notes/Month | Features |
|------|-------|-------------|----------|
| **Free** | $0 | 100 | Basic API access |
| **Starter** | $49/mo | 5,000 | Priority support |
| **Pro** | $199/mo | 50,000 | Batch processing, webhooks |
| **Enterprise** | Custom | Unlimited | SLA, SSO, on-premise |

### Revenue Projections

| Quarter | Free Users | Paid Users | MRR |
|---------|------------|------------|-----|
| Q1 2026 | 50 | 5 | $500 |
| Q2 2026 | 150 | 15 | $1,500 |
| Q3 2026 | 300 | 30 | $4,000 |
| Q4 2026 | 500 | 60 | $10,000 |

### Target Customers

1. **Healthcare Startups** — Need de-id for AI training data
2. **Research Institutions** — Academic medical centers
3. **EHR Vendors** — White-label integration
4. **Pharma/Life Sciences** — Clinical trial data
5. **Health Tech Companies** — NLP on clinical text

### Competitive Advantages

1. **Price** — 10x cheaper than AWS
2. **Accuracy** — 97% F1 vs 83% AWS
3. **Transparency** — Open weights, auditable
4. **Flexibility** — Self-host or API
5. **Clinical Focus** — Built by a physician

---

## Validation & Compliance

### Validation Datasets

| Dataset | Notes | Status |
|---------|-------|--------|
| Nemotron-PII (held-out) | 726 | ✅ 97.13% F1 |
| i2b2 2014 | 1,304 | 📋 Apply for access |
| PhysioNet Gold Standard | 2,434 | 📋 Requires CITI |
| Real SSM Health Notes | TBD | 📋 IRB required |

### Compliance Considerations

**HIPAA:**
- Model processes PHI → Must be HIPAA compliant
- API: BAA required for healthcare customers
- Self-hosted: Customer's responsibility

**SOC 2:**
- Target: Q3 2026
- Required for enterprise customers

**FDA:**
- Not a medical device (no diagnosis/treatment)
- Documentation tool only

### Security Measures

1. **Encryption** — TLS 1.3 in transit, AES-256 at rest
2. **No Data Retention** — Process and discard
3. **Audit Logging** — All API calls logged
4. **Access Control** — API keys with scopes
5. **Rate Limiting** — Prevent abuse

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Real-world F1 < 90% | Medium | High | Extensive validation |
| Long notes fail | Low | Medium | Chunking with overlap |
| Cold start latency | Medium | Low | Provisioned concurrency |
| Model hallucinations | Low | High | High confidence threshold |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| No product-market fit | Medium | High | Customer interviews |
| Competitor response | High | Medium | Speed, open source moat |
| Regulatory changes | Low | High | Modular architecture |
| AWS cost overruns | Low | Medium | Usage monitoring |

### Mitigation Strategies

1. **Validation First** — Benchmark on real data before marketing
2. **Conservative Claims** — "Up to 97% F1" with caveats
3. **Expert Review** — Recommend human review for compliance
4. **Insurance** — Professional liability coverage

---

## Appendix

### Useful Commands

```bash
# Train model
python train.py --epochs 10 --batch_size 4

# Test inference
python -c "from deid import ClinicalDeidentifier; d = ClinicalDeidentifier('checkpoints/best_model'); print(d.deidentify('Patient John Smith'))"

# Export model to HuggingFace
python export_to_hub.py --model checkpoints/best_model --repo riggsmedai/clinical-deid
```

### References

1. NVIDIA Nemotron-PII: https://huggingface.co/datasets/nvidia/Nemotron-PII
2. Clinical-Longformer: https://huggingface.co/yikuan8/Clinical-Longformer
3. i2b2 2014 Challenge: https://www.i2b2.org/NLP/DataSets/
4. HIPAA Safe Harbor: https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/

### Contact

**Gary Riggs, MD**  
riggsmed@gmail.com  
riggsmedai.com
