"""Database layer for Vercel Postgres."""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

_pool = None

MAX_GENERATIONS = 5


def get_conn():
    global _pool
    url = os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL not set")
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
            published BOOLEAN DEFAULT FALSE,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute("CREATE INDEX IF NOT EXISTS idx_cats_save_id ON cats(save_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_saves_user_id ON saves(user_id)")
    # Migration: add published columns if they don't exist (BEFORE index on published)
    existing = query("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'cats' AND column_name IN ('published', 'published_at')
    """)
    existing_cols = {r["column_name"] for r in existing}
    if "published" not in existing_cols:
        execute("ALTER TABLE cats ADD COLUMN published BOOLEAN DEFAULT FALSE")
    if "published_at" not in existing_cols:
        execute("ALTER TABLE cats ADD COLUMN published_at TIMESTAMP")
    execute("CREATE INDEX IF NOT EXISTS idx_cats_published ON cats(published) WHERE published = TRUE")
    # Likes table
    execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            cat_id INT REFERENCES cats(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, cat_id)
        )
    """)
    execute("CREATE INDEX IF NOT EXISTS idx_likes_cat_id ON likes(cat_id)")


# === User operations ===

def upsert_user(google_id, email, name, avatar_url):
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


def can_generate(user_id):
    user = get_user(user_id)
    if not user:
        return False
    return user["generations_count"] < MAX_GENERATIONS


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


def publish_cat(cat_id):
    execute("UPDATE cats SET published = TRUE, published_at = NOW() WHERE id = %s", (cat_id,))


def unpublish_cat(cat_id):
    execute("UPDATE cats SET published = FALSE, published_at = NULL WHERE id = %s", (cat_id,))


def get_published_cats(limit=50, offset=0):
    """Get published cats with owner info, sorted by likes then date."""
    return query("""
        SELECT c.*, u.name as owner_name, u.avatar_url as owner_avatar,
               COALESCE(lk.like_count, 0) as like_count
        FROM cats c
        JOIN saves s ON c.save_id = s.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (SELECT cat_id, COUNT(*) as like_count FROM likes GROUP BY cat_id) lk ON lk.cat_id = c.id
        WHERE c.published = TRUE AND c.image_url IS NOT NULL
        ORDER BY like_count DESC, c.published_at DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))


def get_published_count():
    row = query_one("SELECT COUNT(*) as cnt FROM cats WHERE published = TRUE AND image_url IS NOT NULL")
    return row["cnt"] if row else 0


def get_cat_owner_id(cat_id):
    """Get the user_id who owns a cat."""
    row = query_one("""
        SELECT s.user_id FROM cats c
        JOIN saves s ON c.save_id = s.id
        WHERE c.id = %s
    """, (cat_id,))
    return row["user_id"] if row else None


# === Likes ===

def toggle_like(user_id, cat_id):
    """Toggle like. Returns (liked: bool, new_count: int)."""
    existing = query_one(
        "SELECT id FROM likes WHERE user_id = %s AND cat_id = %s", (user_id, cat_id)
    )
    if existing:
        execute("DELETE FROM likes WHERE user_id = %s AND cat_id = %s", (user_id, cat_id))
        liked = False
    else:
        execute("INSERT INTO likes (user_id, cat_id) VALUES (%s, %s)", (user_id, cat_id))
        liked = True
    row = query_one("SELECT COUNT(*) as cnt FROM likes WHERE cat_id = %s", (cat_id,))
    return liked, row["cnt"] if row else 0


def get_likes_count(cat_id):
    row = query_one("SELECT COUNT(*) as cnt FROM likes WHERE cat_id = %s", (cat_id,))
    return row["cnt"] if row else 0


def get_user_likes(user_id):
    """Get set of cat_ids liked by user."""
    rows = query("SELECT cat_id FROM likes WHERE user_id = %s", (user_id,))
    return {r["cat_id"] for r in rows}
