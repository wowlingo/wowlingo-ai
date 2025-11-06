"""Direct PyMySQL connection helper - bypasses SQLAlchemy entirely"""
import pymysql
from contextlib import contextmanager
from app.common.config import settings


@contextmanager
def get_raw_connection():
    """
    PyMySQL 직접 연결 - SQLAlchemy 우회

    Usage:
        with get_raw_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    conn = None
    try:
        conn = pymysql.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.username,
            password=settings.database.password,
            database=settings.database.database,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
        yield conn
    finally:
        if conn:
            conn.close()


def execute_query(query, params=None, fetch_one=False):
    """
    간단한 쿼리 실행 헬퍼

    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터 (옵션)
        fetch_one: True면 fetchone(), False면 fetchall()

    Returns:
        쿼리 결과
    """
    with get_raw_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())

        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()

        cursor.close()
        return result
