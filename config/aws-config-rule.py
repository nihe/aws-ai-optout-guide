"""Custom AWS Config rule (periodic): verify the org-wide AI opt-out policy.

Publishes a real evaluation via config:PutEvaluations (required for AWS Config to
record the result). COMPLIANT only when a policy that is attached to the
organization root is the hardened variant: services.default.opt_out_policy with
@@assign: optOut and all three @@operators_allowed_for_child_policies locks.

Deploy in the Organizations management account (or delegated administrator) with
IAM permissions: organizations:ListPolicies, organizations:ListTargetsForPolicy,
organizations:DescribePolicy, config:PutEvaluations. Trigger: periodic.
"""
import json
from datetime import datetime, timezone

import boto3

LOCK = ["@@none"]


def _is_hardened_opt_out(content):
    services = content.get("services", {})
    default = services.get("default", {})
    setting = default.get("opt_out_policy", {})
    return (
        services.get("@@operators_allowed_for_child_policies") == LOCK
        and default.get("@@operators_allowed_for_child_policies") == LOCK
        and setting.get("@@operators_allowed_for_child_policies") == LOCK
        and setting.get("@@assign") == "optOut"
    )


def evaluate_organization_policy():
    org = boto3.client("organizations")

    found_any = False
    root_attached_seen = False
    for page in org.get_paginator("list_policies").paginate(
        Filter="AISERVICES_OPT_OUT_POLICY"
    ):
        for policy in page["Policies"]:
            found_any = True
            attached_to_root = False
            for tpage in org.get_paginator("list_targets_for_policy").paginate(
                PolicyId=policy["Id"]
            ):
                if any(t["Type"] == "ROOT" for t in tpage["Targets"]):
                    attached_to_root = True
                    break
            if not attached_to_root:
                continue

            # Evaluate EVERY root-attached policy: multiple policies can be attached,
            # and any hardened one satisfies the control.
            root_attached_seen = True
            detail = org.describe_policy(PolicyId=policy["Id"])
            content = json.loads(detail["Policy"]["Content"])
            if _is_hardened_opt_out(content):
                return "COMPLIANT", (
                    "Hardened default-optOut policy is attached to the organization root"
                )

    if root_attached_seen:
        return "NON_COMPLIANT", (
            "Root-attached AI opt-out policy found, but none is the hardened "
            "default optOut (missing default, a child-policy lock, or @@assign optOut)"
        )
    if found_any:
        return "NON_COMPLIANT", "AI opt-out policy exists but none is attached to the root"
    return "NON_COMPLIANT", "No AI opt-out policy found"


def lambda_handler(event, context):
    try:
        compliance, annotation = evaluate_organization_policy()
    except Exception as e:  # fail closed
        compliance, annotation = "NON_COMPLIANT", f"Error checking policy: {e}"

    config = boto3.client("config")
    config.put_evaluations(
        Evaluations=[
            {
                "ComplianceResourceType": "AWS::::Account",
                "ComplianceResourceId": event["accountId"],
                "ComplianceType": compliance,
                "Annotation": annotation[:256],
                "OrderingTimestamp": datetime.now(timezone.utc),
            }
        ],
        ResultToken=event["resultToken"],
    )
    return {"compliance_type": compliance, "annotation": annotation}
