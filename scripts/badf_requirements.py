#!/usr/bin/env python3
"""Fail-closed structural validator for BADF Gate G02 Requirements Traceability Matrices."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PLACEHOLDER_WORDS = {"TBD", "TODO", "UNKNOWN", "REPLACE_ME", "__REQUIRED__", "DECLARED_MISSING"}
ID_PATTERNS = {
    "objective": re.compile(r"^OBJ-[A-Za-z0-9._-]+$"),
    "capability": re.compile(r"^CAP-[A-Za-z0-9._-]+$"),
    "epic": re.compile(r"^EPIC-[A-Za-z0-9._-]+$"),
    "requirement": re.compile(r"^REQ-[A-Za-z0-9._-]+$"),
    "nfr": re.compile(r"^NFR-[A-Za-z0-9._-]+$"),
    "acceptance": re.compile(r"^AC-[A-Za-z0-9._-]+$"),
    "test": re.compile(r"^TEST-[A-Za-z0-9._-]+$"),
    "evidence": re.compile(r"^EVDREQ-[A-Za-z0-9._-]+$"),
    "source": re.compile(r"^SRC-[A-Za-z0-9._-]+$"),
}
NODE_GROUPS = {
    "capabilities": "capability",
    "epics": "epic",
    "requirements": "requirement",
    "nfrs": "nfr",
    "acceptance_criteria": "acceptance",
    "test_obligations": "test",
    "evidence_requirements": "evidence",
    "security_sources": "source",
}
ALLOWED_LINKS = {
    "OBJECTIVE_TO_CAPABILITY": ("objective", "capability"),
    "CAPABILITY_TO_EPIC": ("capability", "epic"),
    "EPIC_TO_REQUIREMENT": ("epic", "requirement"),
    "REQUIREMENT_TO_NFR": ("requirement", "nfr"),
    "REQUIREMENT_TO_ACCEPTANCE": ("requirement", "acceptance"),
    "NFR_TO_ACCEPTANCE": ("nfr", "acceptance"),
    "ACCEPTANCE_TO_TEST": ("acceptance", "test"),
    "TEST_TO_EVIDENCE": ("test", "evidence"),
    "SOURCE_TO_REQUIREMENT": ("source", "requirement"),
}
REQUIREMENT_TYPES = {"FUNCTIONAL", "DATA", "SECURITY", "COMPLIANCE", "OPERABILITY"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
NFR_CATEGORIES = {"PERFORMANCE", "AVAILABILITY", "SECURITY", "PRIVACY", "SCALABILITY", "RESILIENCE",
                  "ACCESSIBILITY", "OBSERVABILITY", "COST", "DATA", "COMPATIBILITY", "OTHER"}
OPERATORS = {"<", "<=", ">", ">=", "=="}
SOURCE_KINDS = {"THREAT", "COMPLIANCE", "PRIVACY", "ABUSE_CASE"}
DEPENDENCY_KINDS = {"REQUIRES", "SEQUENCES_AFTER", "EXTERNAL_BLOCKER"}
DEPENDENCY_STATUSES = {"MAPPED", "RESOLVED", "BLOCKED"}
DECISION_STATUSES = {"OPEN", "RESOLVED"}
FINDING_LENSES = {"CLARITY", "SCOPE", "TRACEABILITY", "TESTABILITY", "SECURITY", "COMPLIANCE", "DEPENDENCY", "OTHER"}
FINDING_SEVERITIES = {"BLOCKING", "NON_BLOCKING"}
FINDING_STATUSES = {"OPEN", "RESOLVED"}
PRINCIPAL_TYPES = {"human", "agent", "service", "controller"}


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
        raise ValidationError(f"cannot load RTM JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError("RTM root must be a JSON object")
    return value


def require_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(value))
    if missing:
        raise ValidationError(f"{label} missing fields: {', '.join(missing)}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    return value


def scan_placeholders(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_placeholders(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan_placeholders(child, f"{path}[{i}]")
    elif isinstance(value, str):
        stripped = value.strip()
        upper = stripped.upper()
        if upper in PLACEHOLDER_WORDS or "__REQUIRED__" in upper or re.search(r"<[^>]+>", stripped):
            raise ValidationError(f"{path} contains unresolved placeholder {value!r}")


def check_id(value: Any, kind: str, label: str) -> str:
    text = require_string(value, label)
    if not ID_PATTERNS[kind].fullmatch(text):
        raise ValidationError(f"{label} {text!r} is not a canonical {kind} id")
    return text


def _require_list(value: Any, label: str, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be an array")
    if not value and not allow_empty:
        raise ValidationError(f"{label} must not be empty")
    return value


def _register_nodes(doc: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, Any]], list[str]]:
    prd = doc["prd_baseline"]
    require_fields(prd, {"id", "version", "artifact", "digest", "gate", "disposition", "approval_evidence_refs", "objectives"}, "prd_baseline")
    for key in ("id", "version", "artifact", "digest"):
        require_string(prd[key], f"prd_baseline.{key}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", prd["digest"]):
        raise ValidationError("prd_baseline.digest must be sha256:<64 lowercase hex>")
    if prd["gate"] != "G01":
        raise ValidationError("prd_baseline.gate must be G01")
    if prd["disposition"] not in {"APPROVED", "APPROVED_WITH_CONDITIONS"}:
        raise ValidationError("prd_baseline.disposition must establish an approved G01 baseline")
    refs = _require_list(prd["approval_evidence_refs"], "prd_baseline.approval_evidence_refs")
    for i, ref in enumerate(refs):
        require_string(ref, f"prd_baseline.approval_evidence_refs[{i}]")

    kinds: dict[str, str] = {}
    payloads: dict[str, dict[str, Any]] = {}
    objectives: list[str] = []
    for i, obj in enumerate(_require_list(prd["objectives"], "prd_baseline.objectives")):
        if not isinstance(obj, dict):
            raise ValidationError(f"prd_baseline.objectives[{i}] must be an object")
        require_fields(obj, {"id", "statement"}, f"prd_baseline.objectives[{i}]")
        oid = check_id(obj["id"], "objective", f"prd_baseline.objectives[{i}].id")
        require_string(obj["statement"], f"prd_baseline.objectives[{i}].statement")
        if oid in kinds:
            raise ValidationError(f"duplicate node id {oid}")
        kinds[oid] = "objective"
        payloads[oid] = obj
        objectives.append(oid)

    nodes = doc["nodes"]
    if not isinstance(nodes, dict):
        raise ValidationError("nodes must be an object")
    require_fields(nodes, set(NODE_GROUPS), "nodes")
    extra_groups = sorted(set(nodes) - set(NODE_GROUPS))
    if extra_groups:
        raise ValidationError("nodes has unknown groups: " + ", ".join(extra_groups))

    for group, kind in NODE_GROUPS.items():
        allow_empty = group == "security_sources"
        items = _require_list(nodes[group], f"nodes.{group}", allow_empty=allow_empty)
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValidationError(f"nodes.{group}[{i}] must be an object")
            nid = check_id(item.get("id"), kind, f"nodes.{group}[{i}].id")
            if nid in kinds:
                raise ValidationError(f"duplicate node id {nid}")
            kinds[nid] = kind
            payloads[nid] = item

            if kind == "capability":
                require_fields(item, {"id", "statement", "rationale"}, f"capability {nid}")
                require_string(item["statement"], f"{nid}.statement"); require_string(item["rationale"], f"{nid}.rationale")
            elif kind == "epic":
                require_fields(item, {"id", "statement", "value", "priority"}, f"epic {nid}")
                require_string(item["statement"], f"{nid}.statement"); require_string(item["value"], f"{nid}.value")
                if item["priority"] not in PRIORITIES: raise ValidationError(f"{nid}.priority invalid")
            elif kind == "requirement":
                require_fields(item, {"id", "type", "statement", "rationale", "priority", "security_sensitive"}, f"requirement {nid}")
                require_string(item["statement"], f"{nid}.statement"); require_string(item["rationale"], f"{nid}.rationale")
                if item["type"] not in REQUIREMENT_TYPES: raise ValidationError(f"{nid}.type invalid")
                if item["priority"] not in PRIORITIES: raise ValidationError(f"{nid}.priority invalid")
                if not isinstance(item["security_sensitive"], bool): raise ValidationError(f"{nid}.security_sensitive must be boolean")
            elif kind == "nfr":
                require_fields(item, {"id", "category", "statement", "metric", "operator", "target", "unit", "measurement_method"}, f"NFR {nid}")
                for k in ("statement", "metric", "unit", "measurement_method"): require_string(item[k], f"{nid}.{k}")
                if item["category"] not in NFR_CATEGORIES: raise ValidationError(f"{nid}.category invalid")
                if item["operator"] not in OPERATORS: raise ValidationError(f"{nid}.operator invalid")
                if not isinstance(item["target"], (int, float)) or isinstance(item["target"], bool): raise ValidationError(f"{nid}.target must be numeric")
            elif kind == "acceptance":
                require_fields(item, {"id", "statement", "pass_condition"}, f"acceptance {nid}")
                require_string(item["statement"], f"{nid}.statement"); require_string(item["pass_condition"], f"{nid}.pass_condition")
            elif kind == "test":
                require_fields(item, {"id", "level", "statement", "expected_evidence_type"}, f"test {nid}")
                require_string(item["level"], f"{nid}.level"); require_string(item["statement"], f"{nid}.statement")
                require_string(item["expected_evidence_type"], f"{nid}.expected_evidence_type")
            elif kind == "evidence":
                require_fields(item, {"id", "evidence_type", "claim"}, f"evidence requirement {nid}")
                require_string(item["evidence_type"], f"{nid}.evidence_type"); require_string(item["claim"], f"{nid}.claim")
            elif kind == "source":
                require_fields(item, {"id", "kind", "reference", "statement", "requires_requirement"}, f"source {nid}")
                if item["kind"] not in SOURCE_KINDS: raise ValidationError(f"{nid}.kind invalid")
                require_string(item["reference"], f"{nid}.reference"); require_string(item["statement"], f"{nid}.statement")
                if not isinstance(item["requires_requirement"], bool): raise ValidationError(f"{nid}.requires_requirement must be boolean")
    return kinds, payloads, objectives


def _check_links(doc: dict[str, Any], kinds: dict[str, str], payloads: dict[str, dict[str, Any]], objectives: list[str]) -> dict[str, Any]:
    incoming: dict[str, list[tuple[str, str]]] = defaultdict(list)
    outgoing: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for i, link in enumerate(_require_list(doc["links"], "links")):
        if not isinstance(link, dict):
            raise ValidationError(f"links[{i}] must be an object")
        require_fields(link, {"from", "to", "type"}, f"links[{i}]")
        src = require_string(link["from"], f"links[{i}].from")
        dst = require_string(link["to"], f"links[{i}].to")
        typ = require_string(link["type"], f"links[{i}].type")
        if src not in kinds or dst not in kinds:
            raise ValidationError(f"links[{i}] references unknown node {src!r}->{dst!r}")
        if typ not in ALLOWED_LINKS:
            raise ValidationError(f"links[{i}].type {typ!r} is not canonical")
        expected = ALLOWED_LINKS[typ]
        actual = (kinds[src], kinds[dst])
        if actual != expected:
            raise ValidationError(f"links[{i}] {typ} requires {expected[0]}->{expected[1]}, got {actual[0]}->{actual[1]}")
        key = (src, dst, typ)
        if key in seen:
            raise ValidationError(f"duplicate link {src}->{dst} ({typ})")
        seen.add(key)
        outgoing[src].append((dst, typ))
        incoming[dst].append((src, typ))

    def has_out(node: str, typ: str) -> bool:
        return any(t == typ for _, t in outgoing[node])
    def has_in(node: str, typ: str) -> bool:
        return any(t == typ for _, t in incoming[node])

    for oid in objectives:
        if not has_out(oid, "OBJECTIVE_TO_CAPABILITY"):
            raise ValidationError(f"orphan PRD objective {oid}: no capability")
    for nid, kind in kinds.items():
        if kind == "capability":
            if not has_in(nid, "OBJECTIVE_TO_CAPABILITY") or not has_out(nid, "CAPABILITY_TO_EPIC"):
                raise ValidationError(f"{nid} lacks objective upstream or epic downstream coverage")
        elif kind == "epic":
            if not has_in(nid, "CAPABILITY_TO_EPIC") or not has_out(nid, "EPIC_TO_REQUIREMENT"):
                raise ValidationError(f"{nid} lacks capability upstream or requirement downstream coverage")
        elif kind == "requirement":
            if not has_in(nid, "EPIC_TO_REQUIREMENT"):
                raise ValidationError(f"{nid} has no epic parent")
            if not has_out(nid, "REQUIREMENT_TO_NFR"):
                raise ValidationError(f"{nid} has no quantified NFR overlay")
            if not has_out(nid, "REQUIREMENT_TO_ACCEPTANCE"):
                raise ValidationError(f"{nid} has no acceptance criterion")
            item = payloads[nid]
            if item["security_sensitive"] or item["type"] in {"SECURITY", "COMPLIANCE"}:
                if not has_in(nid, "SOURCE_TO_REQUIREMENT"):
                    raise ValidationError(f"{nid} is security/compliance-sensitive but has no source provenance")
        elif kind == "nfr":
            if not has_in(nid, "REQUIREMENT_TO_NFR") or not has_out(nid, "NFR_TO_ACCEPTANCE"):
                raise ValidationError(f"{nid} lacks requirement upstream or acceptance downstream coverage")
        elif kind == "acceptance":
            if not (has_in(nid, "REQUIREMENT_TO_ACCEPTANCE") or has_in(nid, "NFR_TO_ACCEPTANCE")):
                raise ValidationError(f"{nid} has no requirement/NFR parent")
            if not has_out(nid, "ACCEPTANCE_TO_TEST"):
                raise ValidationError(f"{nid} has no test obligation")
        elif kind == "test":
            if not has_in(nid, "ACCEPTANCE_TO_TEST") or not has_out(nid, "TEST_TO_EVIDENCE"):
                raise ValidationError(f"{nid} lacks acceptance upstream or evidence downstream coverage")
        elif kind == "evidence":
            if not has_in(nid, "TEST_TO_EVIDENCE"):
                raise ValidationError(f"{nid} has no test parent")
        elif kind == "source":
            if payloads[nid]["requires_requirement"] and not has_out(nid, "SOURCE_TO_REQUIREMENT"):
                raise ValidationError(f"{nid} requires a derived requirement but drives none")

    return {"incoming": incoming, "outgoing": outgoing, "links": len(seen)}


def _check_dependencies(doc: dict[str, Any], kinds: dict[str, str]) -> list[str]:
    blockers: list[str] = []
    graph: dict[str, list[str]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for i, dep in enumerate(_require_list(doc["dependencies"], "dependencies", allow_empty=True)):
        if not isinstance(dep, dict):
            raise ValidationError(f"dependencies[{i}] must be an object")
        require_fields(dep, {"from_requirement", "to_requirement", "kind", "status"}, f"dependencies[{i}]")
        src = require_string(dep["from_requirement"], f"dependencies[{i}].from_requirement")
        dst = require_string(dep["to_requirement"], f"dependencies[{i}].to_requirement")
        if kinds.get(src) != "requirement" or kinds.get(dst) != "requirement":
            raise ValidationError(f"dependencies[{i}] must reference known requirement ids")
        if src == dst:
            raise ValidationError(f"dependencies[{i}] is self-referential")
        if dep["kind"] not in DEPENDENCY_KINDS:
            raise ValidationError(f"dependencies[{i}].kind invalid")
        if dep["status"] not in DEPENDENCY_STATUSES:
            raise ValidationError(f"dependencies[{i}].status invalid")
        key = (src, dst, dep["kind"])
        if key in seen:
            raise ValidationError(f"duplicate dependency {src}->{dst} ({dep['kind']})")
        seen.add(key)
        graph[src].append(dst)
        if dep["status"] == "BLOCKED":
            blockers.append(f"dependency:{src}->{dst}")

    visiting: set[str] = set()
    visited: set[str] = set()
    def dfs(node: str) -> None:
        if node in visiting:
            raise ValidationError(f"requirement dependency cycle detected at {node}")
        if node in visited:
            return
        visiting.add(node)
        for nxt in graph[node]:
            dfs(nxt)
        visiting.remove(node)
        visited.add(node)
    for node in list(graph):
        dfs(node)
    return blockers


def _check_decisions_and_findings(doc: dict[str, Any], kinds: dict[str, str]) -> list[str]:
    blockers: list[str] = []
    decision_ids: set[str] = set()
    for i, dec in enumerate(_require_list(doc["decisions"], "decisions", allow_empty=True)):
        if not isinstance(dec, dict):
            raise ValidationError(f"decisions[{i}] must be an object")
        require_fields(dec, {"id", "status", "statement", "owner", "resolution"}, f"decisions[{i}]")
        did = require_string(dec["id"], f"decisions[{i}].id")
        if did in decision_ids: raise ValidationError(f"duplicate decision id {did}")
        decision_ids.add(did)
        if dec["status"] not in DECISION_STATUSES: raise ValidationError(f"{did}.status invalid")
        require_string(dec["statement"], f"{did}.statement"); require_string(dec["owner"], f"{did}.owner")
        if dec["status"] == "OPEN":
            blockers.append(f"decision:{did}")
        else:
            require_string(dec["resolution"], f"{did}.resolution")

    finding_ids: set[str] = set()
    for i, finding in enumerate(_require_list(doc["review_findings"], "review_findings", allow_empty=True)):
        if not isinstance(finding, dict):
            raise ValidationError(f"review_findings[{i}] must be an object")
        require_fields(finding, {"id", "lens", "severity", "status", "statement", "node_refs"}, f"review_findings[{i}]")
        fid = require_string(finding["id"], f"review_findings[{i}].id")
        if fid in finding_ids: raise ValidationError(f"duplicate finding id {fid}")
        finding_ids.add(fid)
        if finding["lens"] not in FINDING_LENSES: raise ValidationError(f"{fid}.lens invalid")
        if finding["severity"] not in FINDING_SEVERITIES: raise ValidationError(f"{fid}.severity invalid")
        if finding["status"] not in FINDING_STATUSES: raise ValidationError(f"{fid}.status invalid")
        require_string(finding["statement"], f"{fid}.statement")
        refs = _require_list(finding["node_refs"], f"{fid}.node_refs", allow_empty=True)
        for ref in refs:
            if ref not in kinds: raise ValidationError(f"{fid} references unknown node {ref!r}")
        if finding["severity"] == "BLOCKING" and finding["status"] == "OPEN":
            blockers.append(f"finding:{fid}")
    return blockers


def validate(doc: dict[str, Any]) -> dict[str, Any]:
    require_fields(doc, {"schema_version", "rtm_id", "work_package_id", "gate", "prd_baseline", "nodes",
                         "links", "dependencies", "decisions", "review_findings", "author"}, "RTM")
    extra = sorted(set(doc) - {"schema_version", "rtm_id", "work_package_id", "gate", "prd_baseline", "nodes",
                               "links", "dependencies", "decisions", "review_findings", "author"})
    if extra:
        raise ValidationError("RTM has unknown fields: " + ", ".join(extra))
    if doc["schema_version"] != "1.0.0": raise ValidationError("schema_version must be 1.0.0")
    if not re.fullmatch(r"RTM-[A-Za-z0-9._-]+", require_string(doc["rtm_id"], "rtm_id")):
        raise ValidationError("rtm_id is not canonical")
    if not re.fullmatch(r"WP-[A-Za-z0-9._-]+", require_string(doc["work_package_id"], "work_package_id")):
        raise ValidationError("work_package_id is not canonical")
    if doc["gate"] != "G02": raise ValidationError("gate must be G02")

    author = doc["author"]
    if not isinstance(author, dict): raise ValidationError("author must be an object")
    require_fields(author, {"id", "principal_type"}, "author")
    require_string(author["id"], "author.id")
    if author["principal_type"] not in PRINCIPAL_TYPES: raise ValidationError("author.principal_type invalid")

    scan_placeholders(doc)
    kinds, payloads, objectives = _register_nodes(doc)
    graph = _check_links(doc, kinds, payloads, objectives)
    blockers = _check_dependencies(doc, kinds)
    blockers.extend(_check_decisions_and_findings(doc, kinds))

    counts = {kind: sum(1 for k in kinds.values() if k == kind)
              for kind in ("objective","capability","epic","requirement","nfr","acceptance","test","evidence","source")}
    return {
        "rtm_id": doc["rtm_id"],
        "work_package_id": doc["work_package_id"],
        "counts": counts,
        "links": graph["links"],
        "blockers": sorted(blockers),
        "disposition": "REWORK_REQUIRED" if blockers else "ELIGIBLE_FOR_G02_REVIEW",
        "authority": "NO_GATE_AUTHORITY",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rtm", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate(load_json(args.rtm))
    except ValidationError as exc:
        print(f"BADF REQUIREMENTS FAIL: {exc}", file=sys.stderr)
        return 2
    counts = ",".join(f"{k}={v}" for k, v in report["counts"].items())
    if report["disposition"] == "REWORK_REQUIRED":
        print("BADF REQUIREMENTS REWORK_REQUIRED: "
              f"{report['rtm_id']} blockers={','.join(report['blockers'])}; {counts}; "
              "authority=NO_GATE_AUTHORITY")
        return 3
    print("BADF REQUIREMENTS ELIGIBLE_FOR_G02_REVIEW: "
          f"{report['rtm_id']} links={report['links']}; {counts}; authority=NO_GATE_AUTHORITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
