# AI Services Opt-Out Policy — hardened variant, for an EXISTING AWS Organization.
#
# This module deliberately does NOT create or own the organization: destroying IaC
# state must never be able to delete an organization (deleted organizations and their
# policies cannot be recovered). Run it from the management account.
#
# One-time prerequisite (enabling a policy type is an API call, not a resource):
#   aws organizations enable-policy-type \
#       --root-id $(aws organizations list-roots --query 'Roots[0].Id' --output text) \
#       --policy-type AISERVICES_OPT_OUT_POLICY
#
# The @@operators_allowed_for_child_policies:["@@none"] operators lock the opt-out so
# no member account or child OU can override it. For a deliberate per-OU exception
# (e.g. a sandbox OU opting in to one service), drop the lock at root and add an
# explicit optIn child policy — as a documented ADR, not an accident.

data "aws_organizations_organization" "current" {}

resource "aws_organizations_policy" "ai_opt_out" {
  name        = "AI-OptOut-All-Services"
  description = "Opt out of AI service data usage (child overrides locked)"
  type        = "AISERVICES_OPT_OUT_POLICY"

  content = jsonencode({
    services = {
      "@@operators_allowed_for_child_policies" = ["@@none"]
      default = {
        "@@operators_allowed_for_child_policies" = ["@@none"]
        opt_out_policy = {
          "@@operators_allowed_for_child_policies" = ["@@none"]
          "@@assign" = "optOut"
        }
      }
    }
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_organizations_policy_attachment" "ai_opt_out" {
  policy_id = aws_organizations_policy.ai_opt_out.id
  target_id = data.aws_organizations_organization.current.roots[0].id
}
