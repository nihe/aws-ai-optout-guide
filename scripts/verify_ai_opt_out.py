#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def verify_ai_opt_out():
    """Verify AI opt-out policies are properly configured"""
    org_client = boto3.client('organizations')
    
    # Check if org exists and AI opt-out is enabled
    try:
        org = org_client.describe_organization()
        print(f"✅ Organization found: {org['Organization']['Id']}")
        
        # Check if AI opt-out policy type is enabled
        policy_types = org['Organization']['AvailablePolicyTypes']
        ai_opt_out_enabled = any(
            pt['Type'] == 'AISERVICES_OPT_OUT_POLICY' and pt['Status'] == 'ENABLED'
            for pt in policy_types
        )
        
        if ai_opt_out_enabled:
            print("✅ AI opt-out policy type is ENABLED")
        else:
            print("❌ AI opt-out policy type is NOT enabled")
            return False
            
        # List all AI opt-out policies
        policies = org_client.list_policies(Filter='AISERVICES_OPT_OUT_POLICY')
        print(f"\n📋 Found {len(policies['Policies'])} AI opt-out policies:")
        
        for policy in policies['Policies']:
            print(f"  - {policy['Name']} (ID: {policy['Id']})")
            
            # Check policy content
            policy_detail = org_client.describe_policy(PolicyId=policy['Id'])
            content = json.loads(policy_detail['Policy']['Content'])
            
            if 'default' in content.get('services', {}):
                print("    ✅ Policy includes 'default' (all services)")
            else:
                print("    ⚠️  Policy doesn't include 'default' service")
                
        # Check all accounts
        print("\n🏢 Checking accounts:")
        accounts = org_client.list_accounts()
        
        for account in accounts['Accounts']:
            if account['Status'] == 'ACTIVE':
                try:
                    effective = org_client.describe_effective_policy(
                        PolicyType='AISERVICES_OPT_OUT_POLICY',
                        TargetId=account['Id']
                    )
                    
                    if effective['EffectivePolicy']:
                        print(f"  ✅ {account['Name']} - Opt-out policy active")
                    else:
                        print(f"  ❌ {account['Name']} - No opt-out policy")
                except Exception as e:
                    print(f"  ⚠️  {account['Name']} - Error checking: {str(e)}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🔍 AWS AI Opt-Out Verification Tool")
    print(f"📅 Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if verify_ai_opt_out():
        print("\n✅ AI opt-out verification completed successfully!")
    else:
        print("\n❌ AI opt-out verification failed - action required!")