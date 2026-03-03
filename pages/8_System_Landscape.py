from __future__ import annotations

import pandas as pd
import streamlit as st

from src.system_landscape import ALL_CATEGORIES, DEFAULT_STACK_NAME, DISCLAIMER
from src.ui import configure_page, render_page_header, render_section_header, render_status_badges

configure_page("System Landscape", icon=":material/account_tree:")
render_page_header(
    "System Landscape",
    "This page explains the typical destination stack used as example labels in the demo and how those connectors can be swapped without changing the control-tower UX.",
)

render_status_badges(
    [
        {"label": "Source-agnostic", "status": "OK"},
        {"label": "Example labels", "status": "OK"},
        {"label": "Connector swap", "status": "OK"},
    ]
)

render_section_header("Connector model", f"{DEFAULT_STACK_NAME} labels are illustrative only. {DISCLAIMER}")
st.markdown(
    "\n".join(
        [
            "- The demo uses source_system labels as examples, not deployment claims.",
            "- Each category shows the kinds of records and IDs the control tower expects.",
            "- Connectors can be replaced to fit the actual environment without changing the page structure or recommendation schema.",
        ]
    )
)

rows = []
for category in ALL_CATEGORIES:
    rows.append(
        {
            "family": category.family,
            "category": category.category,
            "example_systems": ", ".join(category.examples),
            "contributes": ", ".join(category.contributions),
            "trace_fields": ", ".join(category.trace_fields),
            "id_rule": category.id_rule,
        }
    )

render_section_header("Typical production systems (examples)", "Use this table when the panel asks how the control tower maps to a real venue landscape.")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

render_section_header("Connector-swap concept", "The page layout stays fixed while connectors and source labels can be replaced behind the scenes.")
st.markdown(
    "\n".join(
        [
            "1. Replace example source labels with the actual CMDB, ITSM, EDMS, observability, OT, and ticketing systems.",
            "2. Preserve the required data contract: source_system plus traceable IDs such as ci_id, source_id, doc_ref, dashboard_ref, ot_event_id, and linked_incident_id.",
            "3. Keep the recommendation snapshot schema unchanged so Draft preview, Final authoritative JSON, and exports continue to work.",
        ]
    )
)
