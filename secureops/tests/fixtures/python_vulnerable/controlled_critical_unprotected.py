"""US3 controlled fixture: critical request data reaches a SQL sink."""


def approve_refund_without_protection(request, cursor):
    refund_id = request.form["refund_id"]
    reviewer = request.form["reviewer"]
    query = (
        "UPDATE refunds "
        f"SET approved_by = '{reviewer}' "
        f"WHERE id = {refund_id}"
    )
    cursor.execute(query)
    return cursor.rowcount
