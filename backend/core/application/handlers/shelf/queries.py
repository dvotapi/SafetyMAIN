"""Read side of the document shelf: overview, one shelf, search, place detail."""

from __future__ import annotations

from collections import defaultdict

from backend.core.application.handlers.shelf.support import (
    ShelfOverviewView,
    ShelfReader,
    ShelfSectionSlotsView,
    ShelfSectionSummaryView,
    ShelfSlotDetailView,
    ShelfSlotView,
    ShelfSubsectionSlotsView,
)
from backend.core.application.queries.shelf import (
    SEARCH_MAX_LIMIT,
    SEARCH_QUERY_MAX_LENGTH,
    GetShelfOverviewQuery,
    GetShelfSectionSlotsQuery,
    GetShelfSlotQuery,
    SearchShelfSlotsQuery,
)
from backend.core.application.services.shelf_status_evaluator import summarize
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.exceptions.shelf import (
    ShelfSectionNotFound,
    ShelfSlotValidationError,
)
from backend.core.domain.value_objects.safety_ids import ShelfSectionId


class _QueryHandlerBase:
    def __init__(self, unit_of_work: UnitOfWorkContract, clock: ClockContract) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock


def _sorted(views: list[ShelfSlotView]) -> tuple[ShelfSlotView, ...]:
    return tuple(sorted(views, key=lambda view: view.slot.code.sort_key))


class GetShelfOverviewHandler(_QueryHandlerBase):
    """All sections with counts, readiness and the per-place strip (one pass)."""

    def handle(self, query: GetShelfOverviewQuery) -> ShelfOverviewView:
        now = self._clock.now()
        reader = ShelfReader(self._unit_of_work, query.organization_id)
        sections = self._unit_of_work.shelf_sections.list(query.organization_id)
        views = reader.views(
            self._unit_of_work.shelf_slots.list_all(query.organization_id), now.date()
        )
        by_section: dict[ShelfSectionId, list[ShelfSlotView]] = defaultdict(list)
        for view in views:
            by_section[view.slot.section_id].append(view)
        summaries = tuple(
            ShelfSectionSummaryView(
                section=section,
                summary=summarize(
                    (view.slot, view.evaluation.effective_status)
                    for view in by_section[section.id]
                ),
                strip=_sorted(by_section[section.id]),
            )
            for section in sections
        )
        totals = summarize((view.slot, view.evaluation.effective_status) for view in views)
        return ShelfOverviewView(sections=summaries, totals=totals, evaluated_at=now)


class GetShelfSectionSlotsHandler(_QueryHandlerBase):
    def handle(self, query: GetShelfSectionSlotsQuery) -> ShelfSectionSlotsView:
        section = self._unit_of_work.shelf_sections.get_by_code(
            query.organization_id, query.section_code
        )
        if section is None:
            raise ShelfSectionNotFound(query.section_code)
        reader = ShelfReader(self._unit_of_work, query.organization_id)
        views = reader.views(
            self._unit_of_work.shelf_slots.list_by_section(query.organization_id, section.id),
            self._clock.now().date(),
        )
        by_subsection: dict[object, list[ShelfSlotView]] = defaultdict(list)
        for view in views:
            by_subsection[view.slot.subsection_id].append(view)
        return ShelfSectionSlotsView(
            section=section,
            subsections=tuple(
                ShelfSubsectionSlotsView(
                    subsection=subsection, slots=_sorted(by_subsection[subsection.id])
                )
                for subsection in sorted(section.subsections, key=lambda item: item.code)
            ),
        )


class SearchShelfSlotsHandler(_QueryHandlerBase):
    """Case-insensitive substring over code, title and short title (P20)."""

    def handle(self, query: SearchShelfSlotsQuery) -> tuple[ShelfSlotView, ...]:
        needle = query.query.strip()
        if not needle or len(needle) > SEARCH_QUERY_MAX_LENGTH:
            raise ShelfSlotValidationError(
                f"Search text must have 1 to {SEARCH_QUERY_MAX_LENGTH} characters."
            )
        if not 1 <= query.limit <= SEARCH_MAX_LIMIT:
            raise ShelfSlotValidationError(f"Limit must be 1 to {SEARCH_MAX_LIMIT}.")
        reader = ShelfReader(self._unit_of_work, query.organization_id)
        slots = self._unit_of_work.shelf_slots.search(
            query.organization_id, needle, limit=query.limit
        )
        return reader.views(slots, self._clock.now().date())


class GetShelfSlotHandler(_QueryHandlerBase):
    def handle(self, query: GetShelfSlotQuery) -> ShelfSlotDetailView:
        reader = ShelfReader(self._unit_of_work, query.organization_id)
        slot = reader.slot(query.slot_id)
        return reader.detail(slot, self._clock.now().date(), query.capabilities)
