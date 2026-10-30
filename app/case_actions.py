from datetime import datetime, timezone

from app.database import DATABASE_PATH, get_connection


def save_case_notes(
    case_id,
    agent_id,
    notes,
    expected_version,
    database_path=DATABASE_PATH,
    investigation_reason=None,
):
    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if not isinstance(notes, str):
        raise ValueError("Notes must be text.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    updated_at = datetime.now(timezone.utc).isoformat()

    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        previous = connection.execute(
            """
            SELECT "Case Status", "Investigation Reason"
            FROM agent_updates
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Record Version" = ?
              AND "Case Status" IN (
                  'Open',
                  'Awaiting Dependency',
                  'Awaiting Senior Review',
                  'Awaiting Other Department'
              );
            """,
            (case_id, agent_id, expected_version),
        ).fetchone()

        if previous is None:
            return False

        previous_status, previous_reason = previous

        reason = (
            previous_reason
            if investigation_reason is None
            else investigation_reason
        )

        validate_investigation(reason, notes)

        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Agent Notes" = ?,
                "Investigation Reason" = ?,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Case Status" = ?
              AND "Record Version" = ?;
            """,
            (
                notes,
                reason,
                updated_at,
                case_id,
                agent_id,
                previous_status,
                expected_version,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Investigation Updated",
                previous_status,
                previous_status,
                agent_id,
                updated_at,
                (
                    f"Previous reason: {previous_reason}\n"
                    f"Investigation reason: {reason}\n"
                    f"Agent notes: {notes}"
                ),
            ),
        )

    return True

def claim_case(
    case_id,
    agent_id,
    expected_version,
    database_path=DATABASE_PATH,
):
    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    updated_at = datetime.now(timezone.utc).isoformat()

    with get_connection(database_path) as connection:
        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Agent Working" = ?,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Case Status" = 'Open'
              AND (
                  "Agent Working" IS NULL
                  OR TRIM("Agent Working") = ''
              )
              AND "Record Version" = ?;
            """,
            (
                agent_id,
                updated_at,
                case_id,
                expected_version,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Case Assigned",
                "Open",
                "Open",
                agent_id,
                updated_at,
                f"Case assigned to {agent_id}.",
            ),
        )

    return True

def release_case(
    case_id,
    agent_id,
    expected_version,
    database_path=DATABASE_PATH,
):
    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    updated_at = datetime.now(timezone.utc).isoformat()

    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        previous = connection.execute(
            """
            SELECT "Case Status"
            FROM agent_updates
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Record Version" = ?
              AND "Case Status" IN (
                  'Open',
                  'Awaiting Dependency',
                  'Awaiting Senior Review',
                  'Awaiting Other Department'
              );
            """,
            (case_id, agent_id, expected_version),
        ).fetchone()

        if previous is None:
            return False

        previous_status = previous[0]

        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Agent Working" = NULL,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Record Version" = ?
              AND "Case Status" = ?;
            """,
            (
                updated_at,
                case_id,
                agent_id,
                expected_version,
                previous_status,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Assignment Removed",
                previous_status,
                previous_status,
                agent_id,
                updated_at,
                f"{agent_id} returned the case to the shared queue.",
            ),
        )

    return True

def complete_case(
    case_id,
    agent_id,
    final_outcome,
    notes,
    expected_version,
    database_path=DATABASE_PATH,
    investigation_reason=None,
):
    allowed_outcomes = {
        "Refund Processed",
        "Refund Already Processed",
        "No Refund Due",
    }

    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if final_outcome not in allowed_outcomes:
        raise ValueError("Select a valid final outcome.")

    if not isinstance(notes, str):
        raise ValueError("Notes must be text.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    now = datetime.now(timezone.utc)
    updated_at = now.isoformat()
    completion_date = now.date().isoformat()

    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        previous = connection.execute(
            """
            SELECT "Investigation Reason"
            FROM agent_updates
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Case Status" = 'Open'
              AND "Record Version" = ?;
            """,
            (case_id, agent_id, expected_version),
        ).fetchone()

        if previous is None:
            return False

        previous_reason = previous[0]

        reason = (
            previous_reason
            if investigation_reason is None
            else investigation_reason
        )

        validate_investigation(reason, notes, completing=True)

        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Agent Notes" = ?,
                "Investigation Reason" = ?,
                "Case Status" = 'Completed',
                "Final Outcome" = ?,
                "Completed By" = ?,
                "Completion Date" = ?,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Case Status" = 'Open'
              AND "Record Version" = ?;
            """,
            (
                notes,
                reason,
                final_outcome,
                agent_id,
                completion_date,
                updated_at,
                case_id,
                agent_id,
                expected_version,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Case Completed",
                "Open",
                "Completed",
                agent_id,
                updated_at,
                (
                    f"Final outcome: {final_outcome}\n"
                    f"Previous reason: {previous_reason}\n"
                    f"Investigation reason: {reason}\n"
                    f"Agent notes: {notes}"
                ),
            ),
        )

    return True

def raise_dependency(
    case_id,
    agent_id,
    dependency_type,
    owner,
    target_date,
    details,
    notes,
    expected_version,
    database_path=DATABASE_PATH,
):
    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if dependency_type not in {"Senior Review", "Other Department"}:
        raise ValueError("Select a valid dependency type.")

    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("A dependency owner is required.")

    if not isinstance(details, str) or not details.strip():
        raise ValueError("Dependency details are required.")

    if not isinstance(notes, str):
        raise ValueError("Notes must be text.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    now = datetime.now(timezone.utc)

    try:
        target = datetime.strptime(
            str(target_date), "%Y-%m-%d"
        ).date()
    except ValueError as exc:
        raise ValueError(
            "Target date must use YYYY-MM-DD."
        ) from exc

    if target < now.date():
        raise ValueError("Target date cannot be in the past.")

    updated_at = now.isoformat()
    owner = owner.strip()
    details = details.strip()

    with get_connection(database_path) as connection:
        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Agent Notes" = ?,
                "Case Status" = 'Awaiting Dependency',
                "Dependency Type" = ?,
                "Dependency Owner" = ?,
                "Dependency Raised Date" = ?,
                "Dependency Target Date" = ?,
                "Dependency Details" = ?,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Case Status" = 'Open'
              AND "Record Version" = ?;
            """,
            (
                notes,
                dependency_type,
                owner,
                now.date().isoformat(),
                target.isoformat(),
                details,
                updated_at,
                case_id,
                agent_id,
                expected_version,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Dependency Raised",
                "Open",
                "Awaiting Dependency",
                agent_id,
                updated_at,
                (
                    f"Type: {dependency_type}\n"
                    f"Owner: {owner}\n"
                    f"Target: {target.isoformat()}\n"
                    f"Details: {details}\n"
                    f"Agent notes: {notes}"
                ),
            ),
        )

    return True

def resolve_dependency(
    case_id,
    agent_id,
    resolution_note,
    expected_version,
    database_path=DATABASE_PATH,
):
    if not case_id or not agent_id:
        raise ValueError("Case and agent identifiers are required.")

    if not isinstance(resolution_note, str) or not resolution_note.strip():
        raise ValueError("A dependency resolution note is required.")

    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("A valid loaded record version is required.")

    updated_at = datetime.now(timezone.utc).isoformat()

    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        previous = connection.execute(
            """
            SELECT
                "Case Status",
                "Dependency Type",
                "Dependency Owner",
                "Dependency Raised Date",
                "Dependency Target Date",
                "Dependency Details"
            FROM agent_updates
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Record Version" = ?
              AND "Case Status" IN (
                  'Awaiting Dependency',
                  'Awaiting Senior Review',
                  'Awaiting Other Department'
              );
            """,
            (case_id, agent_id, expected_version),
        ).fetchone()

        if previous is None:
            return False

        (
            previous_status,
            dependency_type,
            owner,
            raised_date,
            target_date,
            details,
        ) = previous

        result = connection.execute(
            """
            UPDATE agent_updates
            SET "Case Status" = 'Open',
                "Dependency Type" = NULL,
                "Dependency Owner" = NULL,
                "Dependency Raised Date" = NULL,
                "Dependency Target Date" = NULL,
                "Dependency Details" = NULL,
                "Last Updated Date" = ?,
                "Record Version" = "Record Version" + 1
            WHERE "Case ID" = ?
              AND "Agent Working" = ?
              AND "Record Version" = ?
              AND "Case Status" = ?;
            """,
            (
                updated_at,
                case_id,
                agent_id,
                expected_version,
                previous_status,
            ),
        )

        if result.rowcount != 1:
            return False

        connection.execute(
            """
            INSERT INTO workflow_events (
                Case_ID,
                Event_Type,
                From_Status,
                To_Status,
                Agent_ID,
                Event_Date,
                Event_Notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                case_id,
                "Dependency Resolved",
                previous_status,
                "Open",
                agent_id,
                updated_at,
                (
                    f"Resolution: {resolution_note.strip()}\n"
                    f"Previous type: {dependency_type}\n"
                    f"Previous owner: {owner}\n"
                    f"Raised: {raised_date}\n"
                    f"Target: {target_date}\n"
                    f"Previous details: {details}"
                ),
            ),
        )

    return True
INVESTIGATION_REASONS = (
    "Not Yet Determined",
    "Payment Date Misunderstood",
    "Refund Action Missed",
    "Waiting for Information",
    "Refund Mailbox Delay",
    "Other",
)


def validate_investigation(reason, notes, completing=False):
    if reason not in INVESTIGATION_REASONS:
        raise ValueError("Select a valid investigation reason.")

    if not isinstance(notes, str):
        raise ValueError("Investigation notes must be text.")

    if reason == "Other" and not notes.strip():
        raise ValueError(
            "Explain the Other investigation reason in the notes."
        )

    if (
        completing
        and reason == "Not Yet Determined"
        and not notes.strip()
    ):
        raise ValueError(
            "Explain why the case can be completed "
            "while its investigation reason remains unknown."
        )