# Skill Invocation Guide

Use this reference when explaining how Codex selects and invokes skills.

## Implicit Invocation

Codex compares the user's request with each available skill's `name` and `description`. A clear description must state what the skill does and when it applies. Implicit invocation is convenient but depends on task wording and the current skill catalog.

## Explicit Invocation

Use `$skill-name` when the user wants deterministic selection:

```text
$spreadsheets analyze this attendance workbook
$browser open the dashboard and inspect the current status
$skill-navigator explain which skill should handle this file
```

Explicit invocation selects the skill workflow; it does not automatically provide missing applications, connectors, credentials, or permissions.

## Routing Workflow

1. Discover candidate skills from metadata.
2. Select the smallest skill set that covers the requested outcome.
3. Read each selected `SKILL.md` completely before taking task actions.
4. Read only the referenced resources needed for the current variant.
5. Follow the selected skill's workflow and the user's instructions.
6. Report missing dependencies instead of silently substituting a materially different workflow.

When the user asks only for a recommendation or explanation, do not execute the target workflow. When the user asks to perform the task, continue with the selected skill after completing its required setup and validation steps.
