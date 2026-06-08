import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "/code/data/bot.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid             INTEGER PRIMARY KEY,
            first_name      TEXT,
            username        TEXT,
            wallet          INTEGER DEFAULT 0,
            referral_code   TEXT UNIQUE,
            referred_by     INTEGER DEFAULT NULL,
            referral_count  INTEGER DEFAULT 0,
            rewarded_sets   INTEGER DEFAULT 0,
            joined_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            uid              INTEGER,
            plan_key         TEXT,
            plan_name        TEXT,
            plan_price       INTEGER,
            config_name      TEXT,
            paid_from_wallet INTEGER DEFAULT 0,
            discount_pct     INTEGER DEFAULT 0,
            group_msg_id     INTEGER,
            config_data      TEXT DEFAULT NULL,
            purchased_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallet_requests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            uid          INTEGER,
            amount       INTEGER,
            group_msg_id INTEGER DEFAULT NULL,
            status       TEXT DEFAULT 'pending',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE uid=?", (uid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(uid, first_name, username, referral_code, referred_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (uid, first_name, username, referral_code, referred_by)
        VALUES (?,?,?,?,?)
    """, (uid, first_name, username, referral_code, referred_by))
    conn.commit()
    conn.close()


def get_user_by_referral(code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE referral_code=?", (code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_wallet(uid, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET wallet=wallet+? WHERE uid=?", (amount, uid))
    conn.commit()
    conn.close()


def deduct_wallet(uid, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET wallet=wallet-? WHERE uid=?", (amount, uid))
    conn.commit()
    conn.close()


def increment_referral_count(referrer_uid):
    conn = get_conn()
    conn.execute("UPDATE users SET referral_count=referral_count+1 WHERE uid=?", (referrer_uid,))
    conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT referral_count, rewarded_sets FROM users WHERE uid=?", (referrer_uid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_rewarded_set(referrer_uid):
    conn = get_conn()
    conn.execute("UPDATE users SET rewarded_sets=rewarded_sets+1 WHERE uid=?", (referrer_uid,))
    conn.commit()
    conn.close()


def save_purchase(uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id)
        VALUES (?,?,?,?,?,?,?,?)
    """, (uid, plan_key, plan_name, plan_price, config_name, int(paid_from_wallet), discount_pct, group_msg_id))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_purchase_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE group_msg_id=?", (group_msg_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_config_to_purchase(purchase_id, config_data):
    conn = get_conn()
    conn.execute("UPDATE purchases SET config_data=? WHERE id=?", (config_data, purchase_id))
    conn.commit()
    conn.close()


def get_purchases_by_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE uid=? ORDER BY purchased_at DESC", (uid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_purchase_by_id(purchase_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_wallet_request(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO wallet_requests (uid, amount) VALUES (?,?)", (uid, amount))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def set_wallet_request_msg(request_id, group_msg_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET group_msg_id=? WHERE id=?", (group_msg_id, request_id))
    conn.commit()
    conn.close()


def get_wallet_request_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallet_requests WHERE group_msg_id=? AND status='pending'", (group_msg_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def confirm_wallet_request(request_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET status='confirmed' WHERE id=?", (request_id,))
    conn.commit()
    conn.close()
