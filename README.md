# AWS AI Opt-Out Guide

A comprehensive guide and toolkit for opting out of AWS AI services' default data usage for model improvements. Protects your data privacy and ensures compliance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

By default, some AWS AI services (e.g., Rekognition, Transcribe) use your data to improve models, potentially storing it outside your region. This repo provides scripts, templates, and instructions to opt out organization-wide.

Key features:
- Supports manual, IaC (Terraform, CloudFormation, CDK), and enterprise (Control Tower/LZA) methods.
- Verification script to confirm opt-out.
- Alignment with AWS Well-Architected Framework (e.g., MLSEC-01).
- Handles transitions like CodeWhisperer to Amazon Q Developer.

For full details, read [GUIDE.md](GUIDE.md) (the complete blog post).

## Quick Start

1. **Clone the repo**:
   
`` bash
git clone https://github.com/yourusername/aws-ai-optout-guide.git cd aws-ai-optout-guide
``

2. **Manual Opt-Out (Single Account)**:
- Use scripts in `scripts/` and templates in `templates/`.
- Example: Run Method 1 steps from GUIDE.md, using `templates/ai-opt-out-policy.json`.

3. **IaC Deployment**:
- Terraform: See `templates/terraform/main.tf`.
- CloudFormation: Deploy `templates/cloudformation/ai-opt-out.yaml`.
- CDK (Python): `cd templates/cdk && cdk deploy` (install AWS CDK first: `pip install aws-cdk-lib`).

4. **Verify**:

`ỳthon
python scripts/verify_ai_opt_out.py
``


5. **Enterprise (LZA/Control Tower)**:
- Use workarounds in GUIDE.md, e.g., `scripts/post-lza-deployment.sh`.

## Affected Services (as of July 2025)
- Amazon CodeGuru Profiler, Comprehend, Lex, Polly, Rekognition, Textract, Transcribe, Translate.
- Newer: AWS Transform, Kiro (Preview).

Privacy-first services (no opt-out needed): Bedrock, SageMaker, Q Developer Pro.

## Requirements
- AWS CLI configured with admin access.
- Python 3+ for scripts.
- For IaC: Terraform, AWS CDK, or CloudFormation tools.

## Contributing
- Fork and PR improvements.
- Report issues or suggest features.

See [GUIDE.md](GUIDE.md) for troubleshooting, FAQs, and compliance checklists.

## License
MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments
Thanks to the AWS community for insights on privacy and implementations.