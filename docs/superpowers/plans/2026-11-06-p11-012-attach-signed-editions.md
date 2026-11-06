# Attach signed editions approved by one order (extension of `scripts/attach_shelf_scans.py`)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Put a set of signed instructions on the shelf when they were all approved by one order. Case from the product owner (production): a folder of signed ИОТ and the order that approves them, itself a shelf place. The order puts them all in force from one date. All of them are PDFs, and each file name starts with its place code. Today's script cannot do this:

- it finds files by `legacy_location`;
- it takes only places whose curated status is «Есть»;
- it skips types that require an approval order (ИОТ require one).

**Approach:** extend the script approved on 2026-11-06 (plan `2026-11-06-p11-012-attach-shelf-scans.md`, PR #16). It still uses the existing handlers and audit, has no DELETE and needs no new API or migration.

## Decisions (review these)

| # | Decision | Why |
|---|---|---|
| E1 | `--match-by-code`: every `*.pdf` directly in `--root` whose name starts with a place code (`^[А-ЯЁа-яё]+\.\d{2}\.\d{2}`) is that place's file; `legacy_location` is ignored. Several files for one code → `ambiguous`; a code with no place → reported as `unknown_code`. | The files are named by code. |
| E2 | `--approval-order ОТ.05.02`: the order's place is processed **first**: develop as a draft of the place's type (must be `order`), `effective_from`, upload, approve, activate. The script stops before the other files if the order fails. Then every other document gets `approved_by_document_id` = the order (draft edit) before approve and activate. Types requiring an order are no longer skipped in this mode. | The order is required for ИОТ activation (P11-001 D1–D20); it must be in force first. |
| E3 | In `--match-by-code` mode the curated statuses «Есть», «В работе (проект)» and «Есть — нужен пересмотр» are accepted; places that are excluded, «Нет», «Уточнить», or have any linked document are skipped with a reason. | A signed file proves the document exists; the workbook status may be older. |
| E4 | Each PDF is uploaded as the **working file** (needed for approval) and, after approval, attached again as the **signed scan**, so the panel shows «Скан подписанной редакции». | D1: the signed edition is shown as the signed scan. |
| E5 | One `--effective-from` for all, including the order (the date the order puts them in force); `--order-note "№ … от …"` goes to the order's `notes`. | Taken from the order text by the operator. |
| E6 | The real run is done by the operator on the production server or an operator machine with the production `DATABASE_URL` and `STORAGE_*`. The agent has no production access and never handles its credentials. Sequence: dry run → `--apply --limit 2` → the rest. | Production is outward-facing; secrets stay with the operator. |
| E7 | Tests (synthetic files only):<br>- order first, then the instructions link to it and become active;<br>- an order failure stops the run;<br>- matching by code, with unknown and ambiguous codes;<br>- the accepted statuses;<br>- the signed scan is attached;<br>- a re-run skips everything;<br>- `-m db`. | — |

## Prerequisites on production (operator)

1. PR #16 and this extension are merged and deployed; migrations up to `0016_document_file_role` are applied.
2. The document type catalog is seeded for the organization (`scripts/seed_document_types.py`): `order`, `iot_profession`, `iot_work_type`.
3. The workbook is imported (after fixing row 11, «Реестр» → «Карта / реестр»). The order and instruction places exist with «Тип в SafetyMAIN» = `order` / `iot_profession` / `iot_work_type`.
4. The actor holds `shelf:curate` and `compliance_document:create/update/approve/activate`. Today only the **admin** role has `shelf:curate`.

## Open questions

- **Q1.** Does the OHS specialist have the **admin** role in the organization? Answered: yes. If not, the run is refused: `shelf:curate` is admin-only until P11-009.
- **Q2.** Are the PDFs signed editions or unsigned copies? Answered: the signatures are images over the signature line (the text layer shows only the line), so the PDFs are the signed editions; E4 stands.
- **Q3.** The order also lists places whose files are not in the folder yet. Answered: later, the same way.
- **Q4.** In the workbook, does «Тип в SafetyMAIN» contain the codes `order` / `iot_profession` / `iot_work_type` for these places? If it contains other values, the dry run will show `no_document_type`, and the codes must be fixed in the workbook or in the shelf first.
