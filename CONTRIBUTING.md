# Contributing to Clinical-Deid

Thank you for your interest in contributing to Clinical-Deid! This document provides guidelines for contributing.

## Ways to Contribute

### 1. Validation Results (Most Needed!)

If you have access to clinical de-identification datasets, please help us validate:

- i2b2/n2c2 2014 De-identification Challenge
- PhysioNet Gold Standard Corpus
- N-GRID 2016
- MIMIC-III Clinical Notes

See the [Validation section in README](README.md#-help-us-validate) for details.

### 2. Bug Reports

Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, GPU)

### 3. Feature Requests

Open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Alternative approaches you've considered

### 4. Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python -m pytest tests/`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions focused and small

## Contributor License Agreement (CLA)

By submitting a contribution to this project, you agree to the following terms:

### Grant of Rights

You grant RIGGSMED LLC a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to:

1. Use, copy, modify, and distribute your contribution
2. Sublicense your contribution under any license, including proprietary licenses
3. Use your contribution in commercial products and services

### Your Representations

You represent that:

1. You are the original author of the contribution
2. You have the right to grant the above license
3. Your contribution does not violate any third-party rights
4. Your contribution does not contain any malicious code

### Why a CLA?

Clinical-Deid uses a dual-licensing model (Apache 2.0 for open source, commercial license for enterprise). The CLA ensures we can:

- Continue offering the open-source version for free
- Offer commercial licenses to enterprise customers
- Protect contributors from liability

### How to Sign

By opening a Pull Request, you indicate agreement to these terms. No separate signature required.

## Review Process

1. All PRs require review by a maintainer
2. CI must pass (when implemented)
3. Documentation must be updated if needed
4. Breaking changes require discussion first

## Community Guidelines

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn
- No PHI in issues, PRs, or discussions

## Questions?

Email: riggsmed@gmail.com

---

Thank you for helping make clinical text de-identification accessible to everyone! 🏥
