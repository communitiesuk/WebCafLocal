# Solution Architecture Document - WebCAF (Local Government)

## Document control

| Item | Value |
| --- | --- |
| Document owner | Solution Architect (Local Government) |
| Author(s) | Solution Architect |
| Reviewers | Product Owner, Security Lead, Platform/Azure Lead |
| Version | 0.2 |
| Status | Draft |
| Last updated | 28 Jan 2026 |

## Purpose and scope

- Purpose: Define the solution architecture for the WebCAF Local Government proof‑of‑concept (POC), derived from GovAssure WebCAF, and describe how it can evolve to a production‑ready service.
- In scope: Web application, assessment workflows, data model, integrations (OIDC and Notify), Azure hosting, security controls, operations, and deployment automation (Terraform).
- Out of scope: Production accreditation and operational runbook sign‑off, service transition contracts, and long‑term data retention policy (to be agreed).

## Background and drivers

- Problem statement: Local government organisations need a secure and usable way to complete CAF self‑assessments and evidence readiness. The POC validates the feasibility of reusing the GovAssure WebCAF approach for local government.
- Policy drivers: NCSC CAF for local government; UK data protection (UK GDPR); GOV.UK Service Manual and Technology Code of Practice; accessibility and security obligations.
- Business outcomes: Faster assessment completion, consistent data capture for assurance, reduced manual administration, and a reusable architecture for wider rollout.

## Objectives and success criteria

- Objective 1: Provide a secure self‑assessment workflow (draft, complete, submit) for CAF and Cyber Essentials frameworks.
- Objective 2: Capture structured assessment data for reporting and assurance.
- Objective 3: Demonstrate Azure hosting and GOV.UK One Login integration in a sandbox environment.

Success criteria:
- Users can authenticate and complete an assessment end‑to‑end in the POC.
- Assessment data is stored centrally in PostgreSQL and can be exported for reporting.
- Deployment is repeatable via Terraform and container images.

## Stakeholders and users

- Business owner: Local Government sponsor / programme lead.
- Product owner: Service product lead.
- Delivery team: Developers, DevOps, security, UX.
- User personas: Local government assessors, system owners, and administrators.

## Assumptions, constraints, and dependencies

Assumptions:
- Hosting is in Azure UK regions.
- The POC uses a single primary region and a single database.
- GOV.UK One Login is available for the chosen environment (integration/sandbox).

Constraints:
- POC is not production‑ready; formal security accreditation is out of scope.
- Data residency must remain within UK regions.
- Cost and time are constrained to a pilot budget.

Dependencies:
- GOV.UK One Login (OIDC) for authentication.
- GOV.UK Notify (optional) for transactional emails.
- Azure Container Apps, ACR, Key Vault, Log Analytics, PostgreSQL Flexible Server.
- Terraform for infrastructure provisioning.

## Requirements

### Functional requirements

- FR‑01: User authentication (OIDC) with local profile mapping.
- FR‑02: Admin setup for organisations, systems, and user profiles.
- FR‑03: Create and manage CAF/CE draft assessments.
- FR‑04: Save answers, compute completion status, and show progress by objective/section.
- FR‑05: Generate and download assessment reports (PDF).
- FR‑06: Audit and administrative views for configuration and cutoff dates.

### Non‑functional requirements

- Availability: POC best‑effort; production target to be agreed (e.g., 99.5%).
- Performance: Page responses within 2 seconds for typical form loads under expected load.
- Scalability: Stateless web container; scale out via Container Apps; database vertical scaling.
- Security: Secrets in Key Vault; TLS in transit; least‑privilege RBAC.
- Privacy: UK GDPR compliance; DPIA required before production.
- Accessibility: WCAG 2.2 AA alignment for user‑facing flows.
- Compliance: CAF guidance, GOV.UK Service Manual, Technology Code of Practice.

## Architecture overview

Summary:
- The system is a Django web application that provides CAF/CE workflows and stores assessment answers in PostgreSQL. It runs as a container in Azure Container Apps, uses Key Vault for secrets, and integrates with OIDC and optional GOV.UK Notify.

Key decisions:
- Use a single Django application (monolith) for the POC for speed of delivery.
- Store assessment answers as JSON in the `webcaf_assessment` table for flexibility.
- Use Azure managed services (Container Apps, PostgreSQL Flexible Server, Key Vault).
- Use Terraform for repeatable infrastructure deployments.

### Architecture views (C4 recommended)

- Context (C4 L1): `docs/architecture.drawio` → diagram **C4-Context**.
- Container (C4 L2): `docs/architecture.drawio` → diagram **C4-Container**.
- Component (C4 L3): `docs/architecture.drawio` → diagram **C4-Component**.
- Deployment (C4 L4): `docs/architecture.drawio` → diagram **C4-Deployment**.

## Application and service architecture

- Core service: WebCAF Django application (UI + business logic).
- Major modules:
  - Authentication/SSO (OIDC and local dev auth).
  - Assessment workflow (drafts, sections, completion status).
  - Framework parser (CAF/CE YAML definitions).
  - Form factory and validation.
  - Reporting/PDF generation (WeasyPrint).
  - Admin configuration (profiles, systems, settings).
- Background jobs: None required for POC. Future options include scheduled report generation, notifications, and data exports.

## Data architecture

- Data domains: organisations, systems, user profiles, assessments.
- Primary store: PostgreSQL Flexible Server.
- Core table: `webcaf_assessment` with answers in `assessments_data` (JSON).
- Data relationships: see `docs/assessment-data-postgres.md`.
- Data flows: Browser → Web App → PostgreSQL; secrets from Key Vault injected as env vars.
- Data classification: Likely OFFICIAL (includes personal data such as contact names/emails). Confirm via DPIA.
- Retention and deletion: Define policy with programme owner; POC uses default DB retention. Production must implement archival and deletion schedules.

## Integration architecture

- OIDC (GOV.UK One Login): OAuth2/OIDC flows for authentication and user mapping.
- GOV.UK Notify (optional): For transactional emails (status, invitations).
- Reporting (optional): Power BI or data extracts from PostgreSQL.
- Protocols: HTTPS (OIDC, Notify), SQL/TLS (PostgreSQL), REST for app APIs.
- Error handling: Retry external calls where safe; surface user‑friendly errors on auth failures.

## Security architecture

- Authentication: OIDC (GOV.UK One Login); local auth only for dev/sandbox if enabled.
- Authorization: UserProfile‑based roles (admin, organisation lead/user).
- Secrets management: Azure Key Vault for database credentials, OIDC secrets, Django secret key.
- Encryption: TLS in transit; Azure‑managed encryption at rest for PostgreSQL and Key Vault.
- Audit logging: Application logs to Log Analytics; admin actions audited via Django admin and history logs.
- Threat model summary: Key risks are identity compromise, data leakage, and misconfiguration of cloud resources. Mitigated via RBAC, Key Vault, and monitoring.

## Infrastructure and deployment architecture

- Environments: Dev and sandbox are implemented; test/prod to be defined.
- Hosting model: Azure Container Apps (containerized Django app).
- Data: Azure PostgreSQL Flexible Server.
- Secrets: Azure Key Vault.
- Images: Azure Container Registry.
- Logging: Azure Log Analytics.
- Provisioning: Terraform (`infra/terraform`).
- CI/CD: GitHub Actions build/test and push images; ACR build supported.
- Network topology: Public web ingress for the app; database secured via firewall rules. Production should consider private endpoints.

## Observability and operations

- Logging: Structured application logs shipped to Log Analytics.
- Metrics/alerts: Container Apps and PostgreSQL metrics monitored; alerting thresholds to be defined.
- Incident response: Follow standard on‑call and incident management processes (to be defined).
- Runbooks: Draft runbooks needed for restart, scaling, backup/restore, and key rotation.

## Governance and decision records

- ADR framework: https://www.gov.uk/government/publications/architectural-decision-record-framework/architectural-decision-record-framework
- ADR template (ADR‑000): https://assets.publishing.service.gov.uk/media/692471975f7777c304ba7ed7/ADR-000_Subject_of_Decision.docx
- ADR register location: `docs/adr/` (to be created).

## Standards and guidance alignment

- NCSC Cyber Assessment Framework (CAF) for local government.
- GOV.UK Service Manual and Technology Code of Practice.
- GOV.UK One Login integration guidance.
- UK GDPR and data handling standards.
- Accessibility: WCAG 2.2 AA.

## Risks and mitigations

- Risk: OIDC integration downtime or configuration errors.
  - Mitigation: Environment‑specific configs, monitoring, and documented fallback.
- Risk: Data sensitivity and privacy requirements not fully addressed in POC.
  - Mitigation: DPIA, data classification review, and security assurance before production.
- Risk: Single‑region deployment (no DR).
  - Mitigation: Define RTO/RPO and implement backups/restore testing.
- Risk: Vendor lock‑in to Azure managed services.
  - Mitigation: Keep application containerized and infrastructure described via Terraform.

## Cost model and financial assumptions

- Cost drivers: Container Apps consumption, PostgreSQL tier, Log Analytics ingestion/retention, Key Vault operations, ACR storage.
- Estimated monthly cost: TBD (requires usage profile and log retention settings).
- Cost risks: Log Analytics retention and database scaling can drive unexpected cost increases.

## Migration and transition plan

- Current state: POC based on GovAssure WebCAF running in sandbox.
- Target state: Production‑ready service with security accreditation, operational runbooks, and defined data governance.
- Transition phases:
  1) POC validation and user feedback.
  2) Security and compliance hardening (DPIA, penetration testing).
  3) Operational readiness (monitoring, runbooks, backups, DR).
  4) Pilot with selected councils.
  5) Wider rollout.

## Testing and assurance

- Unit and integration testing: Django tests and integration tests in CI.
- End‑to‑end testing: Playwright/Behave tests for key journeys.
- Security testing: Dependency scanning, static analysis, and pen‑testing before production.
- Service assessment readiness: Align with GOV.UK Service Standard and assurance requirements.

## Appendix

### Glossary

- CAF: Cyber Assessment Framework.
- ADR: Architectural Decision Record.
- OIDC: OpenID Connect.
- POC: Proof of Concept.

### References

- Architectural Decision Record Framework (GOV.UK):
  https://www.gov.uk/government/publications/architectural-decision-record-framework/architectural-decision-record-framework
- ADR‑000 template (GOV.UK):
  https://assets.publishing.service.gov.uk/media/692471975f7777c304ba7ed7/ADR-000_Subject_of_Decision.docx
- Reference architecture guidance (GOV.UK):
  https://www.gov.uk/guidance/develop-your-data-and-apis-using-a-reference-architecture
- Assessment data storage notes: `docs/assessment-data-postgres.md`
- Dev Azure overview: `docs/dev-azure-overview.md`
- One Login integration: `docs/govuk-one-login.md`
