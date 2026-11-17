---
name: plain-release-notes
description: Turn an exact git range into release notes that the people who use the software can actually read, where every line traces back to a real change, nothing that needs action is missed, and internal noise stays out. Use when asked to write release notes, a changelog entry, "what's new", an update announcement, or app-store notes for a version.
---

# Plain Release Notes

Release notes go wrong in two predictable ways. Either they are a pasted commit log ("bump deps, refactor NoteStore, fix #43"), which nobody outside the team can read, or they are smooth marketing prose that quietly invents things, rounds numbers up, and forgets the one change that breaks people's setup.

This skill sits between the two. You write for the reader, in their words, but the draft carries a hidden trace on every line pointing at the change it came from, and a linter refuses to pass a draft that:

- has a line that traces to nothing, or to something outside the release;
- quotes a number that the traced change never states;
- leaves out a change that requires the reader to do something;
- shows internal work the reader will never notice.

## When to use

- "Write the release notes for v1.5" / "what changed since the last tag?"
- A changelog entry, a "What's new" dialog, an app-store update text, an upgrade email.
- Reviewing someone else's notes before they ship.

Not for: internal sprint reports or engineering changelogs meant for the team. Those can keep the jargon.

## The three sorts

Every change in the range gets exactly one sort. Sorting is the real work; do it before writing a single sentence.

| Sort | Meaning | Goes where |
|------|---------|------------|
| **act** | The reader must do something, or something stops working: breaking change, migration, new required setting, permission, minimum version | Top section **Before you upgrade**, always |
| **see** | The reader will notice it: a new ability, something faster, an annoyance gone | Grouped by what the reader is doing ("When you search") |
| **quiet** | Nobody outside the team will notice: refactors, tests, CI, internal tooling, dependency bumps with no visible effect | Not in the notes. Counted, never shown |

When unsure between see and quiet, ask: *would a user who never reads code notice this within a week?* When unsure between act and see, ask: *what happens if they upgrade without reading anything?*

## Steps

1. **Pin the range.** Get the exact two refs (previous release tag, new tag or commit). Never write from "recent commits".
   ```bash
   python3 scripts/relnotes.py collect v1.4.0 v1.5.0 --repo . > changes.json
   ```
   Merge-based repos list merged pull requests; add `--all-commits` for squash or linear history. Each change carries hints (`breaking`, `migration`, `config`, `security`, `deprecation`, `dependency`) and a `guess` (`act` for breaking/migration, `quiet` for chore/test/ci/refactor prefixes).
2. **Sort every change.** Fill `sort` (act/see/quiet), `heading` (the reader's activity, for see items) and `note` (one plain sentence) in `changes.json`. Treat the guess as a suggestion only. Read the body and files of anything with a risky hint. If a "quiet" item has a `breaking` or `security` hint, prove nobody needs to act before keeping it quiet.
3. **Draft from the skeleton.**
   ```bash
   python3 scripts/relnotes.py skeleton changes.json --title "What's new in Jotter 1.5" > draft.md
   ```
   Rewrite each bullet for the reader. Keep the `<!-- src: ID -->` tag on every bullet; one change may produce two bullets, and one bullet may cite two changes.
4. **Write the way readers scan.**
   - Lead each bullet with the outcome in bold, then at most one sentence of detail.
   - Say what they can do now, not what you did ("Markdown exports keep your line breaks", not "Fixed a bug in export").
   - For act items, say who is affected, what to do, and in what order ("Run your own sync server? Upgrade it to 2.0 first").
   - Numbers only if the change states them, with the baseline ("about 0.4 s on 10000 notes, down from 2.5 s").
   - Use the words on screen, not class names, file paths or ticket jargon.
   - One opening line on what the release means for the reader. No "we're excited".
5. **Lint until it passes.**
   ```bash
   python3 scripts/relnotes.py lint draft.md changes.json            # end users (default)
   python3 scripts/relnotes.py lint draft.md changes.json --audience integrators
   ```
   Errors block publishing; warnings need a decision. `--audience integrators` allows code names and paths for developer-facing notes.
6. **Render and hand over.**
   ```bash
   python3 scripts/relnotes.py render draft.md --changes changes.json > RELEASE_NOTES.md
   ```
   Trace tags are removed. A short hidden coverage line remains (how many act/see/quiet, how many traced). Keep `changes.json` and `draft.md` beside the release, so anyone can later ask "where did this line come from?"

## Example

Range `v1.4.0..v1.5.0` of a demo notes app has seven changes: attachment search (#41), tests (#42), an export fix (#43), pinned notes needing sync server 2.0 (#44), a refactor (#45), CI caching (#46) and system dark mode (#47).

Sorted: #44 act; #41, #43, #47 see; #42, #45, #46 quiet. Result:

```markdown
## Before you upgrade
- **Run your own sync server?** Upgrade it to 2.0 or newer first. Older servers refuse pinned notes and stop syncing.

## When you search
- **Search looks inside attachments.** Text in PDFs and images now turns up in results.
- **Results come back faster:** about 0.4 s on 10000 notes, down from 2.5 s.
```

A careless draft of the same release ("Search is 10x faster after refactor of NoteStore", "Cached wheels in CI", with no mention of the sync server) fails with 5 errors: an invented number, two internal items, an untraced line, and the missing act item. See `examples/`.

## Tips

- If the release has no act items, say nothing about upgrading. Don't add a reassuring empty section.
- A security fix that users can't act on is still see if it changes their risk ("Shared links now expire after 30 days"). Write it plainly, without exploit details.
- Deprecations are act items for the release that announces them: what stops working, when, and what to use instead.
- If you can't explain a change in reader terms, it's probably quiet. If it isn't quiet, ask the author rather than guessing.
- Short beats complete for see items. Coverage warnings for unshown see items are allowed if you choose to drop minor ones. Act items can never be dropped.
