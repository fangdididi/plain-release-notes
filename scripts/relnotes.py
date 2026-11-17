#!/usr/bin/env python3
"""relnotes.py - release notes people actually read, with every line traceable to a change.

Stdlib only (needs git on PATH for `collect`). Subcommands:
  collect   list every change in an exact git range as changes.json, with hint flags
  skeleton  turn a sorted changes.json into a draft with trace tags, grouped by sort
  lint      check a draft against changes.json (traceability, coverage, plain words, numbers)
  render    strip trace tags and print the public version plus a coverage line

A change is sorted by a person (or the agent, then confirmed) into:
  act    the reader must do something (breaking change, migration, config, permission)
  see    the reader will notice it (new ability, faster, fixed annoyance)
  quiet  nobody outside the team will notice (refactor, tests, CI, internal tooling)
"""
import argparse, fnmatch, json, re, subprocess, sys

TRACE = re.compile(r"<!--\s*src:\s*([^>]*?)\s*-->")
PR_RE = [re.compile(r"Merge pull request #(\d+)"), re.compile(r"\(#(\d+)\)\s*$"), re.compile(r"!(\d+)\b")]
HINTS = {
    "breaking": re.compile(r"BREAKING|^\w+(\([^)]*\))?!:", re.M),
    "security": re.compile(r"\b(CVE-\d{4}-\d+|security|xss|csrf|injection|vulnerab)", re.I),
    "deprecation": re.compile(r"\bdeprecat", re.I),
    "quiet_prefix": re.compile(r"^(chore|test|tests|ci|build|refactor|style|docs\(internal\))(\(|:)", re.I),
}
FILE_HINTS = {
    "migration": ["*migrations/*", "*migrate*", "*.sql", "*schema*"],
    "config": ["*.env.example", "*config*.y*ml", "*settings*", "*.toml"],
    "dependency": ["package.json", "*requirements*.txt", "pyproject.toml", "go.mod", "Cargo.toml", "*.lock", "*lock.json"],
}
JARGON_USERS = ["refactor", "bump", "deps", "dependency", "pull request", "commit", "merge", "endpoint",
                "regression", "null", "undefined", "exception", "stack trace", "payload", "schema",
                "migration script", "hotfix", "linter", "ci ", "tech debt", "under the hood"]
WEAK_OPENERS = re.compile(r"^(fixed|fix|fixes) (a |an |the )?(bug|issue|problem)\b", re.I)
IDENT = re.compile(r"(?<!`)\b([a-z]+_[a-z_]+|[a-z]+[A-Z][A-Za-z]+|[A-Z][a-z]+[A-Z][A-Za-z]+)\b(?!`)")
PATHISH = re.compile(r"(?<!`)\b[\w.-]+/[\w./-]+\.\w+\b(?!`)")
NUM = re.compile(r"\d+(?:\.\d+)?")


def git(args, cwd=None):
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        raise SystemExit("git " + " ".join(args) + ": " + r.stderr.strip())
    return r.stdout


def collect(frm, to, cwd=None, first_parent=True):
    a, b = git(["rev-parse", frm], cwd).strip(), git(["rev-parse", to], cwd).strip()
    fmt = "%H%x1f%s%x1f%b%x1e"
    args = ["log", "--format=" + fmt, f"{a}..{b}"] + (["--first-parent"] if first_parent else [])
    out = []
    for rec in git(args, cwd).split("\x1e"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        sha, subj, body = (rec.split("\x1f") + ["", ""])[:3]
        files = [f for f in git(["show", "--format=", "--name-only", "-m", "--first-parent", sha], cwd).splitlines() if f]
        pr = None
        for rx in PR_RE:
            m = rx.search(subj)
            if m:
                pr = "#" + m.group(1); break
        text = subj + "\n" + body
        hints = [k for k, rx in HINTS.items() if k != "quiet_prefix" and rx.search(text)]
        for k, pats in FILE_HINTS.items():
            if any(fnmatch.fnmatch(f, p) or fnmatch.fnmatch(f.split("/")[-1], p) for f in files for p in pats):
                hints.append(k)
        guess = "act" if {"breaking", "migration"} & set(hints) else ("quiet" if HINTS["quiet_prefix"].search(subj) else "")
        out.append({"id": pr or sha[:7], "sha": sha[:7], "subject": subj.strip(), "body": body.strip()[:2000],
                    "files": files[:50], "hints": hints, "sort": "", "guess": guess, "heading": "", "note": ""})
    return {"from": a, "to": b, "changes": out[::-1]}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def skeleton(data, title):
    ch = data["changes"]
    unsorted = [c["id"] for c in ch if c.get("sort") not in ("act", "see", "quiet")]
    if unsorted:
        raise SystemExit("unsorted changes (set sort to act/see/quiet): " + ", ".join(unsorted))
    lines = [f"# {title}", "", "One line on what this release means for you.", ""]
    acts = [c for c in ch if c["sort"] == "act"]
    if acts:
        lines += ["## Before you upgrade", ""]
        for c in acts:
            lines.append(f"- **What to do:** {c.get('note') or c['subject']} <!-- src: {c['id']} -->")
        lines.append("")
    heads = []
    for c in ch:
        if c["sort"] == "see":
            h = c.get("heading") or "Everywhere"
            if h not in heads:
                heads.append(h)
    for h in heads:
        lines += [f"## {h}", ""]
        for c in ch:
            if c["sort"] == "see" and (c.get("heading") or "Everywhere") == h:
                lines.append(f"- {c.get('note') or c['subject']} <!-- src: {c['id']} -->")
        lines.append("")
    return "\n".join(lines)


def bullets(md):
    """Yield (line_no, section, text_without_tag, [ids]) for each bullet."""
    section = ""
    for i, line in enumerate(md.splitlines(), 1):
        if line.startswith("## "):
            section = line[3:].strip()
        s = line.strip()
        if s.startswith(("- ", "* ")):
            ids = []
            for m in TRACE.finditer(s):
                ids += [x.strip() for x in m.group(1).split(",") if x.strip()]
            yield i, section, TRACE.sub("", s[2:]).strip(), ids


def lint(md, data, audience="users", max_words=32):
    by_id = {c["id"]: c for c in data["changes"]}
    for c in data["changes"]:
        by_id.setdefault(c["sha"], c)
    errs, warns, shown, in_upgrade = [], [], set(), set()
    for ln, sec, text, ids in bullets(md):
        if not ids:
            errs.append(f"L{ln}: no trace tag <!-- src: ... --> (every line must point at a change)")
            continue
        srcs = []
        for x in ids:
            c = by_id.get(x)
            if not c:
                errs.append(f"L{ln}: trace '{x}' is not in this release range")
                continue
            srcs.append(c); shown.add(c["id"])
            if c.get("sort") == "quiet":
                errs.append(f"L{ln}: '{x}' is sorted quiet; readers never see it, so leave it out")
            if "upgrade" in sec.lower() or sec.lower().startswith("before"):
                in_upgrade.add(c["id"])
        evidence = " ".join(c["subject"] + " " + c.get("body", "") + " " + c.get("note", "") for c in srcs)
        for n in NUM.findall(re.sub(r"`[^`]*`", "", text)):
            if not re.search(r"(?<![\d.])" + re.escape(n) + r"(?![\d]|\.\d)", evidence):
                errs.append(f"L{ln}: number {n} does not appear in the traced change(s); check it or remove it")
        words = len(text.split())
        if words > max_words:
            warns.append(f"L{ln}: {words} words; keep a line under {max_words}")
        if WEAK_OPENERS.search(re.sub(r"^\*\*[^*]+\*\*\s*", "", text)):
            warns.append(f"L{ln}: opens with 'fixed a bug'; say what now works for the reader")
        if audience == "users":
            low = " " + text.lower() + " "
            for j in JARGON_USERS:
                if " " + j in low:
                    warns.append(f"L{ln}: jargon '{j.strip()}' for an end-user audience")
            for m in IDENT.findall(text):
                warns.append(f"L{ln}: code-style name '{m}'; use the words people see on screen")
            if PATHISH.search(text):
                warns.append(f"L{ln}: file path in user notes")
    for c in data["changes"]:
        if c.get("sort") == "act" and c["id"] not in shown:
            errs.append(f"missing: '{c['id']}' needs reader action but is not in the notes ({c['subject'][:60]})")
        if c.get("sort") == "act" and c["id"] in shown and c["id"] not in in_upgrade:
            warns.append(f"'{c['id']}' needs action but is not under 'Before you upgrade' at the top")
        if c.get("sort") == "see" and c["id"] not in shown:
            warns.append(f"not shown: '{c['id']}' is sorted see but has no line ({c['subject'][:60]})")
        if not c.get("sort"):
            errs.append(f"unsorted: '{c['id']}' ({c['subject'][:60]})")
        if c.get("sort") == "quiet" and ({"breaking", "migration", "security"} & set(c.get("hints", []))):
            warns.append(f"'{c['id']}' is sorted quiet but has hints {c['hints']}; confirm nobody must act")
    return errs, warns


def coverage(data, md):
    shown = {x for _, _, _, ids in bullets(md) for x in ids}
    ch = data["changes"]
    cnt = {k: sum(1 for c in ch if c.get("sort") == k) for k in ("act", "see", "quiet")}
    hit = sum(1 for c in ch if c["id"] in shown or c["sha"] in shown)
    return f"{len(ch)} changes: {cnt['act']} act, {cnt['see']} see, {cnt['quiet']} quiet; {hit} traced in the notes"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("collect"); c.add_argument("frm"); c.add_argument("to"); c.add_argument("--repo"); c.add_argument("--all-commits", action="store_true")
    k = s.add_parser("skeleton"); k.add_argument("changes"); k.add_argument("--title", default="What's new")
    l = s.add_parser("lint"); l.add_argument("draft"); l.add_argument("changes"); l.add_argument("--audience", choices=["users", "integrators"], default="users"); l.add_argument("--max-words", type=int, default=32)
    r = s.add_parser("render"); r.add_argument("draft"); r.add_argument("--changes")
    a = p.parse_args(argv)
    if a.cmd == "collect":
        print(json.dumps(collect(a.frm, a.to, a.repo, not a.all_commits), indent=1, ensure_ascii=False)); return 0
    if a.cmd == "skeleton":
        print(skeleton(load(a.changes), a.title)); return 0
    if a.cmd == "lint":
        md = open(a.draft, encoding="utf-8").read()
        data = load(a.changes)
        errs, warns = lint(md, data, a.audience, a.max_words)
        for e in errs: print("ERROR", e)
        for w in warns: print("WARN ", w)
        print(("FAIL" if errs else "PASS") + f": {len(errs)} errors, {len(warns)} warnings. " + coverage(data, md))
        return 1 if errs else 0
    if a.cmd == "render":
        md = open(a.draft, encoding="utf-8").read()
        out = "\n".join(TRACE.sub("", ln).rstrip() for ln in md.splitlines())
        print(re.sub(r"\n{3,}", "\n\n", out).strip() + "\n")
        if a.changes:
            print("<!-- " + coverage(load(a.changes), md) + " -->")
        return 0


if __name__ == "__main__":
    sys.exit(main())
