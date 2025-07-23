# Enable AWS Organizations
resource "aws_organizations_organization" "org" {
  feature_set = "ALL"
}

# Enable AI opt-out policy type
resource "aws_organizations_policy" "ai_opt_out" {
  name        = "AI-OptOut-All-Services"
  description = "Opt out of AI service data usage"
  type        = "AISERVICES_OPT_OUT_POLICY"

  content = jsonencode({
    services = {
      default = {
        opt_out_policy = {
          "@@assign" = "optOut"
        }
      }
    }
  })
}

# Attach to organization root
resource "aws_organizations_policy_attachment" "ai_opt_out" {
  policy_id = aws_organizations_policy.ai_opt_out.id
  target_id = aws_organizations_organization.org.roots[0].id
}