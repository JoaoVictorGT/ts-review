import psycopg2
import psycopg2.extras

from config import DATABASE_URL


def get_conn():
    return psycopg2.connect(DATABASE_URL)


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
            SELECT u.hotel_slug, d.focus_hotel_name AS hotel_name
            FROM users u
            JOIN hotel_dashboard_data d ON d.hotel_slug = u.hotel_slug
            WHERE u.email = %s AND u.password = %s
            """,
            (email, password),
        )
        row = cur.fetchone()
        return dict(row) if row else None
