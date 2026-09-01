"""AET-B-1 (#287, WP-2026-0130): the seat roster, red-first.

The roster binds operating seats to contract roles -- identity and NOTHING else. The
guard enumerates BOTH doctrine-declared shapes that must never land in it (permissions
and time windows), each constructed and observed refused -- the F4 lesson made
mechanical: the falsification line asks what docs/03 declares a component of
authority, not what the author imagined. Delegations gain the F1 seat-field ratchet
(threshold = this WP's own id; sentinels exempt; the grandfathered delegation counted)
with declaration-consistency labeled as what it is: consistency of what a session says
about itself, not identity verification -- that refusal lands with #261.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

RATCHETED = "WP-2026-9996"   # >= threshold, non-sentinel: the seat ratchet must bite
EXEMPT = "WP-2026-0998"      # sentinel: existing-fixture shape, must stay green
DEM = "BADF-DEM-0996"


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        self.base = seed_clone(self.root, carry_working_state=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        on_ledger = set(self.git("ls-tree", "-r", "--name-only", "origin/main", "--", "work/").splitlines())
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            if rec.relative_to(self.root).as_posix() not in on_ledger:
                shutil.rmtree(rec.parent)
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            subprocess.run([sys.executable, "scripts/badf_gate.py", "reconcile", rec.parent.name], cwd=self.root, env=self.env, capture_output=True)
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- roster deliverable -->\n")
        self.git("add", "README.md"); self.commit("deliverable")
        src = json.loads((self.root / "badf/demands/BADF-DEM-0001.json").read_text(encoding="utf-8"))
        src["demand_id"] = DEM; src["status"] = "AUTHORIZED"
        src["authorized_by"] = {"principal": "operator", "principal_type": "human"}
        (self.root / "badf/demands" / f"{DEM}.json").write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
        self.lock()

    def write_wp(self, wp_id, **extra):
        d = self.root / "work" / wp_id; d.mkdir(parents=True, exist_ok=True)
        rec = {"$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0", "id": wp_id,
               "title": "scratch roster work package", "owner": "human_sponsor", "repository": "bstBizEra/badf",
               "demand": DEM, "objective": "x", "business_value": "x", "in_scope": ["x"], "out_of_scope": ["y"],
               "target_gate": "G07", "change_class": "C2", "data_classification": "internal",
               "acceptance_criteria": ["x"], "permissions": ["write: bstBizEra/badf via PR"], "tests": ["tests/test_probe.py (3)"],
               "evidence": ["source-change"], "rollback": {"reversible": True, "method": "revert"},
               "status": "IN_PROGRESS",
               "expected_surfaces": {"files": ["README.md"]},
               "external_target": {"repository": "bstBizEra/badf", "branch": "main", "base_revision": self.base}}
        rec.update(extra)
        (d / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")

    def write_delegation(self, wp_id, seat=None):
        b = self.root / "work" / wp_id / "build"; b.mkdir(parents=True, exist_ok=True)
        d = {"task": "probe-task", "allowed_paths": ["README.md"], "allowed_tools": [],
             "prohibited": list(gate.DELEGATION_PROHIBITED)}
        if seat is not None:
            d["seat"] = seat
        (b / "session.json").write_text(json.dumps({"work_package_id": wp_id, "delegations": [d]}, indent=2) + "\n")

    def roster(self):
        return json.loads((self.root / "badf/seats.json").read_text(encoding="utf-8"))

    def write_roster(self, data):
        (self.root / "badf/seats.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def git(self, *a): return subprocess.run(["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", *a], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, msg): self.git("commit", "-q", "-m", msg)
    def lock(self): subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
    def gate_cmd(self, *args): return subprocess.run([sys.executable, "scripts/badf_gate.py", *args], cwd=self.root, env=self.env, capture_output=True, text=True)


class RosterArtifactTests(_Scratch):
    def test_roster_exists_schema_validates_and_names_the_vacancy(self):
        r = self.roster()
        ids = [s["id"] for s in r["seats"]]
        for seat in ("SARCHI", "BARCHI-1", "BARCHI-2", "BARCHI-3", "BADF-QA", "BADF-REV"):
            self.assertIn(seat, ids, seat)
        vacant = [s for s in r["seats"] if s.get("status") == "VACANT"]
        self.assertTrue(any(s["role"] == "librarian" for s in vacant),
                        "the librarian vacancy is stated out loud, never implied")
        out = self.gate_cmd("repo")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("BADF SEAT ROSTER", out.stdout)
        self.assertIn("VACANT", out.stdout)

    def test_empty_roster_is_refused_not_reported_clean(self):
        """REV's enumeration-vacuity finding (#290 review): a loop finding nothing passes
        like one finding everything -- an empty roster would print 0 held / 0 VACANT and
        every guard would sleep. The CODE check is the enforcement; the schema's
        minItems is declarative only until #265 Rung A lands (the sole-enforcer pattern)."""
        r = self.roster(); r["seats"] = []
        self.write_roster(r); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("no seats", out.stdout + out.stderr)

    def test_blank_or_padded_seat_id_is_refused(self):
        """QA Finding 1 (#290, blocking; measured on four heads): [{"id": ""}] carries the
        same information as [] and passed the very check added to refuse [] -- the
        degenerate-content shape (#293) on the identity surface. Empty, whitespace-only,
        and padded ids all name nothing a delegation could safely bind to."""
        for probe in ("", "   ", " GHOST"):
            r = self.roster(); r["seats"][0]["id"] = probe
            self.write_roster(r); self.lock()
            out = self.gate_cmd("repo")
            self.assertNotEqual(out.returncode, 0, f"id {probe!r} admitted: {out.stdout}")
            self.assertIn("names nothing", out.stdout + out.stderr, probe)

    def test_duplicate_seat_id_is_refused(self):
        """QA Finding 2 (#290): _rostered_seats() is a set, so a duplicate id collapses
        silently -- on a roster whose subject is identity."""
        r = self.roster(); r["seats"].append(dict(r["seats"][0]))
        self.write_roster(r); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("more than once", out.stdout + out.stderr)

    def test_empty_charter_refs_is_refused(self):
        """QA Finding 2 (#290): charter_refs = [] was admitted -- provenance-free
        identity, the same degenerate-content family as the blank id."""
        r = self.roster(); r["seats"][0]["charter_refs"] = []
        self.write_roster(r); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("charter_refs", out.stdout + out.stderr)

    def test_permission_shaped_key_in_a_seat_is_refused(self):
        r = self.roster(); r["seats"][0]["allowed_tools"] = ["git-push"]
        self.write_roster(r); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("AUTHORITY_CONFLICT", out.stdout + out.stderr)

    def test_time_shaped_key_in_a_seat_is_refused(self):
        r = self.roster(); r["seats"][1]["expires"] = "2027-01-01T00:00:00Z"
        self.write_roster(r); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("AUTHORITY_CONFLICT", out.stdout + out.stderr)
        self.assertIn("#261", out.stdout + out.stderr, "the refusal points at where the decision lives")


class SeatRatchetTests(_Scratch):
    def test_delegation_at_threshold_without_seat_refused_at_assembly(self):
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat=None); self.lock()
        r = self.gate_cmd("self-dossier", RATCHETED)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        out = r.stdout + r.stderr
        self.assertIn("seat", out); self.assertIn(RATCHETED, out)

    def test_declared_seat_absent_from_roster_is_refused(self):
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat="GHOST-SEAT"); self.lock()
        r = self.gate_cmd("self-dossier", RATCHETED)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("GHOST-SEAT", r.stdout + r.stderr)

    def test_rostered_seat_accepted_and_labeled_declaration_consistency(self):
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat="BARCHI-2"); self.lock()
        r = self.gate_cmd("self-dossier", RATCHETED)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_malformed_delegation_reds_the_repo_sweep(self):
        """REV's fork (#290 review): assembly RAISES on a non-dict delegation while the
        repo sweep silently skipped it before the counters -- and assembly does not
        stand on every landing path (session.json can change post-assembly; grandfathered
        WPs never re-assemble). The two sites must agree: malformed refuses at BOTH."""
        self.write_wp(EXEMPT)
        b = self.root / "work" / EXEMPT / "build"; b.mkdir(parents=True, exist_ok=True)
        (b / "session.json").write_text(json.dumps({"work_package_id": EXEMPT, "delegations": ["just-a-string"]}, indent=2) + "\n")
        self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn(EXEMPT, out.stdout + out.stderr)
        self.assertIn("not a mapping", out.stdout + out.stderr)

    def test_ratcheted_no_seat_delegation_reds_the_repo_sweep(self):
        """REV's asymmetric-watch finding (#290 review): both duplicated rules were
        tested through assembly only, leaving the sweep copies correct-and-unwatched
        (the #250 class) on the rung whose copies already forked once. The behavior
        pre-exists, so the proof is mutation discrimination, not red-first: a
        dossier-less WP during `repo` reaches ONLY the sweep copy."""
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat=None); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        text = out.stdout + out.stderr
        self.assertIn(RATCHETED, text); self.assertIn("names no seat", text)

    def test_ghost_seat_delegation_reds_the_repo_sweep(self):
        """Sweep-side twin of the assembly declaration-consistency test (REV's
        asymmetric-watch finding). Uses the EXEMPT sentinel: grandfathering excuses
        only a MISSING seat, never a declared seat absent from the roster."""
        self.write_wp(EXEMPT); self.write_delegation(EXEMPT, seat="GHOST-SEAT"); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        text = out.stdout + out.stderr
        self.assertIn("GHOST-SEAT", text); self.assertIn("declaration-consistency", text)

    def test_blank_delegation_seat_is_absent_at_assembly(self):
        """QA Finding 1's second leg: seat: "" counted as NAMING a seat (only None read
        as absent), so it passed the mandatory-seat ratchet and resolved against the
        empty-id seat. A blank seat names nothing -> normalized to absent, once, in a
        helper both sites call, so the twins cannot fork on the semantic."""
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat="  "); self.lock()
        r = self.gate_cmd("self-dossier", RATCHETED)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        out = r.stdout + r.stderr
        self.assertIn(RATCHETED, out); self.assertIn("names no seat", out)

    def test_blank_delegation_seat_is_absent_at_the_repo_sweep(self):
        """Sweep twin of the blank-seat normalization (dossier-less WP reaches only the
        sweep copy -- same site discrimination as the asymmetric-watch fold)."""
        self.write_wp(RATCHETED); self.write_delegation(RATCHETED, seat=""); self.lock()
        out = self.gate_cmd("repo")
        self.assertNotEqual(out.returncode, 0, out.stdout)
        text = out.stdout + out.stderr
        self.assertIn(RATCHETED, text); self.assertIn("names no seat", text)

    def test_blank_seat_grandfathered_counted_as_absent(self):
        """Positive control for the fold's semantic: blank means ABSENT, not forbidden --
        below the ratchet threshold a blank seat is excused exactly as a missing one is,
        never refused as an unrostered declaration."""
        self.write_wp(EXEMPT); self.write_delegation(EXEMPT, seat=""); self.lock()
        r = self.gate_cmd("self-dossier", EXEMPT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = self.gate_cmd("repo")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_grandfathered_delegation_counted_not_refused(self):
        self.write_wp(EXEMPT); self.write_delegation(EXEMPT, seat=None); self.lock()
        r = self.gate_cmd("self-dossier", EXEMPT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = self.gate_cmd("repo")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        line = [l for l in out.stdout.splitlines() if "BADF SEAT ROSTER" in l]
        self.assertTrue(line and "delegation" in line[0].lower(), out.stdout)


if __name__ == "__main__":
    unittest.main()
