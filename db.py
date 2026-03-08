"""Database layer for Vercel Postgres."""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

_pool = None

MAX_GENERATIONS = 5
MAX_GENERATIONS_PREMIUM = 50
MAX_ACTIVE_USERS = 100  # After this, new users go to waitlist
WAITLIST_BATCH_SIZE = 50


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
    # Migration: add is_premium column to users
    user_cols = query("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'is_premium'
    """)
    if not user_cols:
        execute("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE")
    # Migration: add is_admin column to users
    admin_cols = query("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'is_admin'
    """)
    if not admin_cols:
        execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
    # Migration: add waitlist_approved column to users
    wl_cols = query("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'waitlist_approved'
    """)
    if not wl_cols:
        execute("ALTER TABLE users ADD COLUMN waitlist_approved BOOLEAN DEFAULT TRUE")
        # Existing users are approved by default; new ones after limit will be FALSE
    # Feedback table
    execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id) ON DELETE SET NULL,
            email TEXT,
            name TEXT,
            message TEXT NOT NULL,
            page_url TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Settings table
    init_settings()


# === User operations ===

def upsert_user(google_id, email, name, avatar_url):
    # Check if user already exists
    existing = query_one("SELECT id FROM users WHERE google_id = %s", (google_id,))
    if existing:
        # Existing user — just update profile, keep waitlist status
        row = query_one("""
            UPDATE users SET email = %s, name = %s, avatar_url = %s
            WHERE google_id = %s RETURNING *
        """, (email, name, avatar_url, google_id))
        return row
    else:
        # New user — check if should be waitlisted
        approved = not should_waitlist_new_user()
        # Admins/founders always approved
        if email in ADMIN_EMAILS:
            approved = True
        row = query_one("""
            INSERT INTO users (google_id, email, name, avatar_url, waitlist_approved)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (google_id, email, name, avatar_url, approved))
        return row


def get_user(user_id):
    return query_one("SELECT * FROM users WHERE id = %s", (user_id,))


def increment_generations(user_id):
    execute("UPDATE users SET generations_count = generations_count + 1 WHERE id = %s", (user_id,))


def get_user_max_generations(user):
    """Return max generations limit based on premium status."""
    if user and user.get("is_premium"):
        return MAX_GENERATIONS_PREMIUM
    return MAX_GENERATIONS


def can_generate(user_id):
    user = get_user(user_id)
    if not user:
        return False
    return user["generations_count"] < get_user_max_generations(user)


def set_premium(user_id, is_premium=True):
    execute("UPDATE users SET is_premium = %s WHERE id = %s", (is_premium, user_id))


def set_premium_by_email(email, is_premium=True):
    execute("UPDATE users SET is_premium = %s WHERE email = %s", (is_premium, email))


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


# === Admin ===

ADMIN_EMAILS = ["pafa0712@gmail.com", "insaneramzes@gmail.com"]


def is_admin(user_id):
    """Check if user is admin by email or is_admin flag."""
    user = get_user(user_id)
    if not user:
        return False
    return user.get("email", "") in ADMIN_EMAILS or bool(user.get("is_admin"))


def set_admin(user_id, is_admin_flag=True):
    execute("UPDATE users SET is_admin = %s WHERE id = %s", (is_admin_flag, user_id))


# === Waitlist ===

def get_active_user_count():
    """Count users that are approved (not on waitlist)."""
    row = query_one("SELECT COUNT(*) as cnt FROM users WHERE waitlist_approved = TRUE")
    return row["cnt"] if row else 0


def should_waitlist_new_user():
    """Check if new users should be put on waitlist."""
    return get_active_user_count() >= MAX_ACTIVE_USERS


def is_user_approved(user_id):
    """Check if user is approved (not on waitlist)."""
    user = get_user(user_id)
    if not user:
        return False
    return bool(user.get("waitlist_approved", True))


def get_waitlist(limit=200):
    """Get users on waitlist, ordered by registration date."""
    return query("""
        SELECT id, name, email, avatar_url, created_at
        FROM users WHERE waitlist_approved = FALSE
        ORDER BY created_at ASC LIMIT %s
    """, (limit,))


def get_waitlist_count():
    row = query_one("SELECT COUNT(*) as cnt FROM users WHERE waitlist_approved = FALSE")
    return row["cnt"] if row else 0


def get_waitlist_position(user_id):
    """Get user's position in waitlist (1-based), or 0 if approved."""
    user = get_user(user_id)
    if not user or user.get("waitlist_approved", True):
        return 0
    row = query_one("""
        SELECT COUNT(*) as pos FROM users
        WHERE waitlist_approved = FALSE AND created_at <= (
            SELECT created_at FROM users WHERE id = %s
        )
    """, (user_id,))
    return row["pos"] if row else 0


def approve_waitlist_batch(count=None):
    """Approve the next batch of waitlisted users. Returns count approved."""
    if count is None:
        count = WAITLIST_BATCH_SIZE
    rows = query("""
        UPDATE users SET waitlist_approved = TRUE
        WHERE id IN (
            SELECT id FROM users
            WHERE waitlist_approved = FALSE
            ORDER BY created_at ASC
            LIMIT %s
        )
        RETURNING id
    """, (count,))
    return len(rows)


def approve_user(user_id):
    """Approve a single user from waitlist."""
    execute("UPDATE users SET waitlist_approved = TRUE WHERE id = %s", (user_id,))


# === Settings (key-value store for prompts etc.) ===

def init_settings():
    """Create settings table."""
    execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)


def get_setting(key, default=None):
    row = query_one("SELECT value FROM settings WHERE key = %s", (key,))
    return row["value"] if row else default


def set_setting(key, value):
    execute("""
        INSERT INTO settings (key, value, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
    """, (key, value))


# === Feedback ===

def create_feedback(user_id, email, name, message, page_url=None):
    return query_one("""
        INSERT INTO feedback (user_id, email, name, message, page_url)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """, (user_id, email, name, message, page_url))


def get_all_feedback(limit=50, offset=0):
    return query("""
        SELECT * FROM feedback ORDER BY created_at DESC LIMIT %s OFFSET %s
    """, (limit, offset))


def get_unread_feedback_count():
    row = query_one("SELECT COUNT(*) as cnt FROM feedback WHERE is_read = FALSE")
    return row["cnt"] if row else 0


def mark_feedback_read(feedback_id):
    execute("UPDATE feedback SET is_read = TRUE WHERE id = %s", (feedback_id,))


# === Analytics ===

def get_analytics():
    """Get basic analytics data."""
    stats = {}
    row = query_one("SELECT COUNT(*) as cnt FROM users")
    stats["total_users"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM users WHERE generations_count > 0")
    stats["users_with_generations"] = row["cnt"] if row else 0

    row = query_one("SELECT COALESCE(SUM(generations_count), 0) as cnt FROM users")
    stats["total_generations"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM cats")
    stats["total_cats"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM cats WHERE image_url IS NOT NULL")
    stats["cats_with_images"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM cats WHERE published = TRUE")
    stats["published_cats"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM saves")
    stats["total_saves"] = row["cnt"] if row else 0

    row = query_one("SELECT COUNT(*) as cnt FROM likes")
    stats["total_likes"] = row["cnt"] if row else 0

    # Top users by generations
    stats["top_users"] = query("""
        SELECT id, name, email, generations_count, is_premium, is_admin,
               (SELECT COUNT(*) FROM saves WHERE user_id = users.id) as saves_count,
               (SELECT COUNT(*) FROM cats c JOIN saves s ON c.save_id = s.id WHERE s.user_id = users.id) as cats_count
        FROM users ORDER BY generations_count DESC LIMIT 20
    """)

    # Recent generations (cats with images)
    stats["recent_images"] = query("""
        SELECT c.id, c.name, c.image_url, u.name as owner_name, u.email as owner_email
        FROM cats c
        JOIN saves s ON c.save_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE c.image_url IS NOT NULL
        ORDER BY c.id DESC LIMIT 20
    """)

    return stats
