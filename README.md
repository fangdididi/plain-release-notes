# plain-release-notes

**English** | [简体中文](README.zh-CN.md)

An agent skill for writing release notes that the people who use your software actually read, where every line traces back to a real change, nothing that needs action goes missing, and internal noise stays out.

Most release notes are either a pasted commit log nobody outside the team understands, or polished prose that invents details and forgets the one breaking change. This skill makes the agent write for readers in their own words, while a hidden trace on every line and a strict linter keep the notes honest.

## Features

- **Exact range, not vibes.** `collect` lists every merged PR (or commit) between two refs, with hint flags for breaking, migration, config, security, deprecation and dependency changes.
- **Three sorts.** Each change is *act* (reader must do something), *see* (reader will notice) or *quiet* (internal only). Act items always go first, under "Before you upgrade". Quiet items are counted and never shown.
- **Traceable lines.** Every bullet carries `<!-- src: #ID -->`. The linter rejects lines with no trace, traces outside the range, and numbers the traced change never states.
- **Coverage you can't skip.** A missing act item is an error. An unshown see item is a warning. A "quiet" item with a breaking or security hint gets flagged for a second look.
- **Plain-words checks** for end users: flags "fixed a bug" openers, jargon, code identifiers, file paths and over-long lines. Use `--audience integrators` for developer-facing notes.
- **Clean output.** `render` strips the trace tags and leaves a one-line coverage comment.
- Single Python file, standard library only. `collect` also needs git.

## Install

Copy the folder into your agent's skills directory, for example:

```bash
git clone https://github.com/fangdididi/plain-release-notes ~/.claude/skills/plain-release-notes
```

Then ask: *"Write the release notes for v1.5 (since v1.4.0)."*

## Usage

```bash
python3 scripts/relnotes.py collect v1.4.0 v1.5.0 --repo . > changes.json   # add --all-commits for linear history
# fill sort / heading / note for every change in changes.json
python3 scripts/relnotes.py skeleton changes.json --title "What's new in 1.5" > draft.md
# rewrite bullets for readers, keep the src tags
python3 scripts/relnotes.py lint draft.md changes.json [--audience users|integrators] [--max-words 32]
python3 scripts/relnotes.py render draft.md --changes changes.json > RELEASE_NOTES.md
```

## Example

`examples/make_demo_repo.sh` builds a small demo repo for a notes app with seven changes between `v1.4.0` and `v1.5.0`.

- `examples/draft.md` passes lint with 0 errors and 0 warnings.
- `examples/draft-bad.md` ("Search is 10x faster after refactor of NoteStore", CI caching, nothing about the sync server upgrade) fails:

```
ERROR L6: '#45' is sorted quiet; readers never see it, so leave it out
ERROR L6: number 10 does not appear in the traced change(s); check it or remove it
ERROR L8: no trace tag <!-- src: ... --> (every line must point at a change)
ERROR missing: '#44' needs reader action but is not in the notes
WARN  L5: opens with 'fixed a bug'; say what now works for the reader
FAIL: 5 errors, 6 warnings. 7 changes: 1 act, 3 see, 3 quiet; 4 traced in the notes
```

The rendered public version is in `examples/public.md`.

## File structure

```
plain-release-notes/
├── SKILL.md / SKILL.zh-CN.md      # the skill (English / Chinese)
├── README.md / README.zh-CN.md
├── scripts/relnotes.py            # collect / skeleton / lint / render
├── examples/
│   ├── make_demo_repo.sh          # builds the demo git repo
│   ├── changes.json               # sorted changes for v1.4.0..v1.5.0
│   ├── draft.md / draft-bad.md    # passing and failing drafts
│   ├── lint-draft*.txt            # linter output for both
│   └── public.md                  # rendered notes
├── tests/test_relnotes.py         # 12 tests: python3 -m unittest discover -s tests
└── LICENSE
```

## License

MIT © fangdididi
