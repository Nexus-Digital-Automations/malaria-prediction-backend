# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant architectural decisions made in the Malaria Prediction System.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./adr-001-fastapi-framework.md) | FastAPI as API Framework | Accepted | 2024-01 |
| [ADR-002](./adr-002-ml-model-architecture.md) | Ensemble ML Model Architecture | Accepted | 2024-01 |
| [ADR-003](./adr-003-timescaledb-time-series.md) | TimescaleDB for Time-Series Data | Accepted | 2024-01 |
| [ADR-004](./adr-004-multi-source-data-integration.md) | Multi-Source Environmental Data Integration | Accepted | 2024-01 |
| [ADR-005](./adr-005-jwt-authentication.md) | JWT-Based Authentication | Accepted | 2024-01 |

## ADR Template

When creating new ADRs, use the following template:

```markdown
# ADR-XXX: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?
```

## References

- [Architecture Documentation](../README.md)
- [Michael Nygard's ADR Article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
