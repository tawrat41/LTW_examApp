from __future__ import annotations

from app.infrastructure.admin_queries import AdminQueryRepository

from .dto import DashboardStats, LookupItem


class AdminQueryService:
    def __init__(self, repository: AdminQueryRepository) -> None:
        self._repository = repository

    def get_dashboard_stats(self) -> DashboardStats:
        return self._repository.get_dashboard_stats()

    def list_exam_options(self) -> list[LookupItem]:
        return self._repository.list_exam_options()

    def list_section_options(self, exam_id: str) -> list[LookupItem]:
        return self._repository.list_section_options(exam_id)
