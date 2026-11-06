# Importing the shelf workbook

Guide for the curator and the operator who loads «Полка документов» (the `.xlsx` register
of required documents) into SafetyMAIN. Rules behind it: TASK-P11-012 §3 and
`docs/architecture/DocumentShelf.md`.

The workbook is internal data. Keep it outside the repository and never attach it to an
issue or a pull request.

## Who runs it

- **Operator:** a person with access to the backend environment (`DATABASE_URL`). The
  operator runs the command.
- **Actor:** a curator, i.e. an active user who holds `shelf:curate` in the organization
  (today: an administrator). Every change is audited in the actor's name.

## 1. Prepare the workbook

- The sheet must be named «Полка». The header row may be anywhere in the first 10 rows,
  and columns may be in any order: they are found by header name.
- Required headers: Код, Раздел, Подраздел, Документ (место на полке), Вид, Ведётся на,
  Обязательность, Статус, Домен SafetyMAIN.
- Optional headers: Условие применимости, Основание (НПА), Пункт / статья, Выдержка из
  НПА, Ссылка на текст, Достоверность основания, Цикл / периодичность, Период, мес, Тип в
  SafetyMAIN, Где лежит сейчас, Ответственный, Примечание, Код в версии 1, Пакет /
  категория.
- Ignored on purpose: dates (Дата утверждения / выдачи, Следующий пересмотр, Дней до
  пересмотра). Dates belong to documents, not to places. The report lists every ignored
  column.

Allowed values (case, «ё» and spacing around «/» and dashes do not matter):

| Column | Values |
|---|---|
| Код | `SECTION.SS.NN`, e.g. `ТрБ.02.02`; unique in the workbook |
| Раздел | `NN Title`, e.g. «10 Транспортная безопасность»; the same for every row of a section |
| Подраздел | title; the same for every row of a subsection |
| Вид | Политика, Положение, Порядок / процедура, Приказ, Инструкция, Программа, План, Журнал, Перечень, Протокол, Акт, Проект / паспорт, Карта / реестр, Удостоверение / свидетельство, Договор / полис, Отчёт, Разрешение / лицензия |
| Ведётся на | Организация, ОПО / объект, Событие, Работник, ТС / техника, Профессия / вид работ |
| Обязательность | Обязателен (or Обязательна), При условии (needs «Условие применимости»), Рекомендуется |
| Статус | Есть, Есть — нужен пересмотр, В работе (проект), Нет, Уточнить, Не применимо |
| Достоверность основания | «сверено по тексту…», «вторичный источник», «не подтверждено», «—». Any other text is kept in «Примечание» as `Достоверность: …` |
| Домен SafetyMAIN | `occupational`, `industrial`, `transport_security` (the old `labour` is accepted and converted), `fire`, `environmental`, `road`, `dangerous_goods`; the same for every row of a section |
| Тип в SafetyMAIN | the code of an active document type: the place gets this type. Any other text («(новый)», «журнал (P11-005)») is kept as the proposed type |
| Период, мес | a whole number ≥ 1, or empty |
| Ссылка на текст | an absolute `http`/`https` link, or empty |

An unknown value is never guessed. The row is rejected, and the report names the row, the
column and the value.

## 2. Dry run first

```bash
python -m pip install -e ".[import]"
```

```bash
DATABASE_URL=… python -m scripts.import_shelf_workbook --organization-id <uuid> --file "Полка документов.xlsx" --actor-email curator@example.com --dry-run --report report.json
```

A dry run writes nothing and records nothing. It prints the same report as a real run.
`--report` also saves the report as JSON.

## 3. Read the report

```
Shelf import: DRY RUN — nothing written
  workbook: 416 places, 13 sections, 92 subsections, 3 excluded
  created 416, updated 0, unchanged 0, conflicts 0, rejected 0, missing in workbook 0
  sections created 13, renamed 0; subsections created 92, renamed 0
```

| Line | Meaning |
|---|---|
| created | new places |
| updated | the workbook row changed and nobody edited the place in SafetyMAIN; the row is applied |
| unchanged | the row is the same as at the last import. Edits made in SafetyMAIN are kept |
| conflicts | the row changed **and** the place was edited in SafetyMAIN; not applied, see §4 |
| rejected | invalid rows; while there is any, a real run writes **nothing** (exit code 1) |
| missing in workbook | places in SafetyMAIN that the workbook no longer has; they are left as they are and are **never** excluded or removed by the import |

Exit codes: 0 done, 1 rejected rows, 2 the run was refused. A run is refused for an
unknown or inactive user, a user who may not curate, an unknown organization, or a file
that cannot be read (not `.xlsx`, over 20 MB, no sheet «Полка», a missing required
header).

## 4. Resolve conflicts

SafetyMAIN is the source of truth once the shelf is imported (D3). A place counts as edited
in SafetyMAIN when any field the workbook sets was changed there, including its status or
exclusion. Linking a document does not count. The conflict lists each differing field with
the workbook value and the SafetyMAIN value.

To resolve a conflict, either:

- make the workbook row equal to SafetyMAIN: the place becomes `unchanged` again; or
- apply the workbook value in SafetyMAIN by hand: the panel edit is audited as usual.

## 5. Real run

Run the same command without `--dry-run`. It writes all changes in one transaction:

- sections and subsections are created or renamed;
- places are created or updated;
- «Не применимо» places are excluded with the reason «not applicable» and the comment
  «Статус «Не применимо» из реестра-полки». Restoring one gives status «Уточнить».

It records one `compliance.shelf.imported` event with the counts and the file SHA-256,
plus the usual `compliance.place.*` and `compliance.section.*` events. Running it again
with the same file reports every place as `unchanged`.

A section number or domain that differs from the stored one is rejected: the number fixes
the shelf order. Changing either is a separate task.

## 6. Review short titles

The spine label (`short_title`, at most 40 characters) is generated from the title:

- parenthesised fragments are dropped;
- standard abbreviations are applied (охрана труда → ОТ, инструкция по охране труда → ИОТ,
  пожарной безопасности → ПожБ, «Приказ о назначении» → «Назначение», …);
- long titles are cut at a word with «…».

Automatic shortening is often clumsy, so review the labels section by section in the
shelf and fix them in the place panel. A fixed label counts as a SafetyMAIN edit. If the
workbook row of that place changes later, it is reported as a conflict instead of being
overwritten.

When the abbreviation list in the code changes, generated labels change too. The next
import then reports every affected untouched place as `updated`, and every edited one as a
conflict.

## Production

The backend image does not include the `import` extra. Run the import from a machine that
has the repository with `pip install -e ".[import]"` and the production `DATABASE_URL` (the
database lives on a separate server), or install the extra into a one-off container.

## 7. Attaching scans (optional)

`scripts/attach_shelf_scans.py` fills places marked «Есть» that have no document in
SafetyMAIN with the scans you already have. A place is taken when all of these hold:

- the curated status is «Есть», it is not excluded and has no linked document;
- it names an active document type («Тип в SafetyMAIN») that does not require an approval
  order;
- «Где лежит сейчас» (relative to `--root`) points at a PDF file, or at a folder that holds
  exactly one PDF.

For each such place the script creates a draft (code and title from the place), sets the
effective date, uploads the PDF as the working file, approves and activates it, and links
it to the place. All steps are audited in the curator's name. Source files are only read.

```bash
DATABASE_URL=… python -m scripts.attach_shelf_scans --organization-id <uuid> --root "/path/to/scans" --actor-email curator@example.com --report scans.json
```

That is a dry run: it lists the places it would attach and why the others are skipped.
To write, add `--apply --effective-from YYYY-MM-DD` (the same date for every attached
document, e.g. the date the scans were checked). Try `--limit 5` first.

The actor needs `shelf:curate` and `compliance_document:create`, `update`, `approve`,
`activate`. The storage settings (`STORAGE_*`) must point at the real bucket, because the
file goes to storage through a presigned upload, exactly as in the browser.

Skip reasons:

| Reason | Meaning |
|---|---|
| `not_present` | the curated status is not «Есть» |
| `excluded` | the place is excluded |
| `has_document` | a document is already linked |
| `no_document_type` | the place names no document type |
| `type_not_found` | the type is not in the active catalog |
| `type_requires_approval_order` | the type requires an approval order; finish the place in the shelf |
| `no_location` | «Где лежит сейчас» is empty |
| `file_not_found` | there is no such file, or the folder has no PDF |
| `ambiguous` | the folder has several PDFs |
| `not_pdf` | the file is not a PDF |
| `outside_root` | the path leaves `--root` |
| `too_large` | the file is larger than the upload limit |

If a step fails, the script reports the step and continues with the next place. The failed
place keeps its linked draft (or approved) document; nothing is deleted. A re-run skips it
(`has_document`); finish it in the shelf with «Открыть проект».

### Signed editions approved by one order

The scans may be named by place code (`ТрБ.01.02 ИОТ для водителя.pdf`) and approved by
one order that is itself a place (`ТрБ.01.01 Приказ о введении инструкций.pdf`). In that
case use `--match-by-code` and `--approval-order`:

```bash
python -m scripts.attach_shelf_scans --organization-id <uuid> --root "<folder>" --actor-email <admin> --match-by-code --approval-order ТрБ.01.01 --order-note "№ … от …" --report signed.json
```

- Every `*.pdf` directly in the folder whose name starts with a place code is that place's
  file; «Где лежит сейчас» is ignored.
- The order goes first: it is created, uploaded, approved and put in force. If that fails,
  nothing else is touched. On a later run an order already in force on its place is
  reused.
- Every document of a type that requires an approval order is linked to the order, then
  approved and put in force.
- Places with «Есть», «В работе (проект)» or «Есть — нужен пересмотр» are taken.
- Each PDF is stored as the working file and, after approval, as the signed scan, so the
  shelf shows «Скан подписанной редакции». Pass `--no-signed-scan` to skip the second copy.
- The place type («Тип в SafetyMAIN») must be `order` for the order and an active type
  (e.g. `iot_profession`, `iot_work_type`) for the others.

More skip reasons in this mode:

| Reason | Meaning |
|---|---|
| `unknown_code` | there is no place with that code |
| `no_code_in_name` | the file name does not start with a place code |
| `ambiguous` | several files for one code |
| `order_type_mismatch` | the order's place type is not `order` |
| `order_file_not_found` | there is no file of the order in the folder |
| `order_not_in_force` | no order is in force, so documents that need one are skipped |
| `order_failed` | putting the order in force failed in this run |

Add `--apply --effective-from YYYY-MM-DD` to write; try `--limit 2` first (the limit
applies to the documents after the order).
