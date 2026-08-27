"""Governed state transition (BADF-WP-0029, Issue #41, BADF-DEC-0007).

An instance moves beyond G00 / INITIALIZED only as a DERIVED consequence of a
bound, still-valid, APPROVED dossier for its next gate. `advance <instance>
<dossier>` binds the framework's dossier byte-identical under
<instance>/badf/evidence/dossiers/<gate>.json and re-derives state.json;
`instance` recomputes the chain -- every bound copy must equal its framework
original, the original must still render APPROVED, and gates must be
contiguous from G00 -- and refuses any lifecycle the chain cannot support.
The tool binds what humans approved; it never approves. Scratch instances only.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests.test_badf_instance_validation import ValidatedInstance  # noqa: E402
from tests.test_badf_instance import git, snapshot  # noqa: E402

EXAMPLE = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
HUMAN = {"id": "product-owner-signature", "type": "human"}


def bound(approval, dossier):
    """An approval is bound to the dossier it approves: revision, epoch, time."""
    a = dict(approval)
    a["revision"] = dossier["source_revision"]; a["policy_epoch"] = dossier["policy_epoch"]; a["approved_at"] = dossier["created_at"]
    return a


class AdvanceScratch(ValidatedInstance):

    def wp(self):
        return self.state()["active_work_package"]

    def wp_dir(self):
        return self.root / "work" / self.wp()

    def framework_lock(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)

    def dossier_cli(self, rel):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", rel], cwd=self.root, env=self.env, capture_output=True, text=True)

    def advance(self, rel, path=None):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "advance", str(path or self.t), rel],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def approve_g00(self):
        """The HUMAN_REQUIRED init dossier, as a human would complete it: PASS at
        the G00 floor (C0) with the example's reviewer, evidence signed PASS."""
        d = self.wp_dir(); doc = json.loads((d / "gate-dossier.G00.json").read_text())
        # the owner completes the intake: judgment fields supplied, classification
        # lowered from the deny-by-default `restricted` with a stated rationale
        wp = json.loads((d / "work-package.json").read_text())
        wp.update(objective="a scratch product for the transition tests", business_value="none; fixture",
                  in_scope=["the fixture"], out_of_scope=["everything else"], acceptance_criteria=["advance binds an APPROVED dossier"],
                  declared_missing=[], data_classification="internal",
                  data_classification_rationale="fixture data only; lowered by the owner at G00")
        (d / "work-package.json").write_text(json.dumps(wp, indent=2) + "\n")
        for ev in (d / "evidence/G00").glob("*.json"):
            if ev.name.endswith(".receipt.json"):
                continue
            e = json.loads(ev.read_text()); e["outcome"] = "PASS"; e["producer"] = HUMAN
            ev.write_text(json.dumps(e, indent=2) + "\n")
        doc["disposition"] = "PASS"; doc["change_class"] = "C0"; doc["approvals"] = [bound(EXAMPLE["approvals"][0], doc)]
        (d / "gate-dossier.G00.json").write_text(json.dumps(doc, indent=2) + "\n")
        self.framework_lock()
        r = self.dossier_cli(f"work/{self.wp()}/gate-dossier.G00.json")
        assert r.returncode == 0 and "APPROVED" in r.stdout, r.stdout + r.stderr
        return f"work/{self.wp()}/gate-dossier.G00.json"

    def make_g01(self):
        """A G01 dossier for the same WP at the G01 floor (C1): three PASS
        evidence records by a human, two human approvers."""
        d = self.wp_dir(); ev_dir = d / "evidence/G01"; ev_dir.mkdir(parents=True, exist_ok=True)
        g00 = json.loads((d / "gate-dossier.G00.json").read_text())
        index = []
        for t in ("prd", "acceptance-criteria", "product-approval"):
            art = ev_dir / f"{t}.txt"; art.write_text(f"{t} evidence for the scratch product\n")
            e = {"schema_version": "1.0.0", "id": f"EVD-{self.wp()}-G01-{t}", "work_package_id": self.wp(), "gate": "G01",
                 "claim": f"{t} present", "evidence_type": t, "producer": HUMAN,
                 "source_revision": g00["source_revision"], "target": g00["target"],
                 "toolchain": {"name": "human-review", "version": "1"}, "operation": "review",
                 "started_at": g00["created_at"], "completed_at": g00["created_at"], "outcome": "PASS",
                 "artifact": f"work/{self.wp()}/evidence/G01/{t}.txt", "digest": gate.sha256(art)}
            (ev_dir / f"{t}.json").write_text(json.dumps(e, indent=2) + "\n")
            index.append({"type": t, "path": f"work/{self.wp()}/evidence/G01/{t}.json"})
        approvals = []
        for role in ("engineering_owner", "independent_reviewer"):
            a = bound(EXAMPLE["approvals"][0], g00); a["role"] = role; a["by"] = f"{role}-signature"; approvals.append(a)
        doc = dict(g00, id=f"DOS-{self.wp()}-G01-v1", gate="G01", change_class="C1", disposition="PASS",
                   evidence=index, approvals=approvals, conditions=[], non_coverage=[], exceptions=[], risks=[], council=None)
        doc.pop("held_because", None); doc.pop("council_disposition", None)
        (d / "gate-dossier.G01.json").write_text(json.dumps(doc, indent=2) + "\n")
        self.framework_lock()
        r = self.dossier_cli(f"work/{self.wp()}/gate-dossier.G01.json")
        assert r.returncode == 0 and "APPROVED" in r.stdout, r.stdout + r.stderr
        return f"work/{self.wp()}/gate-dossier.G01.json"


class AdvanceTests(AdvanceScratch):

    def test_held_init_dossier_cannot_advance(self):
        before = snapshot(self.t)
        r = self.advance(f"work/{self.wp()}/gate-dossier.G00.json")
        self.assertNotEqual(r.returncode, 0, "a HELD dossier advanced the instance")
        self.assertIn("does not render APPROVED", r.stderr)
        self.assertEqual(snapshot(self.t), before)

    def test_approved_g00_advances_and_instance_rederives_it(self):
        rel = self.approve_g00()
        r = self.advance(rel); self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        bound = self.t / "badf/evidence/dossiers/G00.json"
        self.assertEqual(bound.read_bytes(), (self.root / rel).read_bytes(), "bound copy is not byte-identical")
        self.assertEqual(self.state()["lifecycle"]["current_gate"], "G00")
        self.assertEqual(self.state()["lifecycle"]["state"], "APPROVED")
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("G00 / APPROVED", r.stdout)

    def test_g01_is_refused_before_g00_is_bound_and_accepted_after(self):
        self.approve_g00(); g01 = self.make_g01()
        r = self.advance(g01)
        self.assertNotEqual(r.returncode, 0, "G01 bound before G00"); self.assertIn("next gate is G00", r.stderr)
        self.assertEqual(self.advance(f"work/{self.wp()}/gate-dossier.G00.json").returncode, 0)
        r = self.advance(g01); self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(self.state()["lifecycle"], {"current_gate": "G01", "state": "APPROVED", "target": "PRODUCTION"})
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("G01 / APPROVED", r.stdout)

    def test_same_gate_cannot_be_bound_twice(self):
        rel = self.approve_g00(); self.assertEqual(self.advance(rel).returncode, 0)
        r = self.advance(rel); self.assertNotEqual(r.returncode, 0); self.assertIn("already bound", r.stderr)

    def test_dossier_for_another_work_package_on_the_same_repository_is_refused(self):
        """A later work package on the SAME project (nothing forbids two) has an
        approved dossier. Consistent on its own -- record, dossier and evidence
        all name WP-2026-0999 -- so validate_dossier is satisfied; only the
        binding to THIS instance's work package refuses it."""
        rel = self.approve_g00()
        other = "WP-2026-0999"; od = self.root / "work" / other; od.mkdir()
        rec = json.loads((self.wp_dir() / "work-package.json").read_text()); rec["id"] = other
        (od / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")
        doc = json.loads((self.root / rel).read_text()); doc["work_package_id"] = other; doc["id"] = f"DOS-{other}-G00-v1"
        (self.wp_dir() / "gate-dossier.G00.json").write_text(json.dumps(doc, indent=2) + "\n")   # filed under OUR wp dir, canonical path
        for ev in (self.wp_dir() / "evidence/G00").glob("*.json"):
            if ev.name.endswith(".receipt.json"):
                continue
            e = json.loads(ev.read_text()); e["work_package_id"] = other; ev.write_text(json.dumps(e, indent=2) + "\n")
        self.framework_lock()
        r = self.dossier_cli(rel); self.assertEqual(r.returncode, 0, "the other WP's dossier must validate on its own: " + r.stderr)
        r = self.advance(rel); self.assertNotEqual(r.returncode, 0, "another work package's approval was bound to this instance")
        self.assertIn("names work package", r.stderr)

    def test_non_canonical_dossier_path_is_refused(self):
        rel = self.approve_g00()
        other = self.root / "work" / self.wp() / "copy.json"; other.write_bytes((self.root / rel).read_bytes()); self.framework_lock()
        r = self.advance(f"work/{self.wp()}/copy.json"); self.assertNotEqual(r.returncode, 0); self.assertIn("gate-dossier", r.stderr)

    def test_advance_writes_only_the_bound_dossier_state_and_lock(self):
        rel = self.approve_g00(); before = snapshot(self.t)
        self.assertEqual(self.advance(rel).returncode, 0)
        after = snapshot(self.t)
        changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
        self.assertEqual(changed, {"badf/evidence/dossiers/G00.json", "badf/state.json", "badf/lockfile.json"})

    def test_advance_refuses_a_drifted_instance_and_writes_nothing(self):
        rel = self.approve_g00()
        self.edit_json("badf/state.json", lambda d: d["readiness"].update(product="READY")); before = snapshot(self.t)
        r = self.advance(rel); self.assertNotEqual(r.returncode, 0); self.assertIn("drift", r.stderr)
        self.assertEqual(snapshot(self.t), before)


class ChainCorroborationTests(AdvanceScratch):
    def setUp(self):
        super().setUp()
        self.g00 = self.approve_g00(); assert self.advance(self.g00).returncode == 0

    def test_bound_copy_that_differs_from_the_framework_original_is_refused(self):
        bound = self.t / "badf/evidence/dossiers/G00.json"
        doc = json.loads(bound.read_text()); doc["disposition"] = "PASS"; doc["approvals"].append(doc["approvals"][0])
        bound.write_text(json.dumps(doc, indent=2) + "\n"); self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("differs from the framework", r.stderr)

    def test_framework_original_that_no_longer_renders_approved_is_refused(self):
        doc = json.loads((self.root / self.g00).read_text()); doc["disposition"] = "FAIL"
        (self.root / self.g00).write_text(json.dumps(doc, indent=2) + "\n"); self.framework_lock()
        r = self.instance(); self.assertNotEqual(r.returncode, 0, "a withdrawn approval still carried the instance"); self.assertIn("differs from the framework", r.stderr)

    def test_framework_policy_strengthened_after_the_bind_unapproves_it(self):
        """Same bytes, different world: the framework's C0 floor gains a role,
        so the bound dossier's single reviewer no longer satisfies it. The
        instance must fall, and say why."""
        m = json.loads((self.root / "badf/authority-matrix.json").read_text())
        m["change_classes"]["C0"]["required_roles"].append("security_authority")
        (self.root / "badf/authority-matrix.json").write_text(json.dumps(m, indent=2) + "\n"); self.framework_lock()
        r = self.instance(); self.assertNotEqual(r.returncode, 0, "a dossier the framework no longer accepts still carried the instance")
        self.assertIn("no longer validates", r.stderr)

    def test_hand_edited_lifecycle_is_refused_after_resign(self):
        self.edit_json("badf/state.json", lambda d: d["lifecycle"].update(current_gate="G01"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("disagrees", r.stderr)

    def test_a_gap_in_the_chain_is_refused(self):
        """A bound G02 with no bound G01 -- contiguity from G00 is required."""
        bound = self.t / "badf/evidence/dossiers/G02.json"; bound.write_bytes((self.t / "badf/evidence/dossiers/G00.json").read_bytes())
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0)
        self.assertTrue("contiguous" in r.stderr or "G01" in r.stderr, r.stderr)


if __name__ == "__main__":
    unittest.main()
