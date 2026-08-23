"""Clean Python fixture with parameterized database access."""


def normalize_username(raw_username: str) -> str:
    username = raw_username.strip().lower()
    if not username.replace("_", "").isalnum():
        raise ValueError("username contains unsupported characters")
    return username


def find_user_by_username(cursor, raw_username: str):
    username = normalize_username(raw_username)
    cursor.execute(
        "SELECT id, username, email FROM users WHERE username = ?",
        (username,),
    )
    return cursor.fetchone()
