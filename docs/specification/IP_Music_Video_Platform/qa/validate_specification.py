#!/usr/bin/env python3
"""Read-only v2 specification checks; writes only the static validation report.

This script does not execute the platform, SQL migrations, API requests, model
calls, customer experiments, kb.py tests, or cost-model tests. A passed check
means only that the specified static property holds in the inspected files.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def validate(root):
    inputs = {}
    checks = []

    def read(relative):
        path = root / relative
        raw = path.read_bytes()
        inputs[relative] = {
            "path": relative,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        return raw.decode("utf-8")

    def load(relative):
        return json.loads(read(relative))

    def check(name, condition, detail="", invalid=None):
        entry = {"check": name, "passed": bool(condition), "detail": detail}
        if invalid:
            entry["invalid_items"] = invalid
        checks.append(entry)

    def references(name, records, key, allowed, identity="id", scalar=False):
        bad = []
        for row in records:
            value = row.get(key, None if scalar else [])
            values = [value] if scalar else value
            if not isinstance(values, list):
                bad.append({"record": row.get(identity), "field": key, "invalid_type": type(values).__name__})
                continue
            for ref in values:
                if ref not in allowed:
                    bad.append({"record": row.get(identity), "field": key, "reference": ref})
        check(name, not bad, f"{len(records)} records inspected; reference existence only.", bad)

    req_doc = load("output/requirements_catalog.json")
    at_doc = load("output/acceptance_tests.json")
    it_doc = load("output/integration_tests.json")
    screen_doc = load("output/screen_catalog.json")
    flow_doc = load("output/user_flows.json")
    eval_doc = load("output/evaluation_protocol.json")
    fixture_doc = load("output/fixture_registry.json")
    trace_doc = load("output/traceability_matrix.json")
    system_doc = load("output/system_and_ux_tests.json")
    source_doc = load("output/source_registry.json")
    bus_doc = load("output/business_requirements.json")
    kmr_doc = load("output/knowledge_management_requirements.json")
    comp_doc = load("output/comparison_protocol.json")
    api = load("output/technical_contracts.openapi.json")
    api_yaml = yaml.safe_load(read("output/technical_contracts.openapi.yaml"))
    sql = read("output/ontology_schema.sql")
    api_req_map = load("research/api_requirement_reference_map.json")

    req = req_doc["requirements"]
    ats, its = at_doc["tests"], it_doc["tests"]
    screens, roles = screen_doc["screens"], screen_doc["roles"]
    flows = flow_doc["flows"]
    metrics, experiments, cases = eval_doc["metrics"], eval_doc["experiments"], eval_doc["test_cases"]
    fixtures, traces = fixture_doc["fixtures"], trace_doc["rows"]
    sources = source_doc["sources"]
    bus, kmr, comparisons = bus_doc["requirements"], kmr_doc["requirements"], comp_doc["experiments"]
    flow_steps = [{"id": f["id"] + ":" + str(s.get("order")), **s} for f in flows for s in f["steps"]]
    operations = []
    for path, item in api["paths"].items():
        for method, op in item.items():
            if method in HTTP_METHODS:
                operations.append({"path": path, "method": method.upper(), **op})
    opmap = {o["operationId"]: o for o in operations}

    groups = {
        "functional_requirements": (req, "id", 96),
        "acceptance_scenarios": (ats, "id", 192),
        "integration_scenarios": (its, "id", 29),
        "screens": (screens, "id", 38),
        "roles": (roles, "id", 9),
        "flows": (flows, "id", 12),
        "flow_steps": (flow_steps, "id", 73),
        "metrics": (metrics, "id", 32),
        "experiments": (experiments, "id", 16),
        "evaluation_cases": (cases, "id", 48),
        "fixtures": (fixtures, "id", 12),
        "trace_rows": (traces, "requirement_id", 96),
        "api_operations": (operations, "operationId", 143),
        "technical_decisions": (system_doc["technical_decisions"], "id", 15),
        "nfr": (system_doc["nonfunctional_requirements"], "id", 15),
        "technical_scenarios": (system_doc["technical_scenarios"], "id", 36),
        "ux_scenarios": (system_doc["ux_scenarios"], "id", 38),
        "source_records": (sources, "id", 92),
        "business_requirements": (bus, "id", 15),
        "knowledge_management_requirements": (kmr, "id", 20),
        "comparison_experiments": (comparisons, "id", 4),
    }
    counts = {}
    for name, (rows, key, expected) in groups.items():
        ids = [r.get(key) for r in rows]
        counts[name] = len(rows)
        duplicate_ids = [i for i, n in Counter(ids).items() if n > 1]
        check(name + " count and unique IDs", len(rows) == expected and None not in ids and not duplicate_ids,
              f"actual={len(rows)}; expected={expected}; unique={len(set(ids))}", duplicate_ids)

    def ids(rows):
        return {r["id"] for r in rows}

    rids, aids, iids = ids(req), ids(ats), ids(its)
    sids, roleids, mids, eids, fids = ids(screens), ids(roles), ids(metrics), ids(experiments), ids(fixtures)
    bids, sourceids, opids = ids(bus), ids(sources), set(opmap)
    check("FR IDs form FR-001..FR-096", rids == {f"FR-{i:03d}" for i in range(1, 97)})
    check("AT IDs form two explicit cases per FR", aids == {f"AT-{i:03d}-{suffix}" for i in range(1, 97) for suffix in ("A", "B")})
    check("trace covers every FR exactly once", {r["requirement_id"] for r in traces} == rids and len(traces) == len(rids))

    for key, allowed in (("screen_ids", sids), ("api_operation_ids", opids), ("test_ids", aids),
                         ("integration_case_ids", iids), ("related_metric_ids", mids), ("related_experiment_ids", eids)):
        references("FR " + key + " exist", req, key, allowed)
    for key, allowed in (("screen_ids", sids), ("operation_ids", opids), ("acceptance_scenario_ids", aids),
                         ("integration_scenario_ids", iids), ("related_metric_ids", mids), ("related_experiment_ids", eids)):
        references("trace " + key + " exist", traces, key, allowed, "requirement_id")
    for label, rows in (("AT", ats), ("IT", its)):
        references(label + " FR references exist", rows, "requirement_ids", rids)
        references(label + " fixture references exist", rows, "fixture_ids", fids)
    references("AT API references exist", ats, "api_operation_ids", opids)
    references("IT experiment references exist", its, "related_experiments", eids)
    references("screen next targets exist", screens, "next_screens", sids)
    references("screen role presets exist", screens, "roles", roleids | {"all", "all_authenticated_roles"})
    references("role home screens exist", roles, "home", sids, scalar=True)
    references("flow role presets exist", flows, "roles", roleids)
    references("flow step screens exist", flow_steps, "screen_id", sids, scalar=True)
    check("flow step order is contiguous per flow", all([s["order"] for s in f["steps"]] == list(range(1, len(f["steps"]) + 1)) for f in flows))
    references("experiment metric references exist", experiments, "metric_ids", mids)
    references("experiment BUS references exist", experiments, "business_requirements", bids)
    references("experiment FR references exist", experiments, "related_requirement_ids", rids)
    references("evaluation case experiment references exist", cases, "experiment_id", eids, scalar=True)
    references("evaluation case FR references exist", cases, "related_requirement_ids", rids)
    references("comparison experiment BUS references exist", comparisons, "requirement_ids", bids)
    references("API FR references exist", operations, "x-related-requirements", rids, "operationId")
    references("API requirement map FR references exist", api_req_map, "requirement_id", rids, "requirement_id", scalar=True)
    references("API requirement map operation references exist", api_req_map, "operation_ids", opids, "requirement_id")

    by_req = {r["id"]: r for r in req}
    trace_fields = {"screen_ids": "screen_ids", "operation_ids": "api_operation_ids",
                    "acceptance_scenario_ids": "test_ids", "integration_scenario_ids": "integration_case_ids",
                    "related_metric_ids": "related_metric_ids", "related_experiment_ids": "related_experiment_ids"}
    trace_mismatch = []
    for row in traces:
        original = by_req.get(row["requirement_id"])
        if original is None:
            trace_mismatch.append(row["requirement_id"])
            continue
        if any(set(row[a]) != set(original[b]) for a, b in trace_fields.items()):
            trace_mismatch.append(row["requirement_id"])
        if row["baseline_gate"] != original["baseline_gate"] or row["full_release_gate"] != original["release_gate"]:
            trace_mismatch.append(row["requirement_id"] + ":gate")
    check("trace rows match the FR catalog fields and gates", not trace_mismatch, invalid=trace_mismatch)
    atlinks = {rid: {a["id"] for a in ats if rid in a["requirement_ids"]} for rid in rids}
    itlinks = {rid: {t["id"] for t in its if rid in t["requirement_ids"]} for rid in rids}
    check("AT to FR links are reciprocal and two per FR", all(atlinks[r["id"]] == set(r["test_ids"]) and len(atlinks[r["id"]]) == 2 for r in req))
    check("IT to FR links are reciprocal", all(itlinks[r["id"]] == set(r["integration_case_ids"]) for r in req))
    check("release gates and baseline gates are explicit", all(r["release_gate"] in {"G1", "G2", "G3"} and r["baseline_gate"] in {"G1", "G2", "G3"} and r["baseline_scope"] for r in req))
    contract_bad = []
    for test in ats:
        for link in test["planned_contract_references"]:
            op = opmap.get(link["operation_id"])
            if op is None or (link["path"], link["method"], link["contract_status"]) != (op["path"], op["method"], op.get("x-contract-status")):
                contract_bad.append({"test": test["id"], "link": link})
    check("AT planned API method/path/status match OpenAPI", not contract_bad, invalid=contract_bad)

    counts["api_paths"] = len(api["paths"])
    counts["api_schemas"] = len(api["components"]["schemas"])
    counts["api_core"] = sum(o.get("x-contract-status") == "core" for o in operations)
    counts["api_planned"] = sum(o.get("x-contract-status") == "planned" for o in operations)
    check("API path and schema counts", counts["api_paths"] == 116 and counts["api_schemas"] == 122,
          f"paths={counts['api_paths']}; schemas={counts['api_schemas']}")
    check("API core/planned are contract detail levels", counts["api_core"] == 33 and counts["api_planned"] == 110,
          "core/planned do not indicate implemented or runtime-tested endpoints.")
    check("OpenAPI YAML and JSON represent the same document", api_yaml == api)
    check("OpenAPI top-level implementation status is not_implemented", api.get("x-implementation-status") == "not_implemented")
    missing_impl = [o["operationId"] for o in operations if o.get("x-implementation-status") != "not_implemented"]
    check("all API operations explicitly remain not_implemented", not missing_impl, f"{len(operations)} operations inspected.", missing_impl)

    local_refs = []
    external_refs = []

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "$ref" and isinstance(item, str):
                    (local_refs if item.startswith("#/") else external_refs).append(item)
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(api)
    unresolved = []
    for ref in sorted(set(local_refs)):
        target = api
        try:
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError):
            unresolved.append(ref)
    check("OpenAPI local JSON Pointer references resolve", not unresolved,
          f"{len(local_refs)} occurrences; {len(set(local_refs))} distinct local refs. This is not full OpenAPI semantic validation.", unresolved)
    check("OpenAPI references are local to the inspected contract", not external_refs, invalid=external_refs)

    stripped_sql = re.sub(r"/\*.*?\*/|--[^\n]*", "", sql, flags=re.S)
    table_names = re.findall(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.\"]+)", stripped_sql, re.I)
    sql_references = re.findall(r"\bREFERENCES\s+([\w.\"]+)", stripped_sql, re.I)
    counts["sql_tables"] = len(table_names)
    check("SQL defines 51 uniquely named tables", len(table_names) == 51 and len(set(table_names)) == 51,
          "Text declaration count only; SQL is not executed or migration-validated.")
    unknown_sql_refs = sorted(set(sql_references) - set(table_names))
    check("SQL referenced table declarations exist", not unknown_sql_refs, invalid=unknown_sql_refs)

    check("FRs remain unimplemented and runtime-unverified", all(r["status"] == "specified_not_implemented" and r["runtime_verified"] is False and r["binding_status"] == "not_bound" and r["fixture_readiness"] == "planned" for r in req))
    check("AT and IT execution statuses remain not_run with null results", all(t["status"] == "not_run" and t["actual_result"] is None and t["binding_status"] == "not_bound" for t in ats + its))
    binding_keys = ("runtime_fixture_ids", "concrete_request_body", "expected_status_code", "expected_persistence_assertions", "runner_path")
    check("AT concrete runtime bindings remain unprepared", all(all(t["execution_binding"].get(k) is None for k in binding_keys) for t in ats))
    check("metrics remain unmeasured with null observed values", all(m["measurement_status"] == "not_run" and m["observed_value"] is None and m["result"] is None and m["claim_status"] == "unvalidated_target" for m in metrics))
    check("evaluation experiments remain not_run with null results", all(e["status"] == "not_run" and e["run_id"] is None and e["executed_at"] is None and e["results"] is None for e in experiments))
    check("evaluation cases remain not_run with null evidence", all(c["status"] == "not_run" and c["result"] is None and c["evidence"] is None for c in cases))
    check("comparison experiments remain planned_not_run", comp_doc["platform_execution_status"] == "not_run" and all(e["status"] == "planned_not_run" for e in comparisons))
    check("fixture artifacts remain planned and unprepared", all(f["status"] == "planned" and f["artifact_path"] is None and f["sha256"] is None and f["ready_for_execution"] is False for f in fixtures))
    check("trace execution results remain null and not_run", all(t["execution_status"] == "not_run" and t["passed"] is None and t["implementation_status"] == "not_implemented" and t["binding_status"] == "not_bound" for t in traces))
    check("screens and flows remain proposed_not_implemented", all(s["implementation_status"] == "proposed_not_implemented" for s in screens) and all(f["status"] == "proposed_not_implemented" for f in flows))
    system_rows = [r for rows in system_doc.values() if isinstance(rows, list) for r in rows]
    check("technical/NFR/UX records remain specified_not_run", all(r["status"] == "specified_not_run" for r in system_rows))
    check("evaluation protocol asserts no platform or customer execution", eval_doc["execution_status"] == "not_run" and eval_doc["implemented_platform_assumed"] is False and eval_doc["paid_calls_performed"] == 0 and eval_doc["customer_experiments_performed"] == 0)
    check("BUS and KMR proposal records do not claim verified outcomes", all(r["verification_level"] == "unverified" and r["decision_state"] == "proposed" for r in bus + kmr),
          "Separate CLI and calculator execution evidence is not evaluated here.")

    system_ids = ids(system_rows)
    system_bad = []
    for row in system_rows:
        for ref in re.findall(r"\b(?:TCH|NFR|TCT|UXT)-\d{2,3}\b", json.dumps(row["columns"], ensure_ascii=False)):
            if ref not in system_ids:
                system_bad.append({"record": row["id"], "reference": ref})
    check("technical and UX table ID references exist", not system_bad, invalid=system_bad)

    source_inputs = (("business_sources.json", "sources"), ("tech_sources.json", "sources"),
                     ("refero_evidence.json", "references"), ("workflow_sources.json", "sources"),
                     ("project_ontology_sources.json", "sources"))
    expected_sourceids = set()
    for filename, key in source_inputs:
        expected_sourceids.update(s.get("id", s.get("source_id")) for s in load("research/" + filename)[key])
    dp = load("research/duration_pricing_sources.json")
    for key in ("sources", "supporting_policies", "excluded_candidates"):
        expected_sourceids.update(s["id"] for s in dp[key])
    cost_config = load("project_kit/cost_model.json")
    expected_sourceids.update(m["source_id"] for m in cost_config["video_models"].values())
    expected_sourceids.add(cost_config["keyframe_source_id"])
    check("merged source registry preserves the input source ID sets", expected_sourceids == sourceids,
          "Counts records, including repeated URLs and excluded candidates; does not validate the external claims.",
          sorted(expected_sourceids.symmetric_difference(sourceids)))
    check("source records carry explicit URLs", all(isinstance(s.get("url"), str) and s["url"].startswith(("https://", "http://")) for s in sources))

    chapters = {str(p.relative_to(root)): read(str(p.relative_to(root))) for p in sorted((root / "chapters").glob("*.md"))}
    source_bad = []
    for name, content in chapters.items():
        for ref in sorted(set(re.findall(r"\b(?:S-[BTUCP]\d{2}|DP-(?:P|X)?\d{2}|WF-S\d{2})\b", content))):
            if ref not in sourceids:
                source_bad.append({"file": name, "reference": ref})
    check("chapter source IDs resolve to the source registry", not source_bad, invalid=source_bad)
    check("chapters contain no unresolved chat tool-citation syntax", not any("\ue200" in c for c in chapters.values()))
    for key, chapter, prefix in (("technical_decisions", "chapters/04_technical.md", "TCH"),
                                 ("nonfunctional_requirements", "chapters/04_technical.md", "NFR"),
                                 ("technical_scenarios", "chapters/04_technical.md", "TCT"),
                                 ("ux_scenarios", "chapters/05_ux_flows.md", "UXT")):
        chapter_ids = set(re.findall(r"^\|\s*(" + prefix + r"-\d+)\s*\|", chapters[chapter], re.M))
        check(key + " IDs match their source chapter tables", chapter_ids == ids(system_doc[key]))

    passed = sum(c["passed"] for c in checks)
    supplemental = {key: counts.pop(key) for key in ("business_requirements", "knowledge_management_requirements", "comparison_experiments")}
    return {
        "schema_version": "2.0",
        "as_of": "2026-10-23",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "validator": "qa/validate_specification.py",
        "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "verified_scope": "document_and_contract_static_checks_only",
        "static_execution_status": "executed",
        "runtime_status": "not_run",
        "platform_runtime_status": "not_run",
        "counts": counts,
        "supplemental_counts": supplemental,
        "source_record_counts_by_registry": dict(sorted(Counter(s["registry_file"] for s in sources).items())),
        "unique_source_urls": len({s["url"] for s in sources}),
        "source_count_note": "92 is a source-record count, not 92 independent webpages, verified facts, or primary studies. Excluded candidates remain in the evidence registry.",
        "summary": {"static_checks": len(checks), "passed": passed, "failed": len(checks) - passed},
        "checks": checks,
        "pass": passed == len(checks),
        "pass_meaning": "All listed static properties held for the hashed local input files. This does not mean any platform function, acceptance scenario, integration scenario, quality metric, or business hypothesis passed execution.",
        "input_manifest": list(inputs.values()),
        "separate_evidence_not_included": [
            "16 document CLI tests: separate report; not included as platform or specification runtime passes.",
            "10 cost calculator tests: separate report; not included as platform or specification runtime passes.",
            "DOCX/PDF rendering and visual review: separate document artifact review reports.",
        ],
        "not_verified": [
            "Actual SQL migration, PostgreSQL constraints or RLS behavior",
            "Actual HTTP API implementation or end-to-end platform behavior",
            "Provider media generation, cancellation, billing or settlement",
            "Real fixture creation, execution binding, assertion runners or runtime test coverage",
            "Video quality, identity consistency, music fit or team preference outcomes",
            "Load, restore, deletion or cross-IP isolation under runtime conditions",
            "Paid demand, retention, actual customer labor or production unit costs",
            "Freshness or truth of external webpages; source reference linkage only",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    report = validate(root)
    output = root / "output/Specification_Validation_Report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "pass": report["pass"], "summary": report["summary"],
                      "counts": report["counts"], "supplemental_counts": report["supplemental_counts"],
                      "failed_checks": [c for c in report["checks"] if not c["passed"]],
                      "platform_runtime_status": report["platform_runtime_status"]}, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
