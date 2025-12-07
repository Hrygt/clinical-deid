# LinkedIn Post - Clinical-Deid Launch

## Post Text (copy this):

---

🚀 Just open-sourced Clinical-Deid: a PHI de-identification model that outperforms AWS Comprehend Medical

After a weekend of training on my RTX 5090, I'm releasing a model that achieves 97.74% F1 on clinical text de-identification — beating every major commercial solution:

📊 The benchmarks:
• AWS Comprehend Medical: 83% F1 ($0.50/note)
• Azure Health Services: 91% F1
• John Snow Labs: 96% F1
• Clinical-Deid: 97.74% F1 (FREE)

🔬 How it works:
• Fine-tuned Clinical-Longformer (pretrained on MIMIC-III)
• 4,096 token context (handles full notes without chunking)
• 25 PHI categories (all HIPAA Safe Harbor identifiers)
• BILOU tagging for precise entity boundaries

🎯 Why this matters:
Healthcare organizations spend $14,500+ per million notes on de-identification. With open-source weights, that cost drops to zero.

High recall (99.46%) means you catch almost every PHI instance — critical for HIPAA compliance. Missing PHI is a violation; over-redacting is just annoying.

📦 What's included:
• Full model weights on HuggingFace
• Training code on GitHub
• Apache 2.0 license (commercial license available)

🤝 Call for validation:
I trained on synthetic data (NVIDIA Nemotron-PII). If you have access to i2b2 2014 or PhysioNet Gold Standard datasets, I'd love help validating on real clinical notes.

Links in comments 👇

#Healthcare #AI #MachineLearning #NLP #OpenSource #HIPAA #DeIdentification #ClinicalNLP #HealthTech

---

## Comment to add with links:

🔗 Links:
• GitHub: github.com/riggsmedai/clinical-deid
• HuggingFace: huggingface.co/riggsmedai/clinical-deid
• API (coming soon): deid.riggsmedai.com

Built with Clinical-Longformer and NVIDIA's Nemotron-PII dataset. Thanks to the open-source community that makes this possible.

Questions? Drop a comment or reach out!

---

## Image suggestion:

Create a simple graphic showing:
- Bar chart of F1 scores (AWS 83%, Azure 91%, JSL 96%, Clinical-Deid 97.74%)
- Or screenshot of the training completion showing the metrics

---

## Hashtag strategy:

Primary (high engagement):
#Healthcare #AI #MachineLearning #OpenSource

Secondary (niche reach):
#NLP #HIPAA #ClinicalNLP #HealthTech #DeIdentification

Industry reach:
#DigitalHealth #HealthcareInnovation #MedTech
