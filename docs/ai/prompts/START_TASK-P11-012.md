# Задание для Claude Code: TASK-P11-012 «Полка документов»

Ты работаешь в репозитории SafetyMAIN. Реализуй задачу **TASK-P11-012 — Document Shelf («Полка»)** строго по процессу проекта: сначала план, потом код, по одной фазе за раз, с остановкой на ревью после каждой.

Со мной (Кат, владелец продукта) общайся по-русски. Код, комментарии, идентификаторы, коммиты и технические документы — на английском.

---

## 0. Прочитай перед любой работой

1. `CLAUDE.md`, `AI_CONTEXT.md`, `docs/ai/DevelopmentWorkflow.md`.
2. `docs/tasks/TASK-P11-012-document-shelf.md` — **главный контракт** (статус Approved, решения D1–D12, scope по фазам, критерии приёмки 1–14).
3. Поправки в соседних задачах, сделанные под эту задачу (раздел «Amendments from TASK-P11-012» в каждой):
   `EPIC-P11-compliance-documentation.md`, `TASK-P11-001` (раздел «Amendments after completion», A1–A6), `TASK-P11-004` §8, `TASK-P11-005` §9, `TASK-P11-006` §7, `TASK-P11-008` §6, `TASK-P11-009` §8, `TASK-P11-010`.
4. Ближайшая готовая реализация-образец: вертикальный срез `ComplianceDocument` из TASK-P11-001 (domain → application → SQLAlchemy → router → RBAC → audit → tests; фронтенд `features/compliance-documents`) и пример плана фазы `docs/superpowers/plans/2026-10-20-p11-001-phase-3-persistence.md`.
5. Только те архитектурные документы, которые нужны текущей фазе: `docs/architecture/ADR-0006-Document-and-Evidence-Storage.md`, `ComplianceDocumentPersistence.md`, `AuditTaxonomy.md`, `AuthorizationFoundation.md`, `docs/design/RegistryPattern.md`, `Tokens.md`, `Accessibility.md`, `FrontendArchitecture.md`.

Порядок авторитетности при противоречиях: TASK-P11-012 → утверждённый план фазы → `docs/architecture/*` → существующий код → тесты. Не угадывай: если источники расходятся — остановись и спроси меня.

Два значения слова «фаза», не путай:
- **этапы процесса** из `DevelopmentWorkflow.md` (планирование, ревью плана, реализация, самопроверка);
- **фазы реализации задачи** 1–5 из раздела «Suggested implementation phases» в TASK-P11-012.

---

## 1. Ветка и git (один раз, до планирования)

- Сейчас в рабочем дереве на ветке `docs/p11-002-plan-and-pilot` лежат **незакоммиченные** документы этой задачи: новый `docs/tasks/TASK-P11-012-document-shelf.md`, изменённые EPIC и TASK-P11-001/004/005/006/008/009/010, и этот файл `docs/ai/prompts/START_TASK-P11-012.md`. Коммиты ветки `docs/p11-002-plan-and-pilot` их не затрагивают.
- `git fetch`, убедись, что `main` = `origin/main`. Создай от `main` ветку `docs/p11-012-document-shelf` (незакоммиченные изменения перейдут с тобой), закоммить **только эти файлы явными путями**: `docs(tasks): add TASK-P11-012 document shelf and amend dependent P11 tasks`. Открой PR в `main` и дождись моего мержа, прежде чем начинать код.
- Никогда не добавляй в коммит `.claude/`, `docs/superpowers/` (кроме своих новых планов), `.claude/launch.json`. Не пушь в `main` напрямую. Пуш веток и PR — да.
- Каждую фазу реализации делай в своей ветке от свежего `main`: `claude/p11-012-phase-<N>-<slug>`. Одна фаза = один PR.
- Перед любыми изменениями — `git pull` / `git fetch` (правило `CLAUDE.md`). Конфликты или разошедшаяся история — стоп, спроси меня.

---

## 2. Цикл для каждой фазы реализации

Для каждой фазы N (начиная с 1):

1. **План (без кода).** Изучи только нужные файлы. Сохрани план в `docs/superpowers/plans/<YYYY-MM-DD>-p11-012-phase-<N>-<slug>.md` в формате образца P11-001 phase 3: Goal, Architecture, Global Constraints, таблица «Decisions taken in this plan» (P1, P2…), Affected files, шаги с чекбоксами, Verification, Risks, Open questions. Покажи мне краткое резюме плана по-русски и **жди слова «утверждаю»**.
2. **Реализация** только утверждённого объёма. Никаких заделов на будущие фазы, никаких попутных рефакторингов.
3. **Проверка** (обязательно перед PR):
   - backend: `python -m ruff check .`, `python -m pytest`, и при изменении БД — `SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db` против локального Postgres из `docker compose up -d`;
   - frontend (если менялся): `cd frontend && npm run verify`;
   - миграции: `alembic upgrade head` и `downgrade -1` на локальной БД.
4. **Самопроверка** по чек-листу Phase 5 из `DevelopmentWorkflow.md` (нет посторонних изменений, нет TODO/FIXME, соответствие плану). Обнови `CLAUDE.md` / `AI_CONTEXT.md`, если фаза меняет команды, структуру или конвенции.
5. **PR** с описанием: что сделано, какие критерии приёмки TASK закрыты (номера), как проверено, что осталось. Остановись и жди ревью.

После мержа PR — следующая фаза с шага 1.

---

## 3. Фазы и что в них важно

### Фаза 1 — Transport security (≈ 0.5–1 дня), TASK §1
Замена `SafetyDomain.LABOUR = "labour"` на `TRANSPORT_SECURITY = "transport_security"`, миграция `0014_transport_security_domain` (UPDATE + пересоздание `ck_document_types_safety_domain`, downgrade обратно). Список файлов — в §1.3; **не забудь `tests/domain/test_document_type.py`**. Подпись «Транспортная безопасность». Не трогай `SafetyDirection.TRANSPORT_SAFETY` в Hazard — это осознанно разные коды (§1, п. 6). Критерий приёмки 1.

### Фаза 2 — Домен, статус, БД, права, аудит, API (≈ 4–5 дней), TASK §2
- Агрегаты `ShelfSection` (+ подразделы) и `ShelfSlot`, VO `ShelfSlotCode` (`^[А-ЯЁа-яё]+\.\d{2}\.\d{2}$`, есть смешанный регистр `ПожБ`), исключение `SlotExclusion` (комментарий ≥ 5 символов), методы `exclude / restore / confirm_applicable / link_document / unlink_document`.
- `ShelfStatusEvaluator` — правила §2.2 по порядку, `today` = UTC-дата из `ClockContract.now()`; `available_actions` и `primary_action` считает бэкенд. Задокументируй расхождение с P11-001 D11 (fallback на `review_period_months` места).
- Миграция `0015_document_shelf` (§2.3). Никаких физических DELETE и **никаких DELETE-эндпоинтов**: отвязка — `POST …/documents/{document_id}/unlink`.
- `POST /shelf/slots/{id}/develop` создаёт черновик `ComplianceDocument` через существующий обработчик создания и привязывает его в одной единице работы.
- Права `shelf:read` (admin, member, auditor), `shelf:curate` (только admin до P11-009). Межорганизационный доступ → 404.
- Аудит: имена должны проходить `^[a-z]+\.[a-z]+\.[a-z]+$` (`backend/core/domain/security_events/naming.py`) — `compliance.place.*`, `compliance.section.*`, `compliance.shelf.imported`. `_compliance_descriptor` сейчас жёстко ставит `COMPLIANCE_DOCUMENT` — добавь параметр `subject_domain`, новые `SecurityEventSubjectDomain`, `AuditResourceType`, `AuditAction`.
- Документация: `docs/api/ShelfAPI.md`, `docs/architecture/DocumentShelf.md`, `AuditTaxonomy.md`, `UbiquitousLanguage.md`.
- Критерии 2–5. Эту фазу разумно разбить на 2–3 PR (домен+персистенция → приложение+API+RBAC+аудит) — предложи разбиение в плане.

### Фаза 3 — Импорт xlsx (≈ 2 дня), TASK §3
- `scripts/import_shelf_workbook.py` через обработчики приложения; `openpyxl` в новый extra `import` и в `dev`.
- Маппинг по **именам заголовков** (таблица §3.2), строгая проверка словарей, вариант «Обязательна», `labour` → `transport_security`, «Не применимо» → исключение. Отпечаток строки и правила конфликтов §3.4. Генерация коротких названий §3.3.
- Тесты — только на **синтетической** книге, созданной в тесте. Настоящий файл лежит у меня: `/Users/apple/Yandex.Disk.localized/001 ComplEX/009 ПБ, ОТ, ТрБез/Полка документов ОТ и ПБ.xlsx` — **никогда не копируй его в репозиторий**. Прогон `--dry-run` на нём покажи мне в PR (ожидается: 416 мест, 13 разделов, 92 подраздела, 3 исключённых, 0 отклонённых строк).
- Гайд куратора `docs/guides/ShelfImport.md` (папку `docs/guides/` создать). Критерии 6–7.

### Фаза 4 — Подписанные сканы и экран «Полка» (≈ 6–8 дней), TASK §4 и §6
Разбей минимум на 3 PR: (а) бэкенд сканов, (б) фронтенд: обзор, полка и корешки, (в) панель места, исключения, поиск.
- Бэкенд сканов (A2–A4 в P11-001): `DocumentFile.role` (`working | signed_scan`), миграция `0016_document_file_role`; `current_file` = последний **рабочий** файл (approve/activate не должны ломаться от скана), `current_signed_scan`, эндпоинты `signed-scan/upload-url|confirm`, `signed-scan/current/download-url`, `files/{file_id}/view-url` (inline). CORS уже разрешает GET — проверь inline-рендер и range-запросы pdf.js на MinIO, при необходимости обнови runbook. Поправка в ADR-0006.
- Фронтенд: маршрут `/shelf`, пункт «Полка» в группе «Соответствие», фича `features/document-shelf`, общий `components/document-viewer/PdfViewer` (`pdfjs-dist`, ленивая загрузка). Состояние в URL. Диалог загрузки переиспользуй через экспорт `ComplianceDocumentUploadDialog` из `features/compliance-documents/index.ts` — не лезь во внутренности чужой фичи (dependency-cruiser).
- Визуальный язык — строго §4.3–§4.4 и токены §6: новые примитивы палитры (`paper`, `graphite`, `forest`, `ochre`, `brick`) в `primitive.palette`, семантические `shelf-*` ссылаются на них; никаких hex в компонентах. Фон «тёплая бумага» только у области полки. Закладка-ленточка у «В работе» обязательна (зелёный и графит одинаковы по яркости). Статус никогда не только цветом.
- Фронтенд ничего не считает: статусы, готовность, счётчики, доступные действия — только из API.
- Макет-эталон: холст «Полка — SafetyMAIN» у меня в claude.ai (ссылка в шапке TASK; тебе он недоступен — ориентируйся на текст §4.3, все размеры и тексты там).
- Опциональный `scripts/attach_shelf_scans.py` (§4.5) — отдельным PR, только после моего «да».
- Критерии 8–13.

### Фаза 5 — Ознакомление (≈ 2–3 дня), TASK §5
**Не начинай**, пока не готовы TASK-P11-004 (с §8), срез журнала ознакомления TASK-P11-005 §9 и срез `acknowledge_document` TASK-P11-006 §7. Когда до неё дойдём — проверь, что эндпоинты `acknowledgement-coverage` и `acknowledgements` существуют, и только тогда планируй. Полка только отображает их данные. Критерий 14.

---

## 4. Когда остановиться и спросить меня

- TASK и код расходятся, или решение не покрыто TASK.
- Нужно изменить что-то за пределами фазы (другую фичу, общие компоненты, существующие миграции, P11-001 сверх A1–A6).
- Тесты падают по причинам, не связанным с твоими изменениями.
- Любая операция, которую нельзя откатить (удаление файлов, force-push, изменения в `main`).
- Нужен доступ к реальной книге-полке или к хранилищу Yandex.

## 5. Первое действие сейчас

Выполни раздел 1 (ветка `docs/p11-012-document-shelf`, коммит документов, PR). Затем подготовь **план фазы 1** по разделу 2 и пришли мне резюме. Код не пиши до моего «утверждаю».
