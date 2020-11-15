from plugins.catch import get_connection


def init_weekly_point():
    sql = "UPDATE angler_ranking "\
        f"SET weekly_point = 0"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()


def init_monthly_point():
    sql = "UPDATE angler_ranking "\
        f"SET monthly_point = 0"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
