#!/usr/bin/env python3
"""Fail-closed structural and semantic validator for BADF G01 PRD candidates.

This validator proves that a PRD candidate is complete enough to request an
independent G01 decision. It never issues PRD_BASELINED and never substitutes
for product-owner approval or a BADF gate dossier.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
GATE = "G01"
PRD_ID = re.compile(r"^PRD-[A-Za-z0-9._-]+$")
APPROVAL_STATES = {"PENDING", "APPROVED", "REJECTED"}
BASELINE_STATUSES = {"DRAFT", "CANDIDATE", "APPROVAL_PENDING", "APPROVED", "REJECTED"}
CHALLENGE_DISPOSITIONS = {"RESOLVED", "ACCEPTED_AS_RISK", "BLOCKING"}
SEVERITIES = {"Critical", "Major", "Minor"}
PLACEHOLDER_VALUES = {"TBD", "TODO", "REPLACE_ME", "__REQUIRED__", "DECLARED_MISSING"}


class ValidationError(Exception):
    pass


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load PRD JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError("PRD document must be a JSON object")
    return value


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    text = value.strip()
    if text.upper() in PLACEHOLDER_VALUES or (text.startswith("<") and text.endswith(">")):
        raise ValidationError(f"{label} contains an unresolved placeholder")
    return text


def require_text_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be an array")
    if not allow_empty and not value:
        raise ValidationError(f"{label} must not be empty")
    out: list[str] = []
    for index, item in enumerate(value):
        out.append(require_text(item, f"{label}[{index}]"))
    return out


def require_fields(obj: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(obj))
    if missing:
        raise ValidationError(f"{label} missing fields: {', '.join(missing)}")


def require_iso8601(value: Any, label: str) -> str:
    text = require_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label} must include a timezone")
    return text


def require_unique_ids(items: Any, label: str, required: set[str]) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValidationError(f"{label} must be a non-empty array")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        obj = require_object(item, f"{label}[{index}]")
        require_fields(obj, required | {"id"}, f"{label}[{index}]")
        ident = require_text(obj["id"], f"{label}[{index}].id")
        key = ident.casefold()
        if key in seen:
            raise ValidationError(f"{label} contains duplicate id {ident!r}")
        seen.add(key)
        out.append(obj)
    return out


def validate_document(doc: dict[str, Any]) -> dict[str, Any]:
    required_top = {
        "schema_version", "id", "gate", "product", "overview", "problem",
        "target_users", "value_proposition", "vision", "objectives", "scope",
        "capabilities", "differentiation", "success_metrics", "stakeholders",
        "assumptions", "constraints", "raid", "legal_regulatory_data",
        "acceptance_criteria", "challenge", "baseline", "evidence_refs",
    }
    require_fields(doc, required_top, "prd")

    if doc["schema_version"] != SCHEMA_VERSION:
        raise ValidationError(f"schema_version must be {SCHEMA_VERSION}")
    if doc["gate"] != GATE:
        raise ValidationError(f"gate must be {GATE}")
    prd_id = require_text(doc["id"], "prd.id")
    if not PRD_ID.fullmatch(prd_id):
        raise ValidationError("prd.id must match ^PRD-[A-Za-z0-9._-]+$")

    product = require_object(doc["product"], "prd.product")
    require_fields(product, {"name", "type", "stage", "owner", "target_market"}, "prd.product")
    for field in ("name", "type", "stage", "owner", "target_market"):
        require_text(product[field], f"prd.product.{field}")
    require_text(doc["overview"], "prd.overview")

    problem = require_object(doc["problem"], "prd.problem")
    require_fields(problem, {"statement", "affected_users", "current_limitations", "business_impact", "why_now"}, "prd.problem")
    require_text(problem["statement"], "prd.problem.statement")
    require_text_list(problem["affected_users"], "prd.problem.affected_users")
    require_text_list(problem["current_limitations"], "prd.problem.current_limitations")
    require_text_list(problem["business_impact"], "prd.problem.business_impact")
    require_text(problem["why_now"], "prd.problem.why_now")

    target_users = doc["target_users"]
    if not isinstance(target_users, list) or not target_users:
        raise ValidationError("prd.target_users must be a non-empty array")
    for index, user in enumerate(target_users):
        obj = require_object(user, f"prd.target_users[{index}]")
        require_fields(obj, {"segment", "role", "needs", "pain_points"}, f"prd.target_users[{index}]")
        require_text(obj["segment"], f"prd.target_users[{index}].segment")
        require_text(obj["role"], f"prd.target_users[{index}].role")
        require_text_list(obj["needs"], f"prd.target_users[{index}].needs")
        require_text_list(obj["pain_points"], f"prd.target_users[{index}].pain_points")

    value = require_object(doc["value_proposition"], "prd.value_proposition")
    require_fields(value, {"statement", "benefits"}, "prd.value_proposition")
    require_text(value["statement"], "prd.value_proposition.statement")
    require_text_list(value["benefits"], "prd.value_proposition.benefits")
    require_text(doc["vision"], "prd.vision")

    objectives = require_unique_ids(doc["objectives"], "prd.objectives", {"statement", "metric_refs"})
    for index, obj in enumerate(objectives):
        require_text(obj["statement"], f"prd.objectives[{index}].statement")
        require_text_list(obj["metric_refs"], f"prd.objectives[{index}].metric_refs")

    scope = require_object(doc["scope"], "prd.scope")
    require_fields(scope, {"in_scope", "out_of_scope"}, "prd.scope")
    in_scope = require_text_list(scope["in_scope"], "prd.scope.in_scope")
    out_scope = require_text_list(scope["out_of_scope"], "prd.scope.out_of_scope")
    overlap = {item.casefold() for item in in_scope} & {item.casefold() for item in out_scope}
    if overlap:
        raise ValidationError("prd.scope contains the same item in in_scope and out_of_scope")

    capabilities = doc["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ValidationError("prd.capabilities must be a non-empty array")
    for index, item in enumerate(capabilities):
        obj = require_object(item, f"prd.capabilities[{index}]")
        require_fields(obj, {"name", "description", "priority"}, f"prd.capabilities[{index}]")
        require_text(obj["name"], f"prd.capabilities[{index}].name")
        require_text(obj["description"], f"prd.capabilities[{index}].description")
        require_text(obj["priority"], f"prd.capabilities[{index}].priority")

    require_text_list(doc["differentiation"], "prd.differentiation")

    metrics = require_unique_ids(doc["success_metrics"], "prd.success_metrics", {"name", "baseline", "target", "measurement"})
    metric_ids = {m["id"] for m in metrics}
    for index, metric in enumerate(metrics):
        for field in ("name", "baseline", "target", "measurement"):
            require_text(metric[field], f"prd.success_metrics[{index}].{field}")
    for index, objective in enumerate(objectives):
        unknown = set(objective["metric_refs"]) - metric_ids
        if unknown:
            raise ValidationError(f"prd.objectives[{index}].metric_refs references unknown metrics: {', '.join(sorted(unknown))}")

    stakeholders = doc["stakeholders"]
    if not isinstance(stakeholders, list) or not stakeholders:
        raise ValidationError("prd.stakeholders must be a non-empty array")
    for index, item in enumerate(stakeholders):
        obj = require_object(item, f"prd.stakeholders[{index}]")
        require_fields(obj, {"role", "accountability"}, f"prd.stakeholders[{index}]")
        require_text(obj["role"], f"prd.stakeholders[{index}].role")
        require_text(obj["accountability"], f"prd.stakeholders[{index}].accountability")

    require_text_list(doc["assumptions"], "prd.assumptions", allow_empty=True)
    require_text_list(doc["constraints"], "prd.constraints", allow_empty=True)

    raid = require_object(doc["raid"], "prd.raid")
    require_fields(raid, {"risks", "assumptions", "issues", "dependencies"}, "prd.raid")
    for field in ("risks", "assumptions", "issues", "dependencies"):
        require_text_list(raid[field], f"prd.raid.{field}", allow_empty=True)

    legal = require_object(doc["legal_regulatory_data"], "prd.legal_regulatory_data")
    require_fields(legal, {"legal", "regulatory", "data_classification", "privacy"}, "prd.legal_regulatory_data")
    require_text_list(legal["legal"], "prd.legal_regulatory_data.legal", allow_empty=True)
    require_text_list(legal["regulatory"], "prd.legal_regulatory_data.regulatory", allow_empty=True)
    require_text(legal["data_classification"], "prd.legal_regulatory_data.data_classification")
    require_text_list(legal["privacy"], "prd.legal_regulatory_data.privacy", allow_empty=True)

    acceptance = require_unique_ids(doc["acceptance_criteria"], "prd.acceptance_criteria", {"statement", "verification"})
    for index, item in enumerate(acceptance):
        require_text(item["statement"], f"prd.acceptance_criteria[{index}].statement")
        require_text(item["verification"], f"prd.acceptance_criteria[{index}].verification")

    challenge = require_object(doc["challenge"], "prd.challenge")
    require_fields(challenge, {"method", "sources_consulted", "findings", "unresolved_decisions"}, "prd.challenge")
    require_text(challenge["method"], "prd.challenge.method")
    require_text_list(challenge["sources_consulted"], "prd.challenge.sources_consulted", allow_empty=True)
    require_text_list(challenge["unresolved_decisions"], "prd.challenge.unresolved_decisions", allow_empty=True)
    findings = challenge["findings"]
    if not isinstance(findings, list):
        raise ValidationError("prd.challenge.findings must be an array")
    blocking: list[str] = []
    for index, finding in enumerate(findings):
        obj = require_object(finding, f"prd.challenge.findings[{index}]")
        require_fields(obj, {"id", "severity", "finding", "disposition", "evidence"}, f"prd.challenge.findings[{index}]")
        ident = require_text(obj["id"], f"prd.challenge.findings[{index}].id")
        severity = require_text(obj["severity"], f"prd.challenge.findings[{index}].severity")
        disposition = require_text(obj["disposition"], f"prd.challenge.findings[{index}].disposition")
        require_text(obj["finding"], f"prd.challenge.findings[{index}].finding")
        require_text(obj["evidence"], f"prd.challenge.findings[{index}].evidence")
        if severity not in SEVERITIES:
            raise ValidationError(f"challenge finding {ident} has invalid severity {severity!r}")
        if disposition not in CHALLENGE_DISPOSITIONS:
            raise ValidationError(f"challenge finding {ident} has invalid disposition {disposition!r}")
        if disposition == "BLOCKING":
            blocking.append(ident)

    baseline = require_object(doc["baseline"], "prd.baseline")
    require_fields(baseline, {"version", "source_revision", "created_at", "author", "status", "approval"}, "prd.baseline")
    for field in ("version", "source_revision", "author"):
        require_text(baseline[field], f"prd.baseline.{field}")
    require_iso8601(baseline["created_at"], "prd.baseline.created_at")
    status = require_text(baseline["status"], "prd.baseline.status")
    if status not in BASELINE_STATUSES:
        raise ValidationError(f"prd.baseline.status must be one of {sorted(BASELINE_STATUSES)}")

    approval = require_object(baseline["approval"], "prd.baseline.approval")
    require_fields(approval, {"required_role", "state", "approver", "approved_at", "evidence_refs"}, "prd.baseline.approval")
    if require_text(approval["required_role"], "prd.baseline.approval.required_role") != "product_owner":
        raise ValidationError("prd.baseline.approval.required_role must be product_owner")
    state = require_text(approval["state"], "prd.baseline.approval.state")
    if state not in APPROVAL_STATES:
        raise ValidationError(f"prd.baseline.approval.state must be one of {sorted(APPROVAL_STATES)}")
    refs = require_text_list(approval["evidence_refs"], "prd.baseline.approval.evidence_refs", allow_empty=True)
    author = baseline["author"].strip().casefold()
    if state == "APPROVED":
        approver = require_text(approval["approver"], "prd.baseline.approval.approver")
        require_iso8601(approval["approved_at"], "prd.baseline.approval.approved_at")
        if not refs:
            raise ValidationError("approved PRD baseline must carry approval evidence_refs")
        if approver.casefold() == author:
            raise ValidationError("PRD author cannot provide the independent G01 approval recorded on the same candidate")
    else:
        if approval["approver"] is not None or approval["approved_at"] is not None:
            raise ValidationError("non-approved PRD must keep approver and approved_at null")

    require_text_list(doc["evidence_refs"], "prd.evidence_refs", allow_empty=True)

    unresolved = list(challenge["unresolved_decisions"])
    if blocking or unresolved:
        return {
            "status": "REWORK_REQUIRED",
            "prd_id": prd_id,
            "gate": GATE,
            "blocking_findings": blocking,
            "unresolved_decisions": unresolved,
            "authority": "NO_GATE_AUTHORITY",
        }
    return {
        "status": "ELIGIBLE_FOR_G01_REVIEW",
        "prd_id": prd_id,
        "gate": GATE,
        "approval_state": state,
        "authority": "NO_GATE_AUTHORITY",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    try:
        result = validate_document(load_json(args.path))
    except ValidationError as exc:
        print(f"BADF PRD FAIL: {exc}", file=sys.stderr)
        return 2
    if args.json_output:
        print(json.dumps(result, sort_keys=True))
    elif result["status"] == "REWORK_REQUIRED":
        detail = []
        if result["blocking_findings"]:
            detail.append("blocking=" + ",".join(result["blocking_findings"]))
        if result["unresolved_decisions"]:
            detail.append(f"unresolved={len(result['unresolved_decisions'])}")
        print("BADF PRD REWORK_REQUIRED: " + result["prd_id"] + ("; " + "; ".join(detail) if detail else ""))
    else:
        print(
            f"BADF PRD ELIGIBLE_FOR_G01_REVIEW: {result['prd_id']}; "
            f"approval={result['approval_state']}; authority=NO_GATE_AUTHORITY"
        )
    return 3 if result["status"] == "REWORK_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
