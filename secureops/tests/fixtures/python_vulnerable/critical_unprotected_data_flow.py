"""Critical Python fixture: request input flows into a SQL sink."""


def get_invoice_by_customer_email(request, cursor):
    email = request.args["email"]
    query = (
        "SELECT id, total_cents, status FROM invoices "
        f"WHERE customer_email = '{email}'"
    )
    cursor.execute(query)
    return cursor.fetchall()
