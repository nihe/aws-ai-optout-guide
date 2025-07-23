from aws_cdk import Stack
from aws_cdk.aws_organizations import CfnPolicy, CfnOrganization
from constructs import Construct

class AIOptOutStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the organization (assumes it doesn't exist; for existing orgs, pass root_id as a prop)
        org = CfnOrganization(self, "Organization", feature_set="ALL")

        # Create the opt-out policy
        ai_opt_out_policy = CfnPolicy(self, "AIOptOutPolicy",
            name="AI-OptOut-All-Services",
            description="Opt out of AI service data usage",
            type="AISERVICES_OPT_OUT_POLICY",
            content={
                "services": {
                    "default": {
                        "opt_out_policy": {
                            "@@assign": "optOut"
                        }
                    }
                }
            },
            target_ids=[org.attr_root_id]
        )