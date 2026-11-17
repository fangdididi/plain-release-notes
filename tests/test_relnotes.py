import copy, io, json, os, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import relnotes as rn


def changes():
    with open(os.path.join(ROOT, "examples", "changes.json")) as f:
        return json.load(f)


def draft(name="draft.md"):
    with open(os.path.join(ROOT, "examples", name)) as f:
        return f.read()


class Collect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = os.path.join(tempfile.mkdtemp(), "jotter")
        subprocess.run(["bash", os.path.join(ROOT, "examples", "make_demo_repo.sh"), cls.repo], check=True, capture_output=True)
        cls.data = rn.collect("v1.4.0", "v1.5.0", cls.repo)

    def test_exact_range_and_order(self):
        ids = [c["id"] for c in self.data["changes"]]
        self.assertEqual(ids, ["#41", "#42", "#43", "#44", "#45", "#46", "#47"])
        self.assertEqual(len(self.data["from"]), 40)

    def test_breaking_and_migration_hints(self):
        c = {c["id"]: c for c in self.data["changes"]}["#44"]
        self.assertIn("breaking", c["hints"]); self.assertIn("migration", c["hints"]); self.assertEqual(c["guess"], "act")

    def test_quiet_guess_for_chores(self):
        g = {c["id"]: c["guess"] for c in self.data["changes"]}
        self.assertEqual((g["#42"], g["#45"], g["#46"]), ("quiet", "quiet", "quiet"))
        self.assertEqual(g["#47"], "")


class Lint(unittest.TestCase):
    def test_good_draft_passes_clean(self):
        e, w = rn.lint(draft(), changes())
        self.assertEqual((e, w), ([], []))

    def test_bad_draft_errors(self):
        e, w = rn.lint(draft("draft-bad.md"), changes())
        text = "\n".join(e)
        self.assertIn("no trace tag", text); self.assertIn("sorted quiet", text)
        self.assertIn("number 10", text); self.assertIn("missing: '#44'", text)

    def test_unknown_trace(self):
        e, _ = rn.lint("- Something <!-- src: #999 -->\n", changes())
        self.assertTrue(any("not in this release range" in x for x in e))

    def test_number_must_match_whole(self):
        d = changes()
        e, _ = rn.lint("## When you search\n- Search takes 0.4 s now. <!-- src: #41 -->\n", d)
        self.assertFalse(any("number" in x for x in e))
        e, _ = rn.lint("## When you search\n- Search is 4 times quicker. <!-- src: #41 -->\n", d)
        self.assertTrue(any("number 4 " in x for x in e))

    def test_act_outside_upgrade_section_warns(self):
        md = "## Organise\n- Upgrade your sync server to 2.0 first. <!-- src: #44 -->\n"
        _, w = rn.lint(md, changes())
        self.assertTrue(any("Before you upgrade" in x for x in w))

    def test_integrator_audience_allows_identifiers(self):
        md = "## Before you upgrade\n- Set `sync_url` and upgrade the server to 2.0. <!-- src: #44 -->\n"
        _, w = rn.lint(md, changes(), audience="integrators")
        self.assertFalse(any("code-style" in x for x in w))

    def test_quiet_with_breaking_hint_warns(self):
        d = changes(); c = next(x for x in d["changes"] if x["id"] == "#45"); c["hints"] = ["breaking"]
        _, w = rn.lint(draft(), d)
        self.assertTrue(any("confirm nobody must act" in x for x in w))

    def test_skeleton_refuses_unsorted(self):
        d = changes(); d["changes"][0]["sort"] = ""
        with self.assertRaises(SystemExit):
            rn.skeleton(d, "x")

    def test_render_strips_tags(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rn.main(["render", os.path.join(ROOT, "examples", "draft.md")])
        self.assertNotIn("src:", buf.getvalue()); self.assertIn("Before you upgrade", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
