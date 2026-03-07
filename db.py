"""Database layer for Vercel Postgres."""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

_pool = None


def get_conn():
    global _pool
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL not set")
    # Vercel gives postgres:// but psycopg2 needs postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if _pool is None:
        _pool = psycopg2.connect(url, cursor_factory=RealDictCursor)
        _pool.autocommit = True
    return _pool


def query(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return []
    except psycopg2.InterfaceError:
        global _pool
        _pool = None
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return []


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
    except psycopg2.InterfaceError:
        global _pool
        _pool = None
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)


def init_db():
    """Create tables if they don't exist."""
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            name TEXT,
            avatar_url TEXT,
            generations_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            save_info JSONB DEFAULT '{}',
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute("""
        CREATE TABLE IF NOT EXISTS cats (
            id SERIAL PRIMARY KEY,
            save_id INT REFERENCES saves(id) ON DELETE CASCADE,
            cat_key INT NOT NULL,
            name TEXT NOT NULL,
            data JSONB NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute("""
        CREATE INDEX IF NOT EXISTS idx_cats_save_id ON cats(save_id)
    """)
    execute("""
        CREATE INDEX IF NOT EXISTS idx_saves_user_id ON saves(user_id)
    """)


# === User operations ===

def upsert_user(google_id, email, name, avatar_url):
    """Create or update a user from Google OAuth. Returns user dict."""
    row = query_one("""
        INSERT INTO users (google_id, email, name, avatar_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (google_id) DO UPDATE SET
            email = EXCLUDED.email,
            name = EXCLUDED.name,
            avatar_url = EXCLUDED.avatar_url
        RETURNING *
    """, (google_id, email, name, avatar_url))
    return row


def get_user(user_id):
    return query_one("SELECT * FROM users WHERE id = %s", (user_id,))


def increment_generations(user_id):
    execute("UPDATE users SET generations_count = generations_count + 1 WHERE id = %s", (user_id,))


# === Save operations ===

def create_save(user_id, filename, save_info):
    row = query_one("""
        INSERT INTO saves (user_id, filename, save_info)
        VALUES (%s, %s, %s)
        RETURNING *
    """, (user_id, filename, json.dumps(save_info)))
    return row


def get_user_saves(user_id):
    return query("SELECT * FROM saves WHERE user_id = %s ORDER BY uploaded_at DESC", (user_id,))


def get_save(save_id):
    return query_one("SELECT * FROM saves WHERE id = %s", (save_id,))


def delete_save(save_id):
    execute("DELETE FROM saves WHERE id = %s", (save_id,))


# === Cat operations ===

def insert_cats(save_id, cats_data):
    """Bulk insert parsed cats. cats_data is a list of (cat_key, name, data_dict)."""
    conn = get_conn()
    with conn.cursor() as cur:
        for cat_key, name, data in cats_data:
            cur.execute("""
                INSERT INTO cats (save_id, cat_key, name, data)
                VALUES (%s, %s, %s, %s)
            """, (save_id, cat_key, name, json.dumps(data)))


def get_cats_for_save(save_id):
    return query("SELECT * FROM cats WHERE save_id = %s ORDER BY cat_key", (save_id,))


def get_cat(cat_id):
    return query_one("SELECT * FROM cats WHERE id = %s", (cat_id,))


def set_cat_image(cat_id, image_url):
    execute("UPDATE cats SET image_url = %s WHERE id = %s", (image_url, cat_id))
