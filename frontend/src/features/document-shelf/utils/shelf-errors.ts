/** Russian messages for shelf error codes (docs/api/ShelfAPI.md). */
import { ApiClientError, toUserSafeMessage } from "@/services/api/errors";

import { COMMENT_ERROR } from "@/features/document-shelf/utils/shelf-messages";

const MESSAGES: Record<string, string> = {
  comment_too_short: COMMENT_ERROR,
  already_excluded: "Место уже исключено с полки.",
  not_excluded: "Место не исключено.",
  not_to_clarify: "Применимость уже подтверждена.",
  document_subject_not_supported:
    "К месту можно привязать только документ организации.",
  document_type_required: "Выберите тип документа.",
  document_type_not_found: "Тип документа не найден в каталоге.",
  already_linked_active_document:
    "У места уже есть действующий документ или проект.",
  shelf_slot_version_conflict:
    "Место изменили в другом окне. Обновите и повторите.",
  compliance_document_not_found: "Документ не найден.",
};

export function shelfErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError && error.code && MESSAGES[error.code]) {
    return MESSAGES[error.code]!;
  }
  return toUserSafeMessage(error);
}
