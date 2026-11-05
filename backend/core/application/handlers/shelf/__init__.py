from __future__ import annotations

from backend.core.application.handlers.shelf.queries import (
    GetShelfOverviewHandler,
    GetShelfSectionSlotsHandler,
    GetShelfSlotHandler,
    SearchShelfSlotsHandler,
)
from backend.core.application.handlers.shelf.sections import (
    AddShelfSubsectionHandler,
    CreateShelfSectionHandler,
    RenameShelfSectionHandler,
    RenameShelfSubsectionHandler,
)
from backend.core.application.handlers.shelf.slots import (
    BULK_EXCLUDE_MAX_ITEMS,
    BulkExcludeShelfSlotsHandler,
    ConfirmShelfSlotApplicableHandler,
    CreateShelfSlotHandler,
    DevelopShelfSlotDocumentHandler,
    ExcludeShelfSlotHandler,
    LinkShelfSlotDocumentHandler,
    RestoreShelfSlotHandler,
    UnlinkShelfSlotDocumentHandler,
    UpdateShelfSlotHandler,
)
from backend.core.application.handlers.shelf.support import (
    DevelopShelfSlotResult,
    ShelfOverviewView,
    ShelfSectionSlotsView,
    ShelfSectionSummaryView,
    ShelfSlotDetailView,
    ShelfSlotView,
    ShelfSubsectionSlotsView,
)

__all__ = [
    "BULK_EXCLUDE_MAX_ITEMS",
    "AddShelfSubsectionHandler",
    "BulkExcludeShelfSlotsHandler",
    "ConfirmShelfSlotApplicableHandler",
    "CreateShelfSectionHandler",
    "CreateShelfSlotHandler",
    "DevelopShelfSlotDocumentHandler",
    "DevelopShelfSlotResult",
    "ExcludeShelfSlotHandler",
    "GetShelfOverviewHandler",
    "GetShelfSectionSlotsHandler",
    "GetShelfSlotHandler",
    "LinkShelfSlotDocumentHandler",
    "RenameShelfSectionHandler",
    "RenameShelfSubsectionHandler",
    "RestoreShelfSlotHandler",
    "SearchShelfSlotsHandler",
    "ShelfOverviewView",
    "ShelfSectionSlotsView",
    "ShelfSectionSummaryView",
    "ShelfSlotDetailView",
    "ShelfSlotView",
    "ShelfSubsectionSlotsView",
    "UnlinkShelfSlotDocumentHandler",
    "UpdateShelfSlotHandler",
]
