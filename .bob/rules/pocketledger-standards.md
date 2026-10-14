# PocketLedger Team Standards

## Rule 1 — Monetary amounts must use Decimal, never float

All Python functions that handle monetary amounts must use the `Decimal` type, never `float`.

**Rationale:** This avoids IEEE 754 rounding errors that are unacceptable for financial data.

---

## Rule 2 — React components must have JSDoc prop comments

All React components must have a JSDoc comment describing their props.

**Rationale:** Explicit prop documentation improves discoverability, reduces onboarding friction, and makes it easier to spot misuse at review time.

---

## Rule 3 — Audit log entry after every Agent mode interaction

After every Agent mode interaction, append a one-line entry to `bob-audit/audit.log` in the format:

```
[ISO timestamp] [mode] [brief description of change]
```

**Rationale:** Provides a lightweight, human-readable trail of all AI-assisted changes made to the codebase, supporting compliance and post-incident review.
