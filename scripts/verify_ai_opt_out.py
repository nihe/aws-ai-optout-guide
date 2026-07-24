#!/usr/bin/env python3
"""
Verify AWS AI services opt-out policy configuration — fail-closed.

Exit code 0 only when ALL of the following hold; 1 otherwise:
  - an AWS Organization exists and AISERVICES_OPT_OUT_POLICY is ENABLED,
  - EVERY active account's EFFECTIVE policy resolves to the hardened optOut
    (default + @@assign: optOut + all three child-policy locks),
  - no API call needed for the above failed.

The compliance decision is the per-account EFFECTIVE policy — that is what AWS
actually enforces. Policy objects that are not the hardened template are reported
as governance-hygiene warnings, not failures: an unattached draft or a deliberate
per-OU exception must not break the gate while every account still resolves to
the hardened optOut.

Any effective-policy error, missing effective policy, or required API failure is
treated as a failure — the script fails closed rather than reporting optimistic
success. Informational policy-object hygiene warnings do NOT fail the gate as
long as every active account's effective policy is the hardened optOut.
All Organizations list APIs are paginated.
"""
import boto3
import json
import sys
from datetime import datetime

LOCK = ["@@none"]


def is_hardened_opt_out(content):
    """True only for: default + @@assign optOut + all three child-policy locks."""
    services = content.get("services", {})
    default = services.get("default", {})
    setting = default.get("opt_out_policy", {})
    return (
        services.get("@@operators_allowed_for_child_policies") == LOCK
        and default.get("@@operators_allowed_for_child_policies") == LOCK
        and setting.get("@@operators_allowed_for_child_policies") == LOCK
        and setting.get("@@assign") == "optOut"
    )


def verify_ai_opt_out():
    org_client = boto3.client("organizations")
    failures = []

    try:
        org = org_client.describe_organization()
        print(f"✅ Organization found: {org['Organization']['Id']}")

        enabled = any(
            pt["Type"] == "AISERVICES_OPT_OUT_POLICY" and pt["Status"] == "ENABLED"
            for pt in org["Organization"]["AvailablePolicyTypes"]
        )
        if enabled:
            print("✅ AI opt-out policy type is ENABLED")
        else:
            print("❌ AI opt-out policy type is NOT enabled")
            return False

        # --- policies (paginated) ---
        hardened_policy_found = False
        policy_count = 0
        for page in org_client.get_paginator("list_policies").paginate(
            Filter="AISERVICES_OPT_OUT_POLICY"
        ):
            for policy in page["Policies"]:
                policy_count += 1
                detail = org_client.describe_policy(PolicyId=policy["Id"])
                content = json.loads(detail["Policy"]["Content"])
                if is_hardened_opt_out(content):
                    print(f"  ✅ {policy['Name']} — hardened default optOut")
                    hardened_policy_found = True
                else:
                    # Hygiene warning only: an unattached or deliberately scoped policy
                    # must not fail the gate — the effective-policy check below decides.
                    print(f"  ⚠️  {policy['Name']} — not the hardened template (informational)")

        print(f"\n📋 {policy_count} AI opt-out policies checked")
        if not hardened_policy_found:
            print("⚠️  No policy object matches the hardened template — "
                  "relying on the effective-policy check below")

        # --- accounts (paginated): validate the EFFECTIVE policy content ---
        print("\n🏢 Checking effective policy for every active account:")
        for page in org_client.get_paginator("list_accounts").paginate():
            for account in page["Accounts"]:
                # AWS retires the account "Status" field on 2026-09-09; "State" replaces it.
                if account.get("State", account.get("Status")) != "ACTIVE":
                    continue
                try:
                    effective = org_client.describe_effective_policy(
                        PolicyType="AISERVICES_OPT_OUT_POLICY",
                        TargetId=account["Id"],
                    ).get("EffectivePolicy")
                    if effective and is_hardened_opt_out(
                        json.loads(effective["PolicyContent"])
                    ):
                        print(f"  ✅ {account['Name']} — hardened optOut effective")
                    else:
                        print(f"  ❌ {account['Name']} — effective policy missing or not hardened optOut")
                        failures.append(f"account {account['Name']} not compliant")
                except Exception as e:
                    print(f"  ❌ {account['Name']} — API error: {e}")
                    failures.append(f"account {account['Name']} check failed: {e}")

        if failures:
            print(f"\n❌ {len(failures)} failure(s):")
            for f in failures:
                print(f"   - {f}")
            return False
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 AWS AI Opt-Out Verification Tool (fail-closed)")
    print(f"📅 Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if verify_ai_opt_out():
        print("\n✅ AI opt-out verification passed")
        sys.exit(0)
    print("\n❌ AI opt-out verification FAILED — action required")
    sys.exit(1)
