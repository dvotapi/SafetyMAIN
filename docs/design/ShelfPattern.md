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
6. **Place panel, exclusion, search:** PR 4c.

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
