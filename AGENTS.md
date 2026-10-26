# AGENTS.md

The entry point for coding agents other than Claude Code, such as Google Antigravity. The project's rules live in one place, [CLAUDE.md](CLAUDE.md), and apply to you in full. This file adds only what another agent needs to apply them, so the two cannot drift apart (D20).

@[CLAUDE.md](CLAUDE.md)

Make no commit, push or pull request until you have read `CLAUDE.md`. If the line above did not expand into its text, open the file.

## Where CLAUDE.md names a Claude Code tool

| It says | You do |
| --- | --- |
| `superpowers:` skills, in the task loop | You do not have them. Follow each step by hand: a spec and a plan (a paragraph for a small item), tests before code, the checks run before you say it works, and a review of your own diff. |
| `/research-factor <id>` | Follow [.claude/commands/research-factor.md](.claude/commands/research-factor.md) as a recipe, reading `$ARGUMENTS` as the factor id. Run its shell snippets in Git Bash. Leave out step 7's Artifact, which needs a Claude Code tool, and say so in the pull request. |
| `/code-review` | Review your own diff against the spec and the guardrails, and list what you found in the pull request. |

Read `.claude/commands/`, but do not edit `.claude/`: it is Claude Code's configuration.

## Working alongside Claude Code

Both agents work in the same clone, so:

- A branch has one agent at a time. Before you start, run `git branch --show-current` and `git status`. If the tree holds changes you did not make, stop and ask the owner.
- Work on your own branch from `main`, named as `CLAUDE.md` says. If both agents work at once, give each its own worktree (`git worktree add ../Livability-Atlas-<name> -b <branch> main`), and point `ATLAS_DATA_DIR` at one shared folder so they share `data/`.
- Hand over by committing. Leave nothing uncommitted, and read "Now" in `docs/progress.md` again before you edit it, since the other agent may have moved it. When it conflicts, keep both log entries, newest first.

## Keeping this file thin

A rule goes in `CLAUDE.md`, never here. A nested `CLAUDE.md`, such as those planned for `pipeline/` and `web/`, gets a sibling `AGENTS.md` made of one include line, because Antigravity loads `AGENTS.md` folder by folder and does not read `CLAUDE.md`. The include syntax is in D20. Do not write it anywhere else in this file, or it expands there too.
