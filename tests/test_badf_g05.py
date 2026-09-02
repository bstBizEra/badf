"""G05 evidence contract (BADF-WP-0060; the gate march reaches security).

G05's four required evidence types have semantics the gate enforces by opening
the artifact, inside validate_evidence, each mapping to a G05 exit criterion:
threats and abuse cases are each controlled (a threat with no mitigation is
refused); privacy obligations are addressed (a data category with no lawful basis
or handling is refused); dependency and secret controls are planned (no secret
controls, or an uncontrolled dependency, is refused); and residual risk is owned
by a human security_authority whose approval is digest-bound to the threat model.
Faithful-runner shape.
"""

# Rung A (#265, WP-2026-0138): SHADOWED, nothing stronger to re-point at. The control is
# bare list-truthiness, so `minItems: 1` is EXACTLY equivalent and now refuses first.
# The control is RETAINED (criterion 5) and is now unreachable on this path; recorded
# rather than silently re-worded, per SARCHI C2. Disposition deferred, not decided.
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

DOSSIER = "examples/gate-dossier.G05.json"
EV = "examples/evidence/G05"


class G05Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        seed_clone(self.root, carry_working_state=True)
        for rel in ("schemas", "tests"):
            shutil.rmtree(self.root / rel, ignore_errors=True); shutil.copytree(gate.ROOT / rel, self.root / rel)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", DOSSIER], cwd=self.root, env=self.env, capture_output=True, text=True)

    def artifact(self, t):
        return json.loads((self.root / EV / f"{t}.artifact.json").read_text())

    def rewrite(self, t, obj):
        p = self.root / EV / f"{t}.artifact.json"; p.write_text(json.dumps(obj, indent=2) + "\n")
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text())
        rec["digest"] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest(); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def record(self, t, fn):
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text()); fn(rec); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G05 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G05ExampleTests(G05Scratch):

    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "privacy-assessment"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class ThreatModelRuleTests(G05Scratch):

    def test_an_uncontrolled_threat_is_refused(self):
        t = self.artifact("threat-model"); t["threats"][0]["mitigation"] = ""; self.rewrite("threat-model", t)
        self.refused("must be controlled")

    def test_no_threats_is_refused(self):
        t = self.artifact("threat-model"); t["threats"] = []; self.rewrite("threat-model", t)
        self.refused("threats has 0 items")


class PrivacyRuleTests(G05Scratch):

    def test_a_category_without_lawful_basis_is_refused(self):
        p = self.artifact("privacy-assessment"); p["data_categories"][0]["lawful_basis"] = ""; self.rewrite("privacy-assessment", p)
        self.refused("privacy obligations must be addressed")


class SupplyChainRuleTests(G05Scratch):

    def test_no_secret_controls_is_refused(self):
        s = self.artifact("supply-chain-plan"); s["secret_controls"] = []; self.rewrite("supply-chain-plan", s)
        self.refused("dependency and secret controls must be planned")

    def test_an_uncontrolled_dependency_is_refused(self):
        s = self.artifact("supply-chain-plan"); s["dependencies"] = [{"id": "DEP-001", "name": "somelib", "control": ""}]; self.rewrite("supply-chain-plan", s)
        self.refused("dependency DEP-001 has no control")


class SecurityApprovalRuleTests(G05Scratch):

    def test_a_non_human_approval_is_refused(self):
        self.record("security-approval", lambda rec: rec.__setitem__("producer", {"id": "bot", "type": "automation"}))
        self.refused("must be produced by a human security_authority")

    def test_no_residual_risk_owner_is_refused(self):
        a = self.artifact("security-approval"); a["residual_risk_owner"] = ""; self.rewrite("security-approval", a)
        self.refused("residual risk must be owned")

    def test_a_wrong_threat_model_digest_is_refused(self):
        # tamper the threat model after approval: the approval's bound digest no longer matches.
        t = self.artifact("threat-model"); t["threats"][0]["statement"] += " (edited after approval)"; self.rewrite("threat-model", t)
        self.refused("threat_model_digest does not match")


if __name__ == "__main__":
    unittest.main()
