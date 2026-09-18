# Skill Structure

Use this reference when explaining or validating a Codex skill folder.

## Minimum Structure

```text
skill-name/
`-- SKILL.md
```

`SKILL.md` requires YAML frontmatter containing only `name` and `description`, followed by Markdown instructions. The folder name should match `name`.

## Extended Structure

```text
skill-name/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- scripts/
|-- references/
`-- assets/
```

- `agents/openai.yaml`: UI-facing display metadata and optional invocation policy.
- `scripts/`: deterministic or repeatedly used executable helpers.
- `references/`: detailed documentation loaded only when relevant.
- `assets/`: templates, images, fonts, or boilerplate used in outputs.

## Validation Checklist

1. Confirm the folder and frontmatter names match.
2. Confirm `description` states both capability and trigger conditions.
3. Keep core workflow instructions in `SKILL.md` and keep it concise.
4. Link every optional reference directly from `SKILL.md` with a clear read condition.
5. Avoid duplicated guidance across `SKILL.md` and `references/`.
6. Test every included script on a representative input.
7. Verify `agents/openai.yaml` still matches the skill behavior.
8. Do not add unrelated README, changelog, installation, or process-history files.

Structural validity does not prove operational readiness. Check tool availability, credentials, platform requirements, and external permissions separately.
