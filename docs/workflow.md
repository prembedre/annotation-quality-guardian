# 🔄 Workflow — Annotation Quality Guardian

## Git Branching Strategy

We follow **GitHub Flow** — a simple, trunk-based workflow.

```
main ────────────────────────────────────────────────►
  │                                        ▲
  └── feature/backend-auth ────────────────┘  (PR + review)
  └── feature/scoring-kappa ───────────────┘
  └── fix/db-migration-order ──────────────┘
```

### Branch Naming

| Type    | Pattern                         | Example                        |
|---------|---------------------------------|--------------------------------|
| Feature | `feature/<component>-<desc>`    | `feature/backend-auth`         |
| Bugfix  | `fix/<component>-<desc>`        | `fix/scoring-kappa-edge-case`  |
| Docs    | `docs/<desc>`                   | `docs/api-endpoints`           |

### PR Process

1. Create a feature branch from `main`.
2. Make focused commits with clear messages.
3. Open a Pull Request with a description of changes.
4. Request review from at least **one** team member.
5. Address feedback and merge via **squash merge**.

## Development Workflow

### Daily

1. Pull latest `main`.
2. Work on your assigned feature branch.
3. Write or update tests alongside your code.
4. Push and open a PR when ready.

### Weekly

- Team sync to review progress and blockers.
- Update [meeting notes](meeting-notes.md).

## Code Standards

| Language   | Formatter     | Linter       |
|------------|---------------|--------------|
| Python     | `black`       | `ruff`       |
| JavaScript | `prettier`    | `eslint`     |
| SQL        | manual review | —            |

## Commit Message Format

```
<type>(<scope>): <subject>

Examples:
feat(backend): add annotation list endpoint
fix(scoring): handle empty label lists in kappa
docs(readme): update setup instructions
test(gold): add edge case for zero annotations
```
