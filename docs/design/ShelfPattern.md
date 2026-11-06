# Shelf pattern («Полка»)

Screen `/shelf` (`frontend/src/features/document-shelf/`, TASK-P11-012 §4.2–§4.4).
Statuses, counts, readiness and actions come from the shelf API: the UI only displays them
(`docs/architecture/DocumentShelf.md`). Tokens: `docs/design/Tokens.md` («Document shelf»).

## Composition

1. **Header:** title, the line «N мест в K разделах · исключено M · реестр сверен с НПА
   [дата импорта]», filter chips (`aria-pressed`) and the excluded toggle.
2. **Summary:** readiness (percent + `progressbar`) and counts per group with the group
   swatch.
3. **Overview «Все разделы»:** one `<button aria-expanded>` row per section with number,
   title, a strip of thin bars (one per place, in code order, coloured by group), «N из M»
   and the percent. A click opens the shelf and selects its first place.
4. **Opened shelf:** number, title, «N из M в порядке · K обязательных · исключено X»,
   legend, then sub-shelves per subsection with spines and a plank.
5. **Spine (`<button>`):**
   - width by document kind, height by obligation (lookups in `utils/spine-geometry.ts`);
   - an excluded place is a 12 × 70 dashed ghost;
   - vertical `short_title`;
   - a bookmark ribbon above «В работе»;
   - an acknowledgement dot (phase 5);
   - a caret under the selected spine;
   - a 6 px lift on hover and focus (none with `prefers-reduced-motion`);
   - a tooltip on hover **and** keyboard focus (`role="tooltip"`, `aria-describedby`).
6. **Place panel** (`<aside>`, global tokens):
   - header: code, status badge (same swatch language as the spines), title, «подраздел · вид · обязательность»;
   - scan block: signed scan, else the working file labelled «Рабочий файл (без подписи)», shown by the shared `components/document-viewer/PdfViewer` (thumbnails, zoom, keyboard paging; «Открыть на весь экран», «Скачать»);
   - empty states, the exclusion details (reason, comment, who and when), the legal basis, review, edition, approval order and editions;
   - buttons only from `primary_action` / `available_actions`; «Исключить с полки» is a danger text button.

   Escape closes the panel and focus returns to the spine. At ≥ 1200 px the panel is the right column; on phones it is a full-screen sheet.
7. **Exclusion form** (in the panel, no modal): reasons, a required comment with the inline error «Напишите, почему место не нужно: это увидят при проверке.» (the backend `comment_too_short` shows the same text). A linked document adds a warning. After success, a `role="status"` line «Исключено N мест: …» offers «Отменить» (restore at the current versions).
8. **Bulk:** «Выбрать несколько» (curators) turns spines into toggles (excluded ones are disabled); the bar «Выбрано N мест · Исключить выбранные · Снять выбор» opens the same form. It sends the version of each place as the shelf showed it (`version` in the summary DTO), so a place changed meanwhile fails with 409 instead of being excluded; at most 200 places at once.
9. **Other actions:** «Разработать» (asks for a type when the place has none, then opens `/compliance-documents/{id}/edit`), «Загрузить скан» (develop, then upload a working file), «Загрузить подписанный скан» (the reused `ComplianceDocumentUploadDialog` with `target="signed_scan"`), «Привязать документ» (search over organization documents), «Применимо — нужен документ», «Вернуть на полку».
10. **Search:** a combobox over `GET /shelf/slots?q=` in the header; a choice opens its section and place.

## Filters

- «Проблемные» = groups «Нет», «Пересмотр», or an acknowledgement gap.
- «Обязательные» = mandatory and not excluded.

Places that do not match are dimmed (opacity 0.22), never removed. The overview strip has no
obligation level, so under «Обязательные» it dims only excluded bars.

## URL state

`?section=ТрБ&slot=ТрБ.02.02&filter=problems&excluded=hidden`. Opening a section or a place
pushes a history entry; filters and the toggle replace it. Invalid values fall back to the
defaults.

## Status without colour

Every group differs also by pattern: solid fill (Есть), solid fill with a ribbon (В работе),
fill with a border (Пересмотр), dashed outline (Нет), dotted outline (Уточнить), and a small
dashed ghost (Исключено). The status text is in the spine's accessible name and tooltip.

## Responsive

| Width | Layout |
|---|---|
| ≥ 1200 px | shelf and panel side by side |
| 768–1199 px | panel below the shelf |
| < 768 px | the overview drops the counts column; sub-shelves scroll horizontally |
