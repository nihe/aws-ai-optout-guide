# AWS AI Opt-Out Guide

**One policy, thirty-plus services.** A guide and toolkit for opting your organization out of AWS AI services' default data usage for model improvement — scripts, IaC templates, and a verification tool, aligned with the AWS Well-Architected Framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Updated September 2026.** The scope of the AI services opt-out policy has more than tripled. The official list now covers **35 services** (verified 2026-09-30, up from 31 in July), including Amazon CloudWatch, GuardDuty, Security Hub, AWS Glue, DMS, and, new since July, AWS Config. Amazon Q Developer is being sunset in favor of **Kiro** (end of support: 30 April 2027). See [GUIDE.md](GUIDE.md) for the full write-up.

## Overview

By default, a growing set of AWS AI services may use your content to improve their models — including model training — and may store it in an AWS Region outside the one you're using. This is a documented default, not a scandal; the point is to know it and make a deliberate decision. This repo provides scripts, templates, and instructions to opt out organization-wide.

Key points:
- **It's not an SCP.** `AISERVICES_OPT_OUT_POLICY` is a declarative Organizations policy (the `@@`-operator family), not an authorization policy. It isn't evaluated by IAM, so a misconfiguration fails *silently* — verification matters.
- Supports manual, IaC (Terraform, CloudFormation, CDK), and enterprise (Control Tower / LZA) methods.
- Templates use the **hardened variant** — `@@operators_allowed_for_child_policies` locks the opt-out so member accounts can't override it.
- Fail-closed verification: the script validates the effective policy per account and exits non-zero on failure; the AWS Config rule publishes real `PutEvaluations` results.
- Terraform and CDK reference your **existing** organization — no template creates or owns the organization (a destroyed stack must never be able to delete it).
- Aligns with the AWS Well-Architected Framework (ML Lens MLSEC-01).

## Quick Start

1. **Clone the repo:**

   ```bash
   git clone https://github.com/nihe/aws-ai-optout-guide.git
   cd aws-ai-optout-guide
   ```

2. **Manual opt-out (single account):**
   - Use `scripts/` and `templates/`. See Method 1 in [GUIDE.md](GUIDE.md), using `templates/ai-opt-out-policy.json`.

3. **IaC deployment:**
   - Terraform: `templates/terraform/main.tf`
   - CloudFormation: `templates/cloudformation/ai-opt-out.yaml` (pass your root ID `r-xxxx` as the `OrganizationRootId` parameter; assumes the policy type is enabled) or `templates/ai-opt-out-policy.yaml` (a Lambda-backed custom resource enables the policy type and resolves the root ID for you)
   - CDK (Python): `cd templates/cdk && pip install -r requirements.txt && cdk deploy -c root_id=r-xxxx`

4. **Verify (fail-closed):**

   ```bash
   python scripts/verify_ai_opt_out.py
   ```

   The script validates the *effective* policy for every active account (hardened `optOut` + all child-policy locks) and exits non-zero on any failure — use it as a CI/CD or audit gate.

5. **Enterprise (LZA / Control Tower):**
   - LZA has no native support (GitHub issue #107 is still open as of v1.16.3). Use `scripts/post-lza-deployment.sh` (post-deploy automation) or `config/customizations-config.yaml` (custom CloudFormation stack). See Method 2 in [GUIDE.md](GUIDE.md).

## Affected Services (as of September 2026)

The official [Organizations supported-services list](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ai-opt-out_all.html#ai-opt-out-all-list) now counts **35 services**, well beyond the classic AI ones:

- **Classic AI:** CodeGuru Profiler, Comprehend, Lex, Polly, Rekognition, Textract, Transcribe, Translate
- **Observability, ops & governance:** CloudWatch, AI Operations, DevOps Agent, AWS Config
- **Security:** GuardDuty, Security Hub, Security Lake
- **Data & integration:** Glue, DMS, DataZone, Entity Resolution
- **Contact center:** the Amazon Connect family (incl. Connect Health and Connect Talent), Chime SDK voice analytics
- **Business & end-user:** Amazon Quick, Supply Chain, WorkSpaces, Fraud Detector
- **Newer agentic:** AWS Transform, FinOps Agent
- **Industry & science:** Amazon Bio Discovery, Scenario Discovery (IoT SiteWise)
- **Developer tools:** Amazon Q Developer (incl. CodeWhisperer)

Use `default` in your policy so current **and future** services are covered automatically.

**Privacy-first (no opt-out needed):** Amazon Bedrock, Amazon SageMaker, and Kiro via IAM Identity Center / Kiro Enterprise.

**Edge cases the org policy doesn't reach:** Industrial AI (Monitron, Lookout for Vision & Equipment — being retired, opt-out via AWS Support), and Builder-ID / social-login access to Kiro (opt out in the app settings). See GUIDE.md.

## Requirements

- AWS CLI configured with management-account / admin access
- An AWS Organization (creating one is free; required even for a single account)
- Python 3.9+ for scripts
- For IaC: Terraform, AWS CDK, or CloudFormation tooling

## Contributing

Fork and open a PR, or file an issue. Before submitting, run the regression tests — they guard the policy validators against regressions (including the locked-but-`optIn` case):

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest tests/ -q
``` 
See [GUIDE.md](GUIDE.md) for troubleshooting, FAQs, and compliance checklists.

## License

MIT License — see [LICENSE](LICENSE).

## Acknowledgments

Thanks to the AWS community for insights on privacy, Control Tower, and LZA implementations.

Portions of this codebase, its documentation, and code reviews were developed with assistance from [Claude](https://www.anthropic.com/claude), Anthropic's AI model. All AI-assisted contributions were reviewed and validated by the maintainers before merging.
