from aws_cdk import RemovalPolicy, Stack
from aws_cdk.aws_organizations import CfnPolicy
from constructs import Construct


class AIOptOutStack(Stack):
    """AI Services opt-out policy (hardened variant) for an EXISTING organization.

    This stack deliberately does not create or own the organization. Pass the
    existing organization root ID (r-xxxx) via context or props — see app.py.

    One-time prerequisite in the management account (an API call, not a resource):
        aws organizations enable-policy-type \
            --root-id <r-xxxx> --policy-type AISERVICES_OPT_OUT_POLICY
    """

    def __init__(self, scope: Construct, construct_id: str, *, root_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if not root_id or not root_id.startswith("r-"):
            raise ValueError(
                "root_id must be your organization root (r-xxxx). "
                "Find it: aws organizations list-roots --query 'Roots[0].Id' --output text"
            )

        policy = CfnPolicy(
            self,
            "AIOptOutPolicy",
            name="AI-OptOut-All-Services",
            description="Opt out of AI service data usage (child overrides locked)",
            type="AISERVICES_OPT_OUT_POLICY",
            content={
                "services": {
                    "@@operators_allowed_for_child_policies": ["@@none"],
                    "default": {
                        "@@operators_allowed_for_child_policies": ["@@none"],
                        "opt_out_policy": {
                            "@@operators_allowed_for_child_policies": ["@@none"],
                            "@@assign": "optOut",
                        },
                    },
                }
            },
            target_ids=[root_id],
        )
        # Deleting the stack must not remove the org-wide privacy control.
        policy.apply_removal_policy(RemovalPolicy.RETAIN)
