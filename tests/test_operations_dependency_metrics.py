from __future__ import annotations

import pandas as pd

from src.metrics import (
    access_governance_summary,
    operations_dependency_matrix,
    parking_mobility_summary,
    wfm_roster_summary,
)


def test_wfm_roster_summary_counts_critical_gaps() -> None:
    df = pd.DataFrame(
        [
            {
                "service": "Ticketing",
                "required_headcount": 4,
                "checked_in_headcount": 2,
                "training_compliance_rate": 0.92,
                "critical_role_flag": True,
                "backfill_required_flag": True,
            },
            {
                "service": "Ticketing",
                "required_headcount": 2,
                "checked_in_headcount": 2,
                "training_compliance_rate": 0.99,
                "critical_role_flag": False,
                "backfill_required_flag": False,
            },
        ]
    )

    result = wfm_roster_summary(df)

    assert result["critical_shift_gaps"] == 1
    assert result["undertrained_shifts"] == 1
    assert result["backfill_required"] == 1


def test_parking_mobility_summary_counts_congestion() -> None:
    df = pd.DataFrame(
        [
            {
                "venue_area": "Main Gate",
                "occupancy_pct": 0.98,
                "queue_minutes": 20.0,
                "ingress_time_min_p95": 22.0,
                "staffing_dependency_flag": True,
                "incident_flag": True,
            },
            {
                "venue_area": "Main Gate",
                "occupancy_pct": 0.70,
                "queue_minutes": 4.0,
                "ingress_time_min_p95": 6.0,
                "staffing_dependency_flag": False,
                "incident_flag": False,
            },
        ]
    )

    result = parking_mobility_summary(df)

    assert result["congestion_windows"] == 1
    assert result["staffing_dependency_windows"] == 1
    assert result["incident_windows"] == 1


def test_access_governance_summary_counts_privileged_exceptions() -> None:
    now = pd.Timestamp("2026-03-03 08:00:00+00:00")
    df = pd.DataFrame(
        [
            {
                "service": "Ticketing",
                "pending_approvals": 4,
                "stale_accounts": 1,
                "mfa_coverage_rate": 0.89,
                "privileged_access_flag": True,
                "segregation_of_duties_flag": True,
                "next_review_due": now - pd.Timedelta(days=1),
            },
            {
                "service": "Ticketing",
                "pending_approvals": 0,
                "stale_accounts": 0,
                "mfa_coverage_rate": 1.0,
                "privileged_access_flag": False,
                "segregation_of_duties_flag": False,
                "next_review_due": now + pd.Timedelta(days=10),
            },
        ]
    )

    result = access_governance_summary(df)

    assert result["pending_privileged_approvals"] == 4
    assert result["privileged_exceptions"] == 1
    assert result["overdue_certifications"] == 1


def test_operations_dependency_matrix_marks_multi_domain_service_critical() -> None:
    services = pd.DataFrame(
        [
            {
                "service": "Ticketing",
                "owner_team": "IT Ops",
                "service_tier": "Tier-1",
                "primary_system": "Ticketing",
                "criticality": 3,
            }
        ]
    )
    readiness = pd.DataFrame(
        [
            {"service": "Ticketing", "status": "RED", "go_no_go": "HOLD"},
            {"service": "Ticketing", "status": "RED", "go_no_go": "HOLD"},
            {"service": "Ticketing", "status": "AMBER", "go_no_go": "HOLD"},
        ]
    )
    wfm = pd.DataFrame(
        [
            {
                "service": "Ticketing",
                "required_headcount": 5,
                "checked_in_headcount": 3,
                "training_compliance_rate": 0.90,
                "critical_role_flag": True,
                "backfill_required_flag": True,
            }
        ]
    )
    parking = pd.DataFrame(
        [
            {
                "venue_area": "Main Gate",
                "occupancy_pct": 0.99,
                "queue_minutes": 19.0,
                "ingress_time_min_p95": 21.0,
                "staffing_dependency_flag": True,
                "incident_flag": False,
            }
        ]
    )
    access = pd.DataFrame(
        [
            {
                "service": "Ticketing",
                "pending_approvals": 5,
                "stale_accounts": 1,
                "mfa_coverage_rate": 0.90,
                "privileged_access_flag": True,
                "segregation_of_duties_flag": True,
                "next_review_due": pd.Timestamp("2026-03-01 08:00:00+00:00"),
            }
        ]
    )

    result = operations_dependency_matrix(services, readiness, wfm, parking, access)

    assert result.iloc[0]["overall_status"] == "CRIT"
    assert result.iloc[0]["arrival_dependency_status"] == "CRIT"
    assert result.iloc[0]["dependency_score"] >= 8
