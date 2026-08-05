# Research Report: Claude Testing Kit — Prompt Engineering for BDD Test Case Generator

**Date:** 2026-08-05
**Repo:** https://github.com/anhtester/claude-testing-kit
**Author:** Anh Tester — Vietnamese testing community
**Stars:** 47 | Forks: 23 | License: MIT

## Executive Summary

Claude Testing Kit is a pre-configured AI Agent toolkit for Claude Code covering the full testing lifecycle: requirements analysis -> test case design -> automation scripts -> CI/CD -> reporting. It uses structured 6-step plans, rule-based constraints, quality gates, role assignments, and output format enforcement — patterns directly applicable to our BDD Test Case Generator.

Key takeaways for our app: (1) the AI Self-Quality Gate with 5 criteria as post-generation validation, (2) the field-type checklist covering 15 input types ensuring exhaustive coverage, (3) structured risk-based test sizing (High/Med/Low -> TC counts), and (4) the consistent prompt structure: ROLE -> TASK -> CONTEXT -> CONSTRAINTS -> OUTPUT FORMAT.

## Prompt Engineering Patterns

### 1. Prompt Structure (borrowed from their API test prompt)

```
# ROLE       — Senior [Domain] Engineer with [X] years experience
# TASK       — One clear verb: "Write", "Generate", "Analyze"
# CONTEXT    — Frameworks, URLs, credentials, input data
# CONSTRAINTS — Numbered, concrete, measurable rules
# OUTPUT FORMAT — File type, naming convention, schema
```

This is cleaner than our current prompts which lack explicit ROLE/STRUCTURE sections.

### 2. AI Self-Quality Gate (5 Criteria)

Their test case generation prompt requires the AI to self-validate:

1. Unique TC IDs per module (no duplicates)
2. Each step has exactly one expected result (1:1 mapping)
3. Concrete test data (not "enter valid email" but "enter user@example.com")
4. All 15 field types covered in validation
5. Automation metadata (Automatable Y/N, Auto Type, Tags)

**Our equivalent**: Our `gate()` function does Gherkin parse + dedup. We could add step-result 1:1 check and field-type coverage to our quality gate.

### 3. Risk-Based Test Sizing

```
High Risk:   8-15 test cases
Medium Risk: 4-8 test cases
Low Risk:    2-4 test cases
```

**Relevance**: Our generation prompt could instruct the LLM to generate test cases proportional to feature complexity, avoiding both under-coverage and bloat.

### 4. 15 Input Field Types Checklist

Text, Email, Phone, Date, Number, Dropdown, Checkbox/Radio, File Upload, Password, Textarea, OTP/MFA, Date Range, Rich Text, Multi-Select, Range Slider.

**Relevance**: Our `merge.py` could check whether generated test cases cover the input types detected in the UI inventory. Our extraction prompt could tag acceptance criteria by input field type for richer coverage analysis.

### 5. Non-Functional Scenarios

Race condition / double-submit, session timeout / network interruption, localization (UTF-8, Emoji), keyboard-only accessibility (Tab, Enter, Esc), HTTP status codes for API testing.

**Relevance**: Our generation prompt currently only covers positive/negative/edge/boundary categories. Adding these non-functional scenario types would improve coverage for real-world apps.

### 6. API Testing Coverage (12 Status Codes)

200, 201, 400, 401, 403, 404, 406, 409, 413, 415, 429, 500 — with OWASP API Security (BOLA/IDOR, mass assignment, SQLi/XSS, ReDoS) and SLA < 2s.

**Relevance**: If we extend to API test case generation, this checklist provides a ready-made coverage specification.

## Prompt Improvements for Our App

### Current extraction_v1.md — add structure

Current prompt lacks explicit ROLE, CONSTRAINTS, OUTPUT FORMAT sections. Suggested:

```
# ROLE
You are a Senior Business Analyst with 10 years of experience extracting structured requirements from technical documents.

# TASK
Extract features and acceptance criteria from the document below. Tag each criterion as explicit (directly stated) or inferred (implied by context).

# CONSTRAINTS
1. Every feature MUST have source_location citing the original document section
2. Every acceptance criterion MUST have grounding: "explicit" or "inferred"
3. Identify at least the following input field types if present: text, email, number, dropdown, file upload, password, date, checkbox/radio, textarea, OTP, multi-select
4. Output ONLY valid JSON matching the schema below. No prose, no markdown fences.

# OUTPUT FORMAT (JSON schema)
...existing schema...
```

### Current generation_v1.md — add quality gate

Existing prompt has minimal rules. Add:

```
# SELF-QUALITY GATE (validate your output before returning)
1. Every tc_id is unique across all test cases
2. Every step describes intent, not UI mechanics (no "click", "type", "press")
3. Every grounding_source contains exact text from the original requirements
4. For each feature, generate at least:
   - positive scenarios: 2-4
   - negative scenarios: 2-4
   - boundary/edge scenarios: 1-2
5. Append " (inferred)" to grounding_source when citing an acceptance criterion with grounding: "inferred"
```

## Architecture Patterns from claude-testing-kit

### Multi-Platform Support
Kit supports both `.claude/` (Claude Code) and `.agent/` (Antigravity/Gemini CLI) simultaneously by sharing `plans/`, `prompt_templates/`, `scripts/`, and `practices/` directories.

**Relevance**: Our prompt files live in `apps/api/prompts/`. If we adopt their structure, we could add versioned prompt files and share them between CLI, server, and any future integrations.

### 6-Step Plan Workflows
Complex tasks use a `plans/<topic>/` folder with numbered `step-0X-*.md` files + `QUICK_START.md`. Each step is self-contained with its own prompt and output.

**Relevance**: Our `plans/` already follows this pattern. We could add `QUICK_START.md` for new users.

### Skill-Centric Architecture
10 specialized skills (automation engineer, manual testing, UI debug, locator healer, test data generator, framework architect, jira integration, etc.) each with SKILL.md defining ROLE, CAPABILITIES, CONSTRAINTS, TOOLS.

**Relevance**: Our `extract.py`, `generate.py`, `verify.py` modules serve the same purpose but as Python code. Could be supplemented with reusable prompt skill definitions.

## Actionable Recommendations

### Priority 1 (easy, high impact)

1. **Add ROLE/TASK/CONSTRAINTS structure to extraction_v1.md**
   - Copy the structured format from claude-testing-kit
   - Add field type detection to extraction

2. **Add self-quality gate to generation_v1.md**
   - TC count per category (positive 2-4, negative 2-4, boundary 1-2)
   - Concrete data requirement
   - Step-intent declaration (no "click", "type")

3. **Add 15-field-type awareness to merge.py**
   - When UI inventory detects input fields, ensure test cases cover those types

### Priority 2 (medium effort)

4. **Add non-functional scenario category**
   - Race condition, session timeout, localization, keyboard a11y
   - Extend Category enum: `race_condition`, `session_resilience`, `localization`, `accessibility`

5. **Extend self-quality gate metrics**
   - Per-feature TC count audit (too few = under-coverage warning)
   - Step-expected 1:1 ratio check

### Priority 3 (future)

6. **API test case generation mode**
   - Use the 12-status-code + OWASP checklist
   - Auto-generate from Swagger/OpenAPI specs

## Unresolved Questions

- Should we support Vietnamese language prompts for Vietnamese BA docs? The claude-testing-kit is Vietnamese-first.
- Should field-type coverage be a hard metric or informational?
- How to handle the 15 field types when no UI inventory is available (text-only BA doc)?
