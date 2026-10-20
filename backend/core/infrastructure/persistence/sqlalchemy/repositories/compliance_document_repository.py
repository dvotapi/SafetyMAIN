from __future__ import annotations

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.compliance_document import (
    ComplianceDocument,
    is_in_force,
)
from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentNotFound,
    ComplianceDocumentVersionConflict,
    DuplicateActiveComplianceDocumentCode,
)
from backend.core.domain.repositories.compliance_document_repository import (
    ComplianceDocumentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_document_query import (
    ComplianceDocumentPage,
    ComplianceDocumentQuery,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.compliance_document_mapper import (
    files_to_models,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.compliance_document_model import (
    ComplianceDocumentModel,
    DocumentFileModel,
)


class SQLAlchemyComplianceDocumentRepository(ComplianceDocumentRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    # ---- helpers ----

    def _load_files(
        self, document_ids: list[ComplianceDocumentId]
    ) -> dict[ComplianceDocumentId, list[DocumentFileModel]]:
        if not document_ids:
            return {}
        raw = {d.value for d in document_ids}
        rows = self._session.scalars(
            select(DocumentFileModel)
            .where(DocumentFileModel.document_id.in_(raw))
            .order_by(DocumentFileModel.document_id, DocumentFileModel.position)
        ).all()
        grouped: dict[ComplianceDocumentId, list[DocumentFileModel]] = {}
        for row in rows:
            key = ComplianceDocumentId(value=row.document_id)
            grouped.setdefault(key, []).append(row)
        return grouped

    def _hydrate(
        self, model: ComplianceDocumentModel
    ) -> ComplianceDocument:
        files = self._session.scalars(
            select(DocumentFileModel)
            .where(DocumentFileModel.document_id == model.id)
            .order_by(DocumentFileModel.position)
        ).all()
        return to_domain(model, files)

    # ---- contract ----

    def _assert_code_free_in_force(self, document: ComplianceDocument) -> None:
        if not is_in_force(document.status):
            return
        in_force_values = (
            ComplianceDocumentStatus.ACTIVE.value,
            ComplianceDocumentStatus.UNDER_REVIEW.value,
        )
        conflict = self._session.scalar(
            select(ComplianceDocumentModel.id).where(
                ComplianceDocumentModel.organization_id
                == document.organization_id.value,
                ComplianceDocumentModel.code == document.code,
                ComplianceDocumentModel.status.in_(in_force_values),
                ComplianceDocumentModel.id != document.id.value,
            )
        )
        if conflict is not None:
            raise DuplicateActiveComplianceDocumentCode(
                organization_id=document.organization_id,
                code=document.code,
            )

    def add(self, document: ComplianceDocument) -> None:
        self._assert_code_free_in_force(document)
        self._session.add(to_model(document))
        for file_model in files_to_models(document):
            self._session.add(file_model)
        try:
            self._session.flush()
        except IntegrityError as error:
            if "uq_compliance_documents_org_code_in_force" in str(error.orig):
                raise DuplicateActiveComplianceDocumentCode(
                    organization_id=document.organization_id,
                    code=document.code,
                ) from error
            raise

    def get(
        self,
        organization_id: OrganizationId,
        document_id: ComplianceDocumentId,
    ) -> ComplianceDocument | None:
        model = self._session.scalar(
            select(ComplianceDocumentModel).where(
                ComplianceDocumentModel.id == document_id.value,
                ComplianceDocumentModel.organization_id == organization_id.value,
            )
        )
        return None if model is None else self._hydrate(model)

    def list(self, query: ComplianceDocumentQuery) -> ComplianceDocumentPage:
        filters: list[object] = [
            ComplianceDocumentModel.organization_id == query.organization_id.value
        ]
        if not query.include_archived:
            filters.append(
                ComplianceDocumentModel.status != ComplianceDocumentStatus.ARCHIVED.value
            )
        if query.document_type_ids is not None:
            if not query.document_type_ids:
                return ComplianceDocumentPage(
                    items=(), total=0, offset=query.offset, limit=query.limit
                )
            filters.append(
                ComplianceDocumentModel.document_type_id.in_(
                    {t.value for t in query.document_type_ids}
                )
            )
        if query.status is not None:
            filters.append(ComplianceDocumentModel.status == query.status.value)
        if query.subject_kind is not None:
            filters.append(
                ComplianceDocumentModel.subject_kind == query.subject_kind.value
            )
        if query.search is not None and query.search.strip():
            needle = query.search.strip()
            pattern = (
                "%"
                + needle.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
                + "%"
            )
            filters.append(
                or_(
                    ComplianceDocumentModel.code.ilike(pattern, escape="\\"),
                    ComplianceDocumentModel.title.ilike(pattern, escape="\\"),
                )
            )
        where_clause = and_(*filters)

        if query.review_due is not None:
            review_due = query.review_due
            models = self._session.scalars(
                select(ComplianceDocumentModel)
                .where(where_clause)
                .order_by(
                    ComplianceDocumentModel.created_at.desc(),
                    ComplianceDocumentModel.id.desc(),
                )
            ).all()
            file_groups = self._load_files(
                [ComplianceDocumentId(value=m.id) for m in models]
            )
            documents = [
                to_domain(m, file_groups.get(ComplianceDocumentId(value=m.id), []))
                for m in models
            ]
            missing = {
                item.document_type_id
                for item in documents
                if item.document_type_id not in review_due.document_types
            }
            if missing:
                raise ValueError(
                    "Document types are missing from the review-due filter: "
                    + ", ".join(sorted(str(type_id.value) for type_id in missing))
                    + "."
                )
            filtered = [
                item
                for item in documents
                if item.is_review_due(
                    as_of=review_due.as_of,
                    document_type=review_due.document_types[item.document_type_id],
                )
            ]
            total = len(filtered)
            page = filtered[query.offset : query.offset + query.limit]
            return ComplianceDocumentPage(
                items=tuple(page), total=total, offset=query.offset, limit=query.limit
            )

        total = self._session.scalar(
            select(func.count())
            .select_from(ComplianceDocumentModel)
            .where(where_clause)
        )
        assert total is not None
        models = self._session.scalars(
            select(ComplianceDocumentModel)
            .where(where_clause)
            .order_by(
                ComplianceDocumentModel.created_at.desc(),
                ComplianceDocumentModel.id.desc(),
            )
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        file_groups = self._load_files(
            [ComplianceDocumentId(value=m.id) for m in models]
        )
        items = tuple(
            to_domain(m, file_groups.get(ComplianceDocumentId(value=m.id), []))
            for m in models
        )
        return ComplianceDocumentPage(
            items=items, total=total, offset=query.offset, limit=query.limit
        )

    def save(self, document: ComplianceDocument, *, expected_version: int) -> None:
        self._assert_code_free_in_force(document)
        mapped = to_model(document)
        try:
            result = self._session.execute(
                update(ComplianceDocumentModel)
                .where(
                    ComplianceDocumentModel.id == document.id.value,
                    ComplianceDocumentModel.organization_id
                    == document.organization_id.value,
                    ComplianceDocumentModel.version == expected_version,
                )
                .values(
                    document_type_id=mapped.document_type_id,
                    subject_kind=mapped.subject_kind,
                    subject_id=mapped.subject_id,
                    code=mapped.code,
                    title=mapped.title,
                    status=mapped.status,
                    issued_at=mapped.issued_at,
                    effective_from=mapped.effective_from,
                    next_review_at=mapped.next_review_at,
                    approved_by_document_id=mapped.approved_by_document_id,
                    supersedes_document_id=mapped.supersedes_document_id,
                    superseded_by_document_id=mapped.superseded_by_document_id,
                    applicability=mapped.applicability,
                    source=mapped.source,
                    notes=mapped.notes,
                    status_before_archive=mapped.status_before_archive,
                    archive_reason=mapped.archive_reason,
                    updated_at=mapped.updated_at,
                    updated_by=mapped.updated_by,
                    version=mapped.version,
                )
            )
        except IntegrityError as error:
            if "uq_compliance_documents_org_code_in_force" in str(error.orig):
                raise DuplicateActiveComplianceDocumentCode(
                    organization_id=document.organization_id,
                    code=document.code,
                ) from error
            raise

        if result.rowcount != 1:
            existing = self.get(document.organization_id, document.id)
            if existing is None:
                raise ComplianceDocumentNotFound(document.id)
            raise ComplianceDocumentVersionConflict(
                document_id=document.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )

        # Append any newly-attached files (existing files are never modified or removed).
        stored_ids = {
            row
            for row in self._session.scalars(
                select(DocumentFileModel.id).where(
                    DocumentFileModel.document_id == document.id.value
                )
            ).all()
        }
        new_models = [
            fm for fm in files_to_models(document) if fm.id not in stored_ids
        ]
        for fm in new_models:
            self._session.add(fm)
        if new_models:
            try:
                self._session.flush()
            except IntegrityError as error:
                if "uq_compliance_documents_org_code_in_force" in str(error.orig):
                    raise DuplicateActiveComplianceDocumentCode(
                        organization_id=document.organization_id,
                        code=document.code,
                    ) from error
                raise


