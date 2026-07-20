import json

import psycopg2
import psycopg2.errors
import psycopg2.extras
from slugify import slugify

from auth import hash_password, verify_password
from config import DATABASE_URL
from dashboard_defaults import empty_dashboard_data


class EmailAlreadyRegistered(Exception):
    pass


class UnknownHotelSlug(Exception):
    pass


def get_conn():
    return psycopg2.connect(DATABASE_URL)


_DUMMY_HASH = hash_password("not-a-real-password")


def fetch_dashboard_data(hotel_slug: str) -> dict | None:
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT data FROM hotel_dashboard_data WHERE hotel_slug = %s",
            (hotel_slug,),
        )
        row = cur.fetchone()
        return row["data"] if row else None


def authenticate_user(email: str, password: str) -> dict | None:
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT u.email, u.password AS password_hash, u.name, u.plan,
                   u.hotel_slug, d.focus_hotel_name AS hotel_name
            FROM users u
            JOIN hotel_dashboard_data d ON d.hotel_slug = u.hotel_slug
            WHERE u.email = %s
            """,
            (email,),
        )
        row = cur.fetchone()

    if row is None:
        verify_password(password, _DUMMY_HASH)  # burn equivalent time — avoid a timing oracle for user enumeration
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return {
        "email": row["email"],
        "name": row["name"],
        "plan": row["plan"],
        "hotel_slug": row["hotel_slug"],
        "hotel_name": row["hotel_name"],
    }


def search_hotels(query: str, limit: int = 10) -> list[dict]:
    escaped = query.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT hotel_slug, focus_hotel_name AS hotel_name
            FROM hotel_dashboard_data
            WHERE focus_hotel_name ILIKE %s ESCAPE '\\'
            ORDER BY focus_hotel_name
            LIMIT %s
            """,
            (f"%{escaped}%", limit),
        )
        return [dict(row) for row in cur.fetchall()]


def _insert_placeholder_hotel(cur, hotel_name: str) -> str:
    """Insert a new hotel_dashboard_data row for a brand-new self-registered
    hotel; returns the slug actually used. A SAVEPOINT around each attempt
    means a slug collision doesn't abort the outer transaction — the
    subsequent `users` insert in the same transaction still needs to work.
    """
    base_slug = slugify(hotel_name, separator="_") or "hotel"
    slug, suffix = base_slug, 2
    while True:
        cur.execute("SAVEPOINT before_hotel_insert")
        try:
            cur.execute(
                """
                INSERT INTO hotel_dashboard_data (hotel_slug, focus_hotel_name, data, generated_at)
                VALUES (%s, %s, %s, now())
                """,
                (slug, hotel_name, json.dumps(empty_dashboard_data(hotel_name))),
            )
        except psycopg2.errors.UniqueViolation:
            cur.execute("ROLLBACK TO SAVEPOINT before_hotel_insert")
            slug, suffix = f"{base_slug}_{suffix}", suffix + 1
            continue
        cur.execute("RELEASE SAVEPOINT before_hotel_insert")
        return slug


def register_user(
    *,
    name: str,
    email: str,
    password: str,
    hotel_slug: str | None,
    new_hotel_name: str | None,
    plan: str | None,
) -> dict:
    if bool(hotel_slug) == bool(new_hotel_name):
        raise ValueError("Provide exactly one of hotel_slug or new_hotel_name")

    password_hash = hash_password(password)

    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if new_hotel_name:
                hotel_slug = _insert_placeholder_hotel(cur, new_hotel_name)
                hotel_name = new_hotel_name
            else:
                cur.execute(
                    "SELECT focus_hotel_name FROM hotel_dashboard_data WHERE hotel_slug = %s",
                    (hotel_slug,),
                )
                row = cur.fetchone()
                if row is None:
                    raise UnknownHotelSlug(hotel_slug)
                hotel_name = row["focus_hotel_name"]

            cur.execute(
                "INSERT INTO users (email, password, name, hotel_slug, plan) VALUES (%s, %s, %s, %s, %s)",
                (email, password_hash, name, hotel_slug, plan),
            )
        # clean exit of the `with` block = both inserts committed as one transaction
    except psycopg2.errors.UniqueViolation:
        # Only ever users.email at this point — the hotel-slug case is fully
        # absorbed by the savepoint retry above.
        raise EmailAlreadyRegistered(email) from None

    return {
        "email": email,
        "name": name,
        "hotel_slug": hotel_slug,
        "hotel_name": hotel_name,
        "plan": plan,
    }


def set_user_plan(email: str, plan: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET plan = %s WHERE email = %s", (plan, email))
