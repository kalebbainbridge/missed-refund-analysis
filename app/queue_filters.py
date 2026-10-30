def filter_case_queue(
    cases,
    search_text="",
    assignment_mode="all",
    agent_id=None,
):
    required = {"Case ID", "Policy Number", "Client Number", "Agent Working"}
    missing = required - set(cases.columns)
    if missing:
        raise ValueError(f"Missing queue columns: {sorted(missing)}")

    if not isinstance(search_text, str):
        raise ValueError("Search must be text.")
    if assignment_mode not in {"all", "unassigned", "agent"}:
        raise ValueError("Invalid assignment filter.")
    if assignment_mode == "agent" and (
        not isinstance(agent_id, str) or not agent_id.strip()
    ):
        raise ValueError("An agent is required for this filter.")

    filtered = cases.copy()
    term = search_text.strip().casefold()

    if term:
        matches = None
        for column in ["Case ID", "Policy Number", "Client Number"]:
            column_matches = (
                filtered[column].astype("string").str.casefold()
                .str.contains(term, regex=False, na=False)
            )
            matches = column_matches if matches is None else matches | column_matches
        filtered = filtered.loc[matches].copy()

    assignments = filtered["Agent Working"].fillna("").astype(str).str.strip()
    if assignment_mode == "unassigned":
        filtered = filtered.loc[assignments.eq("")].copy()
    elif assignment_mode == "agent":
        filtered = filtered.loc[assignments.eq(agent_id.strip())].copy()

    return filtered.reset_index(drop=True)
