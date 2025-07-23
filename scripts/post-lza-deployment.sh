#!/bin/bash
# post-lza-deployment.sh

echo "Applying AI opt-out policies..."

# Enable policy type
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations enable-policy-type \
    --root-id $ROOT_ID \
    --policy-type AISERVICES_OPT_OUT_POLICY

# Create and attach policy
POLICY_ID=$(aws organizations create-policy \
    --name "AI-OptOut-All-Services" \
    --description "Opt out of AI service data usage" \
    --type AISERVICES_OPT_OUT_POLICY \
    --content file://ai-opt-out-policy.json \
    --query 'Policy.PolicySummary.Id' \
    --output text)

aws organizations attach-policy \
    --policy-id $POLICY_ID \
    --target-id $ROOT_ID

echo "AI opt-out policies applied successfully"