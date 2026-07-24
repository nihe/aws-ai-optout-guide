"""Regression tests for the hardened-policy validators.

Covers the policy-content check in both the verifier and the AWS Config rule —
including the locked-but-optIn case that fooled an earlier implementation.

Run from the repository root:
    pytest tests/
"""
import copy
import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verifier = _load("scripts/verify_ai_opt_out.py", "verify_ai_opt_out")
config_rule = _load("config/aws-config-rule.py", "aws_config_rule")

LOCK = ["@@none"]

HARDENED_OPT_OUT = {
    "services": {
        "@@operators_allowed_for_child_policies": LOCK,
        "default": {
            "@@operators_allowed_for_child_policies": LOCK,
            "opt_out_policy": {
                "@@operators_allowed_for_child_policies": LOCK,
                "@@assign": "optOut",
            },
        },
    }
}

LOCKED_OPT_IN = copy.deepcopy(HARDENED_OPT_OUT)
LOCKED_OPT_IN["services"]["default"]["opt_out_policy"]["@@assign"] = "optIn"

MISSING_ROOT_LOCK = copy.deepcopy(HARDENED_OPT_OUT)
del MISSING_ROOT_LOCK["services"]["@@operators_allowed_for_child_policies"]

MISSING_DEFAULT_LOCK = copy.deepcopy(HARDENED_OPT_OUT)
del MISSING_DEFAULT_LOCK["services"]["default"]["@@operators_allowed_for_child_policies"]

MISSING_SETTING_LOCK = copy.deepcopy(HARDENED_OPT_OUT)
del MISSING_SETTING_LOCK["services"]["default"]["opt_out_policy"][
    "@@operators_allowed_for_child_policies"
]

NO_DEFAULT = {
    "services": {
        "@@operators_allowed_for_child_policies": LOCK,
        "comprehend": {"opt_out_policy": {"@@assign": "optOut"}},
    }
}

WRONG_CASE_VALUE = copy.deepcopy(HARDENED_OPT_OUT)
WRONG_CASE_VALUE["services"]["default"]["opt_out_policy"]["@@assign"] = "optout"

CASES = [
    ("hardened_opt_out", HARDENED_OPT_OUT, True),
    ("locked_opt_in", LOCKED_OPT_IN, False),
    ("missing_root_lock", MISSING_ROOT_LOCK, False),
    ("missing_default_lock", MISSING_DEFAULT_LOCK, False),
    ("missing_setting_lock", MISSING_SETTING_LOCK, False),
    ("no_default", NO_DEFAULT, False),
    ("wrong_case_value", WRONG_CASE_VALUE, False),
    ("empty", {}, False),
]


@pytest.mark.parametrize(("name", "policy", "expected"), CASES)
def test_verifier_is_hardened_opt_out(name, policy, expected):
    assert verifier.is_hardened_opt_out(policy) is expected


@pytest.mark.parametrize(("name", "policy", "expected"), CASES)
def test_config_rule_is_hardened_opt_out(name, policy, expected):
    assert config_rule._is_hardened_opt_out(policy) is expected


def test_repo_template_is_hardened():
    """The shipped policy template must satisfy the shipped validator."""
    content = json.loads((REPO / "templates/ai-opt-out-policy.json").read_text())
    assert verifier.is_hardened_opt_out(content) is True
    assert config_rule._is_hardened_opt_out(content) is True
