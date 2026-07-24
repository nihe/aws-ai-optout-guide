#!/usr/bin/env python3
"""CDK app for the AI Services opt-out policy.

Usage (from templates/cdk/, in the Organizations management account):
    pip install -r requirements.txt
    cdk deploy -c root_id=r-ab12
"""
import aws_cdk as cdk

from ai_opt_out_stack import AIOptOutStack

app = cdk.App()
root_id = app.node.try_get_context("root_id")
AIOptOutStack(app, "AIOptOutStack", root_id=root_id)
app.synth()
