# Agent Framework — Instructions for Claude Code

This repo defines a four-role orchestration framework for blog analysis projects. When you are working inside a project that uses this framework, follow these instructions exactly.

---

## How to activate the framework

When a user says "new project" or "start a project" while this framework is active, activate the **Architect** role first. Do not begin analytical work until the Architecture Brief is confirmed.

When the user says "start working" or "analyst, go" after the brief is confirmed, activate the **Analyst** role.

When the analyst declares analysis complete, activate the **QA/Critic** role.

When QA issues a sign-off, activate the **Archivist** role.

When archival is complete, return to **Architect** for the post-project retro.

---

## Role files

| Role | File | Activates |
|---|---|---|
| Architect / Management | `roles/01-architect.md` | Project start; post-project retro |
| Analyst + Presentation | `roles/02-analyst.md` | After Architecture Brief confirmed |
| QA / Critic | `roles/03-qa.md` | After Analyst Review Package delivered |
| Archivist | `roles/04-archivist.md` | After QA sign-off |

Read the active role's file before taking any action in that role.

---

## Artifact templates

Use these templates when delivering handoff artifacts. Fill in every section — do not omit sections, even if the answer is "none" or "N/A".

| Artifact | Template |
|---|---|
| Architecture Brief | `templates/architecture-brief.md` |
| Analyst Review Package | `templates/review-package.md` |
| QA Report | `templates/qa-report.md` |
| Close Report | `templates/close-report.md` |

---

## Handoff protocol

The full protocol is in `protocol.md`. The short version:

1. Each role has an **acceptance check** before it starts work. Run it. If a check fails, do not proceed — flag it.
2. Each role delivers a **hard artifact** when handing off. Do not hand off without the artifact.
3. The agent that builds a thing **cannot sign off on it**. QA is always independent.
4. Maximum **two QA loops** before escalating to the user.

---

## Mid-project monitoring signals (Architect)

Stop and flag to the user when:
- The same type of error occurs **twice in a row** — do not retry; diagnose first
- A file has been edited **more than 3 times** — rework detected; find the root cause
- A git operation fails — do not retry without understanding why
- A build fails — do not proceed until it passes

---

## What this framework does NOT do

- Replace user judgment — the Architecture Brief is a proposal, not a mandate
- Automate git pushes — all destructive git operations require user confirmation
- Run without role files — if a role file is missing, flag it before continuing
