"""US3 controlled clean fixture: equivalent refund update using bind values."""


def approve_refund_with_parameters(request, cursor):
    refund_id = int(request.form["refund_id"])
    reviewer = str(request.form["reviewer"]).strip()
    cursor.execute(
        "UPDATE refunds SET approved_by = ? WHERE id = ?",
        (reviewer, refund_id),
    )
    return cursor.rowcount
