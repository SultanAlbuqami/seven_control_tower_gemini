from __future__ import annotations

from src.system_landscape import CATEGORY_BY_SLUG, ORR_TRACKER_LABELS, acronym_guide_rows


def test_core_badges_have_human_readable_tooltips() -> None:
    assert CATEGORY_BY_SLUG["itsm_cmdb"].badge_tooltip == "IT Service Management / Configuration Management Database"
    assert CATEGORY_BY_SLUG["cmms_eam"].badge_tooltip == "Computerized Maintenance Management System / Enterprise Asset Management"
    assert CATEGORY_BY_SLUG["edms_document_control"].badge_tooltip == "Electronic Document Management System"


def test_pmis_is_available_as_optional_project_controls_extension() -> None:
    category = CATEGORY_BY_SLUG["pmis_project_controls"]

    assert category.badge_label == "PMIS"
    assert category.optional is True
    assert any("PMIS" in label or "Primavera" in label for label in category.examples)
    assert any("PMIS" in label for label in ORR_TRACKER_LABELS)


def test_acronym_guide_includes_pmis_and_itsm() -> None:
    guide = {row["abbreviation"]: row["full_name"] for row in acronym_guide_rows()}

    assert guide["ITSM"] == "IT Service Management"
    assert guide["PMIS"] == "Project Management Information System"
