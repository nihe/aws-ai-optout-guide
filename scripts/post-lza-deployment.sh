#!/bin/bash
# post-lza-deployment.sh
# Apply the AI opt-out policy after a Landing Zone Accelerator deployment.
# Convergent and fail-closed: checks state instead of suppressing errors, updates a
# drifted policy in place, verifies attachment, and gates on the verification script.
# Run from the repo root in the Organizations management account.
set -euo pipefail

POLICY_NAME="AI-OptOut-All-Services"
POLICY_FILE="templates/ai-opt-out-policy.json"

echo "Applying AI opt-out policy..."

ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)

# 1. Enable the policy type only if it isn't enabled yet (no error suppression)
TYPE_STATUS=$(aws organizations describe-organization \
    --query "Organization.AvailablePolicyTypes[?Type=='AISERVICES_OPT_OUT_POLICY'].Status | [0]" \
    --output text)
if [ "$TYPE_STATUS" != "ENABLED" ]; then
    aws organizations enable-policy-type \
        --root-id "$ROOT_ID" \
        --policy-type AISERVICES_OPT_OUT_POLICY
    echo "Policy type enabled"
else
    echo "Policy type already enabled"
fi

# 2. Create the policy, or reconcile its content if it drifted (convergent)
POLICY_ID=$(aws organizations list-policies \
    --filter AISERVICES_OPT_OUT_POLICY \
    --query "Policies[?Name=='${POLICY_NAME}'].Id | [0]" \
    --output text)

DESIRED=$(python3 -c "import json;print(json.dumps(json.load(open('${POLICY_FILE}')),sort_keys=True,separators=(',',':')))")

if [ "$POLICY_ID" = "None" ] || [ -z "$POLICY_ID" ]; then
    POLICY_ID=$(aws organizations create-policy \
        --name "$POLICY_NAME" \
        --description "Opt out of AI service data usage (child overrides locked)" \
        --type AISERVICES_OPT_OUT_POLICY \
        --content "file://${POLICY_FILE}" \
        --query 'Policy.PolicySummary.Id' \
        --output text)
    echo "Created policy ${POLICY_ID}"
else
    CURRENT=$(aws organizations describe-policy --policy-id "$POLICY_ID" \
        --query 'Policy.Content' --output text \
        | python3 -c "import json,sys;print(json.dumps(json.loads(sys.stdin.read()),sort_keys=True,separators=(',',':')))")
    if [ "$CURRENT" != "$DESIRED" ]; then
        aws organizations update-policy --policy-id "$POLICY_ID" --content "file://${POLICY_FILE}"
        echo "Policy ${POLICY_ID} content reconciled (was drifted)"
    else
        echo "Policy ${POLICY_ID} content already correct"
    fi
fi

# 3. Attach to root only if not attached (no error suppression)
ATTACHED=$(aws organizations list-policies-for-target \
    --target-id "$ROOT_ID" \
    --filter AISERVICES_OPT_OUT_POLICY \
    --query "Policies[?Id=='${POLICY_ID}'].Id | [0]" \
    --output text)
if [ "$ATTACHED" = "None" ] || [ -z "$ATTACHED" ]; then
    aws organizations attach-policy --policy-id "$POLICY_ID" --target-id "$ROOT_ID"
    echo "Policy attached to root ${ROOT_ID}"
else
    echo "Policy already attached to root ${ROOT_ID}"
fi

# 4. Fail-closed gate: verify effective policy for every account
python3 scripts/verify_ai_opt_out.py

echo "AI opt-out policy applied and verified"
