# Solution Architecture Document - WebCAF (Local Government)

## Document control

Guidance:
- Keep this accurate and up to date; use named roles rather than individuals if ownership may change.
- Update version, status, and date whenever material changes are made.

| Item | Value |
| --- | --- |
| Document owner | TBD |
| Author(s) | TBD |
| Reviewers | TBD |
| Version | 0.1 |
| Status | Draft |
| Last updated | TBD |

## Purpose and scope

Guidance:
- State why the document exists and who it is for (technical, security, delivery, governance).
- Define what is in scope and explicitly call out what is not.

Describe why this document exists and the boundaries of the solution.

- Purpose: Provide a complete solution architecture for the WebCAF local government service.
- In scope: Web application, data flows, integrations, infrastructure, security, operations.
- Out of scope: TBD.

## Background and drivers

Guidance:
- Explain the problem/opportunity and the policy or statutory drivers.
- Capture the high‑level business outcomes expected from this solution.

Summarize the problem, policy drivers, and business outcomes.

- Problem statement: Local government organisations need a secure, consistent and user‑friendly way to complete CAF self‑assessments and manage evidence, replacing ad‑hoc spreadsheets and email‑based processes.
- Policy drivers: NCSC CAF for local government; UK GDPR and data protection obligations; GOV.UK Service Manual and Technology Code of Practice; accessibility requirements.
- Business outcomes: Higher completion rates, reduced admin effort, more consistent assessment data, faster assurance cycles, and clearer reporting for programme oversight.

## Objectives and success criteria

Guidance:
- Objectives should be measurable and time‑bound where possible.
- Success criteria should be verifiable (e.g., % completion, deployment time, performance).

Define measurable objectives that indicate the solution is successful.

- Objective 1: Enable local government users to authenticate and complete CAF self‑assessments end‑to‑end.
- Objective 2: Capture structured assessment data for reporting and assurance.
- Success criteria:
  - At least 80% of pilot users complete a draft assessment without support.
  - Assessment data is stored centrally and can be exported for reporting within 24 hours.
  - Deployment is repeatable from code (Terraform + container image) in under 1 hour.

## Stakeholders and users

Guidance:
- List decision makers, delivery team, and user roles.
- Include external stakeholders (security, data protection, operations).

List stakeholders and primary user groups.

- Business owner: TBD.
- Product owner: TBD.
- Delivery team: TBD.
- User personas: TBD.

## Assumptions, constraints, and dependencies

Guidance:
- Assumptions: things believed true for planning (and to be validated).
- Constraints: non‑negotiable limits (budget, time, region, policy).
- Dependencies: services or teams required for delivery.

Capture key assumptions and constraints that shape the design.

- Assumptions:
  - Hosting will be in Azure UK regions.
  - The solution remains a single web application for the POC.
  - Users have access to GOV.UK One Login (or a suitable OIDC provider in sandbox).
- Constraints:
  - POC budget and timeline limit deep optimisation and multi‑region DR.
  - Data residency must remain within the UK.
  - Security accreditation is out of scope for the POC.
- Dependencies:
  - GOV.UK One Login (OIDC) for authentication.
  - GOV.UK Notify (optional) for emails.
  - Azure managed services: Container Apps, PostgreSQL Flexible Server, Key Vault, ACR, Log Analytics.

## Requirements

Guidance:
- Separate functional and non‑functional requirements.
- Number requirements for traceability (FR‑01, NFR‑01, etc.).

### Functional requirements

Guidance:
- Describe user‑facing capabilities and core workflows.
- Focus on “must have” POC requirements first.

- FR-01: TBD.
- FR-02: TBD.

### Non‑functional requirements

Guidance:
- Include targets for availability, performance, security, privacy, accessibility, and compliance.
- Note which NFRs are POC‑level vs production‑level.

List NFRs with measurable targets.

- Availability: TBD.
- Performance: TBD.
- Scalability: TBD.
- Security: TBD.
- Privacy: TBD.
- Accessibility: TBD (eg WCAG 2.2 AA).
- Compliance: TBD.

## Architecture overview

Guidance:
- Provide a concise summary of the target architecture and key decisions.
- Note why the chosen approach fits the constraints and objectives.

Provide a short summary of the target architecture and key design choices.

- Summary: TBD.
- Key decisions: TBD.

### Architecture views (C4 recommended)

Guidance:
- Explain what each C4 level shows and reference the diagram names/locations.
- Ensure diagrams are current and match the narrative.

- C4 overview: We use the C4 model to describe the system at four levels of detail so stakeholders can understand purpose, structure, and deployment. Each level answers a different question and links to the diagrams in `docs/architecture.drawio`.
- Context (C4 L1): Shows the system boundary, user roles, and external systems (e.g., OIDC, Notify). Diagram: **C4-Context**.
- Container (C4 L2): Shows the major runtime containers (web app, database, PDF generation) and their interactions. Diagram: **C4-Container**.
- Component (C4 L3): Breaks down the web application into logical modules (auth, workflow, framework parser, forms, reporting, persistence). Diagram: **C4-Component**.
- Deployment (C4 L4): Shows the runtime infrastructure and cloud services (Container Apps, Key Vault, PostgreSQL, ACR, Log Analytics). Diagram: **C4-Deployment**.

#### Diagram component list (what each box represents)

**C4-Context**
- Local Gov Assessor: primary end user completing assessments.
- Service Owner / Admin: manages organisations, systems, profiles, and configuration.
- WebCAF Local Government Service: the POC web application.
- External IdP (OIDC): GOV.UK One Login or equivalent OIDC provider.
- GOV.UK Notify: optional email delivery service.
- Reporting/Analytics: optional downstream reporting tools (e.g., Power BI).

**C4-Container**
- User (Browser): web client for assessors/admins.
- Web App Container: Django + GOV.UK Frontend serving UI and APIs.
- PDF Generation: WeasyPrint used in-process for report export.
- Relational DB: PostgreSQL used for core assessment data.
- OIDC Provider: external identity provider.
- GOV.UK Notify: optional email integration.

**C4-Component**
- Auth/SSO: OIDC login and local profile mapping.
- Assessment Workflow: draft creation, section routing, completion status.
- Framework Parser: CAF/CE YAML loading and interpretation.
- Form Factory + Validation: dynamic form generation per framework.
- Reporting/PDF Generation: export and rendering logic.
- Admin Views/Config: admin UI and configuration management.
- Persistence (Django ORM): database models and data access.

**C4-Deployment (Azure)**
- End Users: browser clients.
- Azure Container Apps: hosts the WebCAF container.
- Azure Database for PostgreSQL: primary datastore.
- Azure Key Vault: secrets for DB and OIDC.
- Azure Container Registry: image storage.
- Log Analytics: logging and monitoring.
- Build/Push: CI or ACR build step.

**AWS-Deployment (Legacy)**
- AWS ALB: public ingress/load balancer.
- ECS/Fargate Service: runs the WebCAF container.
- Amazon RDS (PostgreSQL): primary datastore (via RDS_* env vars).
- Secrets Manager/SSM: DB credentials and app secrets.
- Amazon ECR: image registry.
- GitHub Actions (OIDC): CI/CD and federation to AWS IAM.
- CloudWatch Logs: application and container logs.

## Application and service architecture

Guidance:
- Describe the app structure, domain boundaries, and key services/modules.
- Note any background tasks or scheduled jobs.

Describe application structure, domains, and service boundaries.

- Core services: TBD.
- Modules and responsibilities: TBD.
- Background jobs and schedulers: TBD.

## Data architecture

Guidance:
- Describe data domains, storage locations, and key tables/fields.
- Include data classification and retention expectations.

Describe data sources, stores, and flows.

- Data domains: TBD.
- Data stores: TBD.
- Data flows: TBD (add diagram).
- Data classification: TBD.
- Retention and deletion: TBD.

## Integration architecture

Guidance:
- List external systems and the protocols used (OIDC, REST, etc.).
- Document error handling, retries, and timeouts.

List external systems and integration patterns.

- External systems: TBD.
- APIs and protocols: TBD.
- Error handling and retries: TBD.

## Security architecture

Guidance:
- Cover identity, access control, secrets management, encryption, and audit logging.
- Summarise key threats and mitigations appropriate for this stage.

Describe identity, access, and security controls.

- Authentication and authorization: TBD.
- Secrets management: TBD.
- Encryption in transit and at rest: TBD.
- Audit logging: TBD.
- Threat model summary: TBD.

## Infrastructure and deployment architecture

Guidance:
- Describe environments, hosting model, CI/CD, and network topology.
- Call out differences between POC and production.

Describe hosting, environments, and deployment workflows.

- Environments: Dev, test, prod (TBD details).
- Hosting model: TBD (eg container apps, AKS, VM).
- CI/CD: TBD.
- Network topology: TBD.

## Observability and operations

Guidance:
- Specify logging, metrics, alerting, and incident response ownership.
- Include runbook expectations (start/stop, backup, key rotation).

Define monitoring, logging, and support processes.

- Metrics and alerts: TBD.
- Logging and audit trails: TBD.
- Incident response: TBD.
- Runbooks: TBD.

## Governance and decision records

Guidance:
- State how architectural decisions are captured and approved.
- Provide ADR location and ownership.

Use ADRs to capture key architectural decisions.

- ADR framework: https://www.gov.uk/government/publications/architectural-decision-record-framework/architectural-decision-record-framework
- ADR template (ADR-000): https://assets.publishing.service.gov.uk/media/692471975f7777c304ba7ed7/ADR-000_Subject_of_Decision.docx
- ADR register location: TBD.

## Standards and guidance alignment

Guidance:
- List standards and policy guidance that the solution must align to.
- Note any gaps or planned compliance work.

Reference relevant government guidance and standards.

- GOV.UK reference architecture guidance:
  https://www.gov.uk/guidance/develop-your-data-and-apis-using-a-reference-architecture
- GOV.UK Service Manual (governance principles):
  https://www.gov.uk/service-manual/agile-delivery/governance-principles-for-agile-service-delivery
- Other standards: TBD (eg NCSC CAF, Technology Code of Practice).

## Risks and mitigations

Guidance:
- Record top architectural risks and mitigation actions.
- Revisit after major changes or new dependencies.

Capture architectural risks and how they are addressed.

- Risk 1: TBD.
- Risk 2: TBD.

## Cost model and financial assumptions

Guidance:
- Identify main cost drivers and assumptions.
- Include expected cost ranges if available.

Summarize expected costs and assumptions.

- Cost drivers: TBD.
- Estimated monthly cost: TBD.
- Cost risks: TBD.

## Migration and transition plan

Guidance:
- Describe the path from POC to pilot/production.
- Include phases, dependencies, and rollback considerations.

Describe how to move from current to target state.

- Current state summary: TBD.
- Transition phases: TBD.
- Cutover approach: TBD.

## Testing and assurance

Guidance:
- List testing types and responsibilities (unit, integration, security, performance).
- Include service assessment readiness and accreditation steps.

Define testing and assurance approach.

- Unit and integration testing: TBD.
- Security testing: TBD.
- Performance testing: TBD.
- Service assessment readiness: TBD.

## Appendix

Guidance:
- Keep glossary and references short and relevant.

### Glossary

Guidance:
- Include key acronyms and service‑specific terms.

- CAF: Cyber Assessment Framework.
- ADR: Architectural Decision Record.
- TBD: To be determined.

### References

Guidance:
- Link to authoritative sources and supporting internal docs.

- Architectural Decision Record Framework (GOV.UK):
  https://www.gov.uk/government/publications/architectural-decision-record-framework/architectural-decision-record-framework
- ADR-000 template (GOV.UK):
  https://assets.publishing.service.gov.uk/media/692471975f7777c304ba7ed7/ADR-000_Subject_of_Decision.docx
- Reference architecture guidance (GOV.UK):
  https://www.gov.uk/guidance/develop-your-data-and-apis-using-a-reference-architecture
