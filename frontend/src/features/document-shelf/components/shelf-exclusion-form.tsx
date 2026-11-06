"use client";

import { useEffect, useId, useRef, useState } from "react";

import {
  Alert,
  Button,
  FieldError,
  Label,
  Radio,
  RadioGroup,
  Text,
  TextArea,
} from "@/components";

import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { SlotExclusionReason } from "@/features/document-shelf/types/shelf-dto";
import {
  EXCLUSION_COMMENT_MAX_LENGTH,
  EXCLUSION_COMMENT_MIN_LENGTH,
  EXCLUSION_REASONS,
} from "@/features/document-shelf/utils/shelf-actions";
import { pluralPlaces } from "@/features/document-shelf/utils/shelf-labels";
import { COMMENT_ERROR } from "@/features/document-shelf/utils/shelf-messages";

/**
 * In-panel exclusion form for one or several places (§4.3.7). The comment rule
 * is also enforced by the backend (`comment_too_short`); the same message is
 * shown for both.
 */
export function ShelfExclusionForm({
  codes,
  hasLinkedDocuments,
  defaultReason = "not_applicable",
  submitting,
  serverError,
  onSubmit,
  onCancel,
}: {
  codes: string[];
  hasLinkedDocuments: boolean;
  defaultReason?: SlotExclusionReason;
  submitting: boolean;
  serverError: string | null;
  onSubmit: (input: { reason: SlotExclusionReason; comment: string }) => void;
  onCancel: () => void;
}) {
  const id = useId();
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => headingRef.current?.focus(), []);
  const [reason, setReason] = useState<SlotExclusionReason>(defaultReason);
  const [comment, setComment] = useState("");
  const [touched, setTouched] = useState(false);
  const tooShort = comment.trim().length < EXCLUSION_COMMENT_MIN_LENGTH;
  const showError = (touched && tooShort) || serverError === COMMENT_ERROR;
  const many = codes.length > 1;
  const title = many
    ? `Исключить ${codes.length} ${pluralPlaces(codes.length)} с полки`
    : "Исключить место с полки";

  return (
    <form
      className={styles.panelBlock}
      aria-labelledby={`${id}-title`}
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        setTouched(true);
        if (tooShort) return;
        onSubmit({ reason, comment: comment.trim() });
      }}
    >
      <h3
        id={`${id}-title`}
        ref={headingRef}
        className={styles.panelHeading}
        tabIndex={-1}
      >
        {title}
      </h3>
      <Text as="p" className={styles.mono}>
        {codes.join(", ")}
      </Text>
      <Text as="p" tone="muted">
        Место останется на полке как исключённое, его можно вернуть.
      </Text>
      {hasLinkedDocuments ? (
        <Alert tone="warning" title="К месту привязан документ">
          Документ останется в разделе «Документы», ознакомление по нему
          продолжится.
        </Alert>
      ) : null}
      <fieldset className={styles.fieldset}>
        <legend>Причина</legend>
        <RadioGroup
          value={reason}
          onValueChange={(value) => setReason(value as SlotExclusionReason)}
          aria-label="Причина исключения"
        >
          {EXCLUSION_REASONS.map((item) => (
            <Radio
              key={item.value}
              id={`${id}-${item.value}`}
              value={item.value}
              label={item.label}
            />
          ))}
        </RadioGroup>
      </fieldset>
      <div className={styles.field}>
        <Label htmlFor={`${id}-comment`} required>
          Комментарий
        </Label>
        <TextArea
          id={`${id}-comment`}
          value={comment}
          maxLength={EXCLUSION_COMMENT_MAX_LENGTH}
          invalid={showError}
          aria-describedby={showError ? `${id}-error` : undefined}
          onChange={(event) => setComment(event.target.value)}
          onBlur={() => setTouched(true)}
          rows={3}
        />
        {showError ? (
          <FieldError id={`${id}-error`}>{COMMENT_ERROR}</FieldError>
        ) : null}
      </div>
      {serverError && serverError !== COMMENT_ERROR ? (
        <Alert tone="danger" title="Не удалось исключить">
          {serverError}
        </Alert>
      ) : null}
      <div className={styles.controls}>
        <Button
          type="submit"
          variant="danger"
          loading={submitting}
          disabled={submitting}
        >
          Исключить
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Отмена
        </Button>
      </div>
    </form>
  );
}
