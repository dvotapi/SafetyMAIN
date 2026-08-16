# Russian UI Copy

Status: Active  
Date: 2026-08-16  
Task: [TASK-P10-001](../tasks/TASK-P10-001-frontend-localization-ru.md)

This document is the locked English-to-Russian glossary for frontend copy.
Backend wire values, identifiers, permission names, and audit event names stay
unchanged.

## Navigation and aggregates

| English                      | Russian                                         |
| ---------------------------- | ----------------------------------------------- |
| Overview                     | Обзор                                           |
| Safety                       | Безопасность                                    |
| Hazards / Hazard             | Опасности / Опасность                           |
| Risk / Risk Assessment       | Риск / Оценка риска                             |
| Risk Controls / Risk Control | Меры управления риском / Мера управления риском |
| People                       | Персонал                                        |
| Knowledge                    | Знания                                          |
| Analytics                    | Аналитика                                       |
| Administration               | Администрирование                               |
| Organization                 | Организация                                     |
| Incident                     | Инцидент                                        |
| Inspection                   | Проверка                                        |
| Corrective Action            | Корректирующее действие                         |
| Training                     | Обучение                                        |
| Permit                       | Наряд-допуск                                    |
| Emergency Asset              | Аварийный ресурс                                |
| Audit Event                  | Событие аудита                                  |

## Shared statuses

| Wire value                     | English                      | Russian                           |
| ------------------------------ | ---------------------------- | --------------------------------- |
| `draft`                        | Draft                        | Черновик                          |
| `under_review`                 | Under Review                 | На рассмотрении                   |
| `approved`                     | Approved                     | Утверждено                        |
| `rejected`                     | Rejected                     | Отклонено                         |
| `planned`                      | Planned                      | Запланировано                     |
| `active`                       | Active                       | Действует                         |
| `in_implementation`            | In Implementation            | Внедряется                        |
| `implemented`                  | Implemented                  | Внедрено                          |
| `verified_effective`           | Verified Effective           | Подтверждена эффективной          |
| `verified_partially_effective` | Verified Partially Effective | Подтверждена частично эффективной |
| `verified_ineffective`         | Verified Ineffective         | Подтверждена неэффективной        |
| `overdue`                      | Overdue                      | Просрочено                        |
| `suspended`                    | Suspended                    | Приостановлено                    |
| `superseded`                   | Superseded                   | Замещено                          |
| `archived`                     | Archived                     | Архив                             |
| `cancelled`                    | Cancelled                    | Отменено                          |

Status badges use these invariant forms across aggregates. Do not apply
aggregate-specific grammatical gender.

## Hazard classification

### Category

`physical` Физическая; `mechanical` Механическая; `electrical`
Электрическая; `chemical` Химическая; `biological` Биологическая;
`ergonomic` Эргономическая; `psychosocial` Психосоциальная;
`fire_and_explosion` Пожар и взрыв; `thermal` Тепловая; `radiation`
Радиационная; `pressure` Давление; `work_at_height` Работа на высоте;
`confined_space` Замкнутое пространство; `transport` Транспортная;
`environmental` Экологическая; `dangerous_goods` Опасные грузы;
`process_safety` Безопасность процессов; `natural_hazard` Природная
опасность; `organizational` Организационная; `other` Иная.

### Safety direction

`occupational_safety` Охрана труда; `industrial_safety` Промышленная
безопасность; `fire_safety` Пожарная безопасность; `environmental_safety`
Экологическая безопасность; `transport_safety` Транспортная безопасность;
`dangerous_goods_transport` Перевозка опасных грузов;
`civil_defense_and_emergency` ГО и ЧС; `sanitary_and_hygienic_safety`
Санитарно-гигиеническая безопасность; `electrical_safety`
Электробезопасность; `radiation_safety` Радиационная безопасность.

### Source and affected subject

`employee_report` Сообщение работника; `inspection` Проверка;
`incident_investigation` Расследование инцидента; `near_miss` Опасное
событие без последствий; `risk_assessment` Оценка риска;
`regulatory_assessment` Регуляторная оценка; `audit` Аудит;
`management_review` Анализ со стороны руководства; `change_management`
Управление изменениями; `equipment_documentation` Документация на
оборудование; `sout` СОУТ; `production_control` Производственный контроль;
`environmental_monitoring` Экологический мониторинг; `transport_control`
Транспортный контроль; `other` Иной.

`employee` Работник; `contractor` Подрядчик; `visitor` Посетитель; `driver`
Водитель; `passenger` Пассажир; `public` Третьи лица; `environment`
Окружающая среда; `equipment` Оборудование; `building` Здание;
`transport_vehicle` Транспортное средство; `cargo` Груз;
`production_process` Производственный процесс.

## Risk assessment

Risk levels: `low` Низкий; `medium` Средний; `high` Высокий; `extreme`
Крайний.

Hierarchy of Controls: `elimination` Устранение; `substitution` Замена;
`engineering` Инженерные меры; `administrative` Административные меры;
`ppe` СИЗ.

Profile titles: `simple_3x3` Простая матрица 3×3; `simple_5x5` Простая
матрица 5×5; `corporate_custom` Корпоративная; `russian_occupational_risk`
Профессиональный риск (РФ); `industrial_safety` Промышленная безопасность;
`fire_safety` Пожарная безопасность; `environmental_risk` Экологический
риск; `transport_risk` Транспортный риск; `adr_risk` Риск ДОПОГ (ADR).

Object types: `workplace` Рабочее место; `job_position` Должность;
`work_activity` Вид работ; `equipment` Оборудование; `vehicle` Транспортное
средство; `production_process` Производственный процесс; `location` Место;
`contractor_activity` Деятельность подрядчика; `chemical` Химическое
вещество; `emergency_scenario` Аварийный сценарий.

Acceptance: `accepted` Принят; `conditionally_accepted` Принят условно;
`not_accepted` Не принят; `requires_escalation` Требует эскалации.

Factors: `probability` Вероятность; `severity` Тяжесть; `exposure`
Экспозиция; `frequency` Частота; `detectability` Обнаружимость;
`environmental_impact` Экологическое воздействие; `fire_consequence`
Последствия пожара; `business_impact` Влияние на бизнес.

## Risk control

Effectiveness: `effective` Подтверждена эффективной; `partially_effective`
Подтверждена частично эффективной; `ineffective` Подтверждена
неэффективной; `not_verified` Не подтверждена; `not_applicable` Не
применяется.

Control nature: `preventive` Предупреждающая; `detective` Выявляющая;
`mitigating` Снижающая; `recovery` Восстановительная.

Evidence type: `document` Документ; `photo` Фото; `video` Видео;
`inspection_record` Запись проверки; `test_result` Результат испытания;
`work_order` Наряд-заказ; `training_record` Запись обучения; `certificate`
Сертификат; `measurement` Измерение; `approval` Согласование; `other` Иное.

Verification type: `initial` Первичная; `scheduled_review` Плановый
пересмотр; `post_incident` После инцидента; `post_inspection` После
проверки; `post_change` После изменения; `management_review` Анализ
руководства; `other` Иная.

Review basis: `fixed_interval` Фиксированный интервал; `risk_based` На
основе риска; `regulatory_requirement` Требование НПА;
`manufacturer_requirement` Требование изготовителя; `corporate_policy`
Корпоративная политика; `post_incident` После инцидента; `post_change`
После изменения; `manual` Вручную.

Owner type: `user` Пользователь; `employee` Работник; `role` Роль;
`organizational_unit` Подразделение; `external_party` Внешняя сторона.

Milestone status: `pending` Ожидает; `in_progress` В работе; `completed`
Выполнено; `blocked` Заблокировано; `cancelled` Отменено.

## Actions and generic UI

| English                                                 | Russian                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| Activate / Archive / Restore hazard                     | Активировать / Архивировать / Восстановить опасность                   |
| Submit for review                                       | Отправить на рассмотрение                                              |
| Approve / Archive assessment                            | Утвердить / Архивировать оценку                                        |
| Assign owner                                            | Назначить владельца                                                    |
| Plan / Start / Complete implementation                  | Спланировать / Начать / Завершить внедрение                            |
| Update progress                                         | Обновить прогресс                                                      |
| Add evidence                                            | Добавить доказательство                                                |
| Verify effectiveness                                    | Подтвердить эффективность                                              |
| Schedule / Complete review                              | Назначить / Завершить пересмотр                                        |
| Suspend / Resume / Supersede / Cancel / Archive control | Приостановить / Возобновить / Заместить / Отменить / Архивировать меру |
| Materialize controls                                    | Создать меры                                                           |
| Save / Cancel / Confirm / Close                         | Сохранить / Отмена / Подтвердить / Закрыть                             |
| Create / Edit / Delete                                  | Создать / Изменить / Удалить                                           |
| Search / Filters / Clear all                            | Поиск / Фильтры / Сбросить все                                         |
| Loading / No records found                              | Загрузка / Нет записей                                                 |
| Previous / Next                                         | Назад / Далее                                                          |
| Sign in / Sign out                                      | Войти / Выйти                                                          |

Counts use `formatPluralRu()` when a count is followed by a Russian noun.
Selection counters use the invariant form `Выбрано: N`.

## Generic errors

| English                                                   | Russian                                               |
| --------------------------------------------------------- | ----------------------------------------------------- |
| Network error. Check your connection and try again.       | Нет сети. Проверьте подключение и повторите попытку.  |
| Authentication required.                                  | Требуется вход.                                       |
| You do not have permission to perform this action.        | Недостаточно прав для этого действия.                 |
| The requested resource was not found.                     | Запрашиваемый объект не найден.                       |
| This record was updated elsewhere. Refresh and try again. | Запись изменена в другом месте. Обновите и повторите. |
| Organization context mismatch.                            | Несовпадение контекста организации.                   |
| Please correct the highlighted fields.                    | Исправьте выделенные поля.                            |
| Something went wrong. Try again later.                    | Что-то пошло не так. Повторите позже.                 |

Backend-authored free-text validation messages are not translated by the
frontend and may remain English.
