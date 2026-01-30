# Assessment data storage (PostgreSQL)

This document describes how WebCAF stores assessment-related data in PostgreSQL for the local government use case.

## Where data lives

The core assessment record is stored in **`webcaf_assessment`**.
All question-level answers and user-provided evidence/notes are stored inside **`webcaf_assessment.assessments_data`** (a JSON column).

Supporting business context is stored in:
- **`webcaf_organisation`**: the local authority / organisation being assessed
- **`webcaf_system`**: the system under assessment (belongs to an organisation)
- **`webcaf_userprofile`**: maps a Django user to an organisation and a role
- **`webcaf_configuration`**: assessment period configuration (default framework, cutoff dates, etc)

Audit/history is captured via **`django-simple-history`** tables:
- **`webcaf_historicalassessment`**
- **`webcaf_historicalorganisation`**
- **`webcaf_historicalsystem`**
- **`webcaf_historicaluserprofile`**

## Core data domains (local government)

- **Identity & access**: Django `auth_user` + `webcaf_userprofile`
- **Organisation**: local authority metadata in `webcaf_organisation`
- **System**: systems owned/used by the organisation in `webcaf_system`
- **Assessment**: status, period, and framework in `webcaf_assessment`
- **Responses**: stored as JSON in `webcaf_assessment.assessments_data`
- **Configuration**: assessment period windows in `webcaf_configuration.config_data`

## Key tables and columns (current application model)

### `webcaf_organisation`
Stores organisation metadata.

Key columns:
- `id` (PK)
- `name` (unique)
- `reference` (generated human-readable reference)
- `organisation_type`
- `contact_name`, `contact_email`, `contact_role`
- `parent_organisation_id` (optional self-reference)

### `webcaf_system`
Stores systems that can be assessed for an organisation.

Key columns:
- `id` (PK)
- `name` (unique per organisation)
- `reference`
- `description`
- `system_type`
- `system_owner` (multi-select)
- `hosting_type` (multi-select)
- `last_assessed`
- `corporate_services` + `corporate_services_other`
- `organisation_id` (FK → `webcaf_organisation.id`)

### `webcaf_userprofile`
Maps a Django user to an organisation and role.

Key columns:
- `id` (PK)
- `user_id` (FK → `auth_user.id`)
- `organisation_id` (FK → `webcaf_organisation.id`, nullable)
- `role` (e.g. `organisation_lead`, `organisation_user`, `cyber_advisor`)

### `webcaf_assessment`
Represents an assessment instance for a system and assessment period.

Key columns:
- `id` (PK)
- `reference`
- `status` (`draft`, `submitted`, `completed`, `cancelled`)
- `framework` (e.g. `caf32`, `caf40`)
- `caf_profile` (`baseline`, `enhanced`)
- `review_type` (`independent`, `peer_review`, `self_assessment`, `not_decided`)
- `assessment_period` (e.g. `25/26`)
- `submission_due_date` (derived from configuration)
- `created_on`, `last_updated`
- `system_id` (FK → `webcaf_system.id`)
- `created_by_id`, `last_updated_by_id` (FK → `auth_user.id`, nullable)
- `assessments_data` (JSON) ← primary store for answers and notes

### `webcaf_configuration`
Stores assessment-period configuration in JSON.

Key columns:
- `id` (PK)
- `name` (unique, e.g. `default`, `26/27`)
- `config_data` (JSON)

Expected keys in `config_data`:
- `default_framework` (e.g. `caf32`)
- `current_assessment_period` (e.g. `25/26`)
- `assessment_period_end` (string formatted like `31 March 2026 11:59pm`)

Note: the code path that selects the “default configuration” uses PostgreSQL’s `to_timestamp(...)` to parse `assessment_period_end` from JSON at query time. If you run with SQLite, that function does not exist.

## Relationships (logical view)

```
Organisation (webcaf_organisation) 1 ── * System (webcaf_system) 1 ── * Assessment (webcaf_assessment)
                                  \                               \
                                   \                               └─ assessments_data (JSON answers)
                                    \
                                     * UserProfile (webcaf_userprofile) * ── 1 auth_user
```

## What is stored in `assessments_data`?

`assessments_data` is a JSON object that stores framework-specific responses.

### CAF structure (typical)
For CAF (e.g. `framework = caf32`), the JSON is keyed by outcome code (e.g. `A1.a`), and each outcome has stages such as `indicators` and `confirmation`.

Example (illustrative):
```json
{
  "A1.a": {
    "indicators": {
      "achieved_A1a_01": true,
      "achieved_A1a_01_comment": "Alternative control description (optional)",
      "partially-achieved_A1a_02": false,
      "not-achieved_A1a_03": false
    },
    "confirmation": {
      "confirm_outcome": "confirm",
      "confirm_outcome_confirm_comment": "Outcome summary written by the assessor",
      "outcome_status": "Achieved",
      "outcome_status_message": "…framework-derived message…"
    }
  }
}
```

Notes:
- Indicator field names are generated from the framework YAML/router and look like `achieved_*`, `partially-achieved_*`, `not-achieved_*` plus optional `*_comment` fields.
- Confirmation fields include `confirm_outcome` and optional free-text justification/comment fields. The system also stores derived status fields (e.g. `outcome_status`) when the confirmation step is saved.
- The UI logic treats an outcome as complete when `confirmation.confirm_outcome == "confirm"`.

### Cyber Essentials structure (typical)
When the Cyber Essentials (CE) flow is enabled, CE answers are stored under a dedicated top-level key (e.g. `cyber_essentials`) with per-section sub-objects.

Example (illustrative):
```json
{
  "cyber_essentials": {
    "A1": {
      "organisation_name": "Example Council",
      "…other CE form fields…": "…"
    }
  }
}
```

## Audit/history tables (change tracking)

The application uses `django-simple-history` to capture change history for key entities. These tables store “snapshots” over time along with:
- `history_date` (when the change happened)
- `history_type` (`+`, `~`, `-` for create/change/delete)
- `history_user_id` (who made the change, when available)

This is especially important for:
- Understanding “who changed what” in `assessments_data` over time
- Supporting review/assurance activities (e.g. identifying when statuses changed)

## Supporting tables you will see in PostgreSQL

PostgreSQL will also contain standard Django and dependency tables, for example:
- `auth_user`, `auth_group`, `django_admin_log`
- `django_session` (server-side sessions; some flows store the “current assessment/profile” selection here)
- `otp_email_emaildevice` (used for OTP, with a Notify-backed proxy model in the app)
- `axes_accessattempt` (rate limiting / lockouts for repeated login failures)

These are not “assessment answers” but are operationally important for authentication, auditing and security.

## Data classification and privacy notes

The database contains:
- **Personal data**: user identifiers, contact names/emails, and free-text comments within assessment answers
- **Potentially sensitive operational detail**: descriptions of systems, controls, exemptions, and alternative mitigations

For the local government context, treat assessment content as **sensitive by default** and apply least-privilege access.

## Retention and deletion (guidance)

Define retention in line with local policy and platform constraints. Common patterns:
- Retain draft assessments for a limited period (e.g. 6–12 months) if abandoned.
- Retain completed assessments for the statutory/audit period required (e.g. 7 years) if used as evidence for governance/assurance.
- Deleting an organisation or system should cascade carefully (or be prevented) to avoid losing evidence unexpectedly.

If retention is implemented, ensure you cover:
- `webcaf_assessment` and its `assessments_data` JSON payload
- `webcaf_historical*` tables (history may need matching retention rules)
