import json
import boto3

def lambda_handler(event, context):
    org_client = boto3.client('organizations')
    config_client = boto3.client('config')
    
    # Check if AI opt-out is enabled
    try:
        policies = org_client.list_policies(Filter='AISERVICES_OPT_OUT_POLICY')
        
        if not policies['Policies']:
            return {
                'compliance_type': 'NON_COMPLIANT',
                'annotation': 'No AI opt-out policy found'
            }
        
        # Check if applied to root
        for policy in policies['Policies']:
            targets = org_client.list_targets_for_policy(PolicyId=policy['Id'])
            if any(t['Type'] == 'ROOT' for t in targets['Targets']):
                return {
                    'compliance_type': 'COMPLIANT',
                    'annotation': 'AI opt-out policy properly configured'
                }
        
        return {
            'compliance_type': 'NON_COMPLIANT',
            'annotation': 'AI opt-out policy not attached to root'
        }
        
    except Exception as e:
        return {
            'compliance_type': 'NON_COMPLIANT',
            'annotation': f'Error checking policy: {str(e)}'
        }