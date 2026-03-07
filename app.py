"""Mewgenics Cat Viewer — Flask app for local dev and Vercel deployment."""

import json
import os
import tempfile

from flask import Flask, render_template, jsonify, request, redirect, make_response, Response

from cat_parser import load_all_cats, get_save_info, CatData, CatStats
from prompt_builder import build_prompt, build_cat_summary_ru, build_cat_summary
from prompt_writer import (generate_visual_prompt, get_image_model, get_system_instruction,
                           get_user_prompt_template, get_prompt_model,
                           DEFAULT_SYSTEM_INSTRUCTION, DEFAULT_USER_PROMPT_TEMPLATE,
                           SETTING_SYSTEM_INSTRUCTION, SETTING_USER_PROMPT_TEMPLATE,
                           SETTING_PROMPT_MODEL, SETTING_IMAGE_MODEL,
                           PROMPT_MODEL, _build_cat_data_text)
from auth import get_google_auth_url, exchange_code, create_jwt, get_current_user
import db
import storage

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPPORTED_LANGS = ('en', 'ru')


# === Helpers ===

def get_lang():
    """Get current language from cookie, default to 'ru'."""
    lang = request.cookies.get('lang', 'ru')
    return lang if lang in SUPPORTED_LANGS else 'ru'


def require_auth():
    return get_current_user(request)


def _cat_data_from_row(row):
    d = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    stats = CatStats(
        base=d.get("stats_base", [0]*7),
        bonus=d.get("stats_bonus", [0]*7),
        extra=d.get("stats_extra", [0]*7),
    )
    return CatData(
        id=row["cat_key"],
        name=d.get("name", ""),
        voice=d.get("voice", ""),
        gender=d.get("gender", ""),
        gender_code=d.get("gender_code", 0),
        stat_focus=d.get("stat_focus", ""),
        cat_class=d.get("cat_class", "Colorless"),
        basic_attack=d.get("basic_attack", ""),
        abilities=d.get("abilities", []),
        passives=d.get("passives", []),
        items=d.get("items", []),
        mutations=d.get("mutations", {}),
        all_frames=d.get("all_frames", {}),
        stats=stats,
        status=d.get("status", "OK"),
        is_dead=d.get("is_dead", False),
        is_retired=d.get("is_retired", False),
        is_donated=d.get("is_donated", False),
        birth_day=d.get("birth_day"),
        age_days=d.get("age_days"),
        pre_meta_flags=d.get("pre_meta_flags", 0),
        parent_keys=d.get("parent_keys", []),
        inbreeding_level=d.get("inbreeding_level", 0),
        breed=d.get("breed", ""),
    )


def _cat_to_db_data(cat):
    return {
        "name": cat.name,
        "voice": cat.voice,
        "gender": cat.gender,
        "gender_code": cat.gender_code,
        "stat_focus": cat.stat_focus,
        "cat_class": cat.cat_class,
        "basic_attack": cat.basic_attack,
        "abilities": cat.abilities,
        "passives": cat.passives,
        "items": cat.items,
        "mutations": cat.mutations,
        "all_frames": cat.all_frames,
        "status": cat.status,
        "is_dead": cat.is_dead,
        "is_retired": cat.is_retired,
        "is_donated": cat.is_donated,
        "birth_day": cat.birth_day,
        "age_days": cat.age_days,
        "pre_meta_flags": cat.pre_meta_flags,
        "parent_keys": cat.parent_keys,
        "inbreeding_level": cat.inbreeding_level,
        "breed": cat.breed,
        "stats_base": cat.stats.base,
        "stats_bonus": cat.stats.bonus,
        "stats_extra": cat.stats.extra,
    }


# === Auth routes ===

@app.route("/auth/google")
def auth_google():
    return redirect(get_google_auth_url())


@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return redirect("/?error=no_code")

    user_info = exchange_code(code)
    if not user_info:
        return redirect("/?error=auth_failed")

    user = db.upsert_user(
        user_info.get("id", ""),
        user_info.get("email", ""),
        user_info.get("name", ""),
        user_info.get("picture", ""),
    )
    token = create_jwt(user["id"], user_info.get("email", ""), user_info.get("name", ""))

    resp = make_response(redirect("/cabinet"))
    resp.set_cookie("auth_token", token, httponly=True, secure=True,
                     samesite="Lax", max_age=60*60*24*30)
    return resp


@app.route("/auth/logout")
def auth_logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie("auth_token")
    return resp


@app.route("/auth/me")
def auth_me():
    user = require_auth()
    if not user:
        return jsonify({"authenticated": False})
    db_user = db.get_user(user["user_id"])
    if not db_user:
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "user": {
            "id": db_user["id"],
            "name": db_user["name"],
            "email": db_user["email"],
            "avatar_url": db_user["avatar_url"],
            "generations_count": db_user["generations_count"],
            "max_generations": db.get_user_max_generations(db_user),
            "is_premium": bool(db_user.get("is_premium")),
        }
    })


@app.route("/api/set-lang", methods=["POST"])
def api_set_lang():
    data = request.get_json() or {}
    lang = data.get("lang", "ru")
    if lang not in SUPPORTED_LANGS:
        lang = "ru"
    resp = jsonify({"success": True, "lang": lang})
    resp.set_cookie("lang", lang, max_age=365*24*3600, samesite="Lax")
    return resp


# === Pages ===

@app.route("/")
def index():
    return render_template("index.html", page="feed", lang=get_lang())


@app.route("/cabinet")
def cabinet():
    return render_template("index.html", page="cabinet", lang=get_lang())


@app.route("/img/<int:cat_id>")
def img_proxy(cat_id):
    """Proxy cat image through our domain to bypass blob storage blocks."""
    import requests as http_requests
    row = db.get_cat(cat_id)
    if not row or not row.get("image_url"):
        return "Not found", 404
    try:
        resp = http_requests.get(row["image_url"], timeout=15)
        if resp.status_code != 200:
            return "Upstream error", 502
        r = Response(resp.content, content_type=resp.headers.get("Content-Type", "image/png"))
        r.headers["Cache-Control"] = "public, max-age=86400, s-maxage=604800"
        r.headers["CDN-Cache-Control"] = "public, max-age=604800"
        return r
    except Exception:
        return "Error", 502


@app.route("/cat/<int:cat_id>")
def cat_page(cat_id):
    """Dedicated cat page with OG tags for social sharing."""
    row = db.get_cat(cat_id)
    if not row or not row.get("published") or not row.get("image_url"):
        return redirect("/")
    data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    name = data.get("name", "Cat")
    cat_class = data.get("cat_class", "")
    image_url = row["image_url"]
    # Get owner
    owner_id = db.get_cat_owner_id(cat_id)
    owner = db.get_user(owner_id) if owner_id else None
    owner_name = owner["name"] if owner else ""
    likes = db.get_likes_count(cat_id)
    return render_template("cat_share.html",
                           cat_id=cat_id, name=name, cat_class=cat_class,
                           image_url=image_url, owner_name=owner_name,
                           likes=likes)


# === Public feed API ===

@app.route("/api/feed")
def api_feed():
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 100)

    rows = db.get_published_cats(limit=limit, offset=offset)
    total = db.get_published_count()

    # Get current user's likes
    user = require_auth()
    user_likes = set()
    if user:
        user_likes = db.get_user_likes(user["user_id"])

    lang = get_lang()
    result = []
    for row in rows:
        cat = _cat_data_from_row(row)
        summary = build_cat_summary(cat, lang=lang)
        summary["db_id"] = row["id"]
        summary["image_url"] = row.get("image_url")
        summary["owner_name"] = row.get("owner_name", "")
        summary["owner_avatar"] = row.get("owner_avatar", "")
        summary["published_at"] = row["published_at"].isoformat() if row.get("published_at") else None
        summary["like_count"] = row.get("like_count", 0)
        summary["liked"] = row["id"] in user_likes
        result.append(summary)

    return jsonify({"cats": result, "total": total})


# === Save upload ===

@app.route("/api/upload", methods=["POST"])
def api_upload():
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    file = request.files.get("save_file")
    if not file or not file.filename:
        return jsonify({"error": "Файл не выбран"}), 400

    with tempfile.NamedTemporaryFile(suffix=".sav", delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        save_info = get_save_info(tmp_path)
        cats = load_all_cats(tmp_path)
    except Exception as e:
        os.unlink(tmp_path)
        return jsonify({"error": f"Ошибка парсинга: {e}"}), 400
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Delete old saves
    old_saves = db.get_user_saves(user["user_id"])
    for old in old_saves:
        old_cats = db.get_cats_for_save(old["id"])
        for oc in old_cats:
            if oc.get("image_url"):
                storage.delete_blob(oc["image_url"])
        db.delete_save(old["id"])

    save = db.create_save(user["user_id"], file.filename, save_info)

    cats_data = []
    for cat in cats:
        cats_data.append((cat.id, cat.name, _cat_to_db_data(cat)))
    db.insert_cats(save["id"], cats_data)

    return jsonify({
        "success": True,
        "save_id": save["id"],
        "cat_count": len(cats),
        "save_info": save_info,
    })


# === Cat API (private — user's own cats) ===

@app.route("/api/cats")
def api_cats():
    user = require_auth()
    if not user:
        return jsonify([])

    saves = db.get_user_saves(user["user_id"])
    if not saves:
        return jsonify([])

    rows = db.get_cats_for_save(saves[0]["id"])
    lang = get_lang()

    result = []
    for row in rows:
        cat = _cat_data_from_row(row)
        summary = build_cat_summary(cat, lang=lang)
        summary["db_id"] = row["id"]
        summary["has_image"] = bool(row.get("image_url"))
        summary["image_url"] = row.get("image_url")
        summary["published"] = bool(row.get("published"))
        result.append(summary)

    return jsonify(result)


@app.route("/api/save-info")
def api_save_info():
    user = require_auth()
    if not user:
        return jsonify({})

    saves = db.get_user_saves(user["user_id"])
    if not saves:
        return jsonify({})

    save = saves[0]
    info = save["save_info"] if isinstance(save["save_info"], dict) else json.loads(save["save_info"])
    info["save_id"] = save["id"]
    info["filename"] = save["filename"]
    return jsonify(info)


@app.route("/api/cat/<int:db_cat_id>/debug")
def api_cat_debug(db_cat_id):
    """Debug: show raw parsed data for a cat."""
    row = db.get_cat(db_cat_id)
    if not row:
        return jsonify({"error": "not found"}), 404
    cat = _cat_data_from_row(row)
    d = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    return jsonify({
        "name": cat.name,
        "class": cat.cat_class,
        "voice": d.get("voice", ""),
        "gender": d.get("gender", ""),
        "gender_code": d.get("gender_code", 0),
        "stat_focus": d.get("stat_focus", ""),
        "basic_attack": d.get("basic_attack", ""),
        "abilities": d.get("abilities", []),
        "passives": d.get("passives", []),
        "items": d.get("items", []),
        "mutations": d.get("mutations", {}),
        "all_frames": d.get("all_frames", {}),
        "stats_base": d.get("stats_base", []),
        "stats_bonus": d.get("stats_bonus", []),
        "stats_extra": d.get("stats_extra", []),
        "status": d.get("status", ""),
        "is_dead": d.get("is_dead", False),
        "is_retired": d.get("is_retired", False),
        "is_donated": d.get("is_donated", False),
        "birth_day": d.get("birth_day"),
        "age_days": d.get("age_days"),
        "pre_meta_flags": d.get("pre_meta_flags", 0),
        "parent_keys": d.get("parent_keys", []),
        "inbreeding_level": d.get("inbreeding_level", 0),
        "breed": d.get("breed", ""),
    })


@app.route("/api/cat/<int:db_cat_id>/prompt")
def api_cat_prompt(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    row = db.get_cat(db_cat_id)
    if not row:
        return jsonify({"error": "Кот не найден"}), 404

    cat = _cat_data_from_row(row)
    summary = build_cat_summary(cat, lang='en')
    # Generate AI prompt for preview
    ai_prompt = generate_visual_prompt(summary)
    fallback = build_prompt(cat)
    return jsonify({
        "prompt": ai_prompt or fallback,
        "fallback_prompt": fallback,
        "cat": summary,
        "ai_generated": ai_prompt is not None,
    })


@app.route("/api/cat/<int:db_cat_id>/generate", methods=["POST"])
def api_generate(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    if not db.can_generate(user["user_id"]):
        return jsonify({"error": f"Лимит генераций исчерпан ({db.MAX_GENERATIONS}/{db.MAX_GENERATIONS})"}), 403

    # Verify ownership
    owner_id = db.get_cat_owner_id(db_cat_id)
    if owner_id != user["user_id"]:
        return jsonify({"error": "Это не ваш кот"}), 403

    row = db.get_cat(db_cat_id)
    if not row:
        return jsonify({"error": "Кот не найден"}), 404

    cat = _cat_data_from_row(row)
    summary = build_cat_summary(cat, lang='en')

    data = request.get_json(silent=True) or {}
    if data.get("custom_prompt"):
        prompt = data["custom_prompt"]
    else:
        # Step 1: AI prompt writer generates a detailed visual prompt
        ai_prompt = generate_visual_prompt(summary)
        # Fallback to hardcoded prompt builder if AI fails
        prompt = ai_prompt or build_prompt(cat)

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        image_model = get_image_model()
        response = client.models.generate_content(
            model=image_model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"

                ext = "png"
                if "jpeg" in mime_type or "jpg" in mime_type:
                    ext = "jpg"
                elif "webp" in mime_type:
                    ext = "webp"

                filename = f"cat_{db_cat_id}_{cat.name[:20]}.{ext}"

                if row.get("image_url"):
                    storage.delete_blob(row["image_url"])

                blob_url = storage.upload_blob(filename, image_data, mime_type)

                if not blob_url:
                    gen_dir = os.path.join(os.path.dirname(__file__), "static", "generated")
                    os.makedirs(gen_dir, exist_ok=True)
                    local_path = os.path.join(gen_dir, f"cat_{db_cat_id}.{ext}")
                    with open(local_path, "wb") as f:
                        f.write(image_data)
                    blob_url = f"/static/generated/cat_{db_cat_id}.{ext}"

                db.set_cat_image(db_cat_id, blob_url)
                db.increment_generations(user["user_id"])

                return jsonify({"success": True, "image_url": blob_url})

        return jsonify({"error": "Нет изображения в ответе"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Feedback ===

@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    data = request.get_json()
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Сообщение обязательно"}), 400

    user = require_auth()
    user_id = user["user_id"] if user else None
    email = data.get("email", "")
    name = data.get("name", "")
    message = data["message"].strip()
    page_url = data.get("page_url", "")

    if not user_id and not email:
        return jsonify({"error": "Укажите email или войдите в аккаунт"}), 400

    if user and not email:
        u = db.get_user(user["user_id"])
        if u:
            email = u.get("email", "")
            name = name or u.get("name", "")

    db.create_feedback(user_id, email, name, message, page_url)
    return jsonify({"success": True})


@app.route("/api/admin/feedback")
def api_admin_feedback():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    rows = db.get_all_feedback()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "email": r.get("email", ""),
            "name": r.get("name", ""),
            "message": r["message"],
            "page_url": r.get("page_url", ""),
            "is_read": r.get("is_read", False),
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        })
    unread = db.get_unread_feedback_count()
    return jsonify({"feedback": result, "unread_count": unread})


@app.route("/api/admin/feedback/<int:fid>/read", methods=["POST"])
def api_admin_feedback_read(fid):
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    db.mark_feedback_read(fid)
    return jsonify({"success": True})


# === Admin user management ===

@app.route("/api/admin/user/<int:uid>/toggle-premium", methods=["POST"])
def api_admin_toggle_premium(uid):
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    target = db.get_user(uid)
    if not target:
        return jsonify({"error": "User not found"}), 404
    new_val = not bool(target.get("is_premium"))
    db.set_premium(uid, new_val)
    return jsonify({"success": True, "is_premium": new_val})


@app.route("/api/admin/user/<int:uid>/toggle-admin", methods=["POST"])
def api_admin_toggle_admin(uid):
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    target = db.get_user(uid)
    if not target:
        return jsonify({"error": "User not found"}), 404
    # Hardcoded admins can't be demoted
    if target.get("email", "") in db.ADMIN_EMAILS:
        return jsonify({"error": "Cannot change hardcoded admin"}), 400
    new_val = not bool(target.get("is_admin"))
    db.set_admin(uid, new_val)
    return jsonify({"success": True, "is_admin": new_val})


@app.route("/api/admin/user/<int:uid>/reset-generations", methods=["POST"])
def api_admin_reset_generations(uid):
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    db.execute("UPDATE users SET generations_count = 0 WHERE id = %s", (uid,))
    return jsonify({"success": True})


# === Likes ===

@app.route("/api/cat/<int:db_cat_id>/like", methods=["POST"])
def api_like(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401
    try:
        liked, count = db.toggle_like(user["user_id"], db_cat_id)
        return jsonify({"success": True, "liked": liked, "like_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Publish/unpublish ===

@app.route("/api/cat/<int:db_cat_id>/publish", methods=["POST"])
def api_publish(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    owner_id = db.get_cat_owner_id(db_cat_id)
    if owner_id != user["user_id"]:
        return jsonify({"error": "Это не ваш кот"}), 403

    row = db.get_cat(db_cat_id)
    if not row or not row.get("image_url"):
        return jsonify({"error": "Сначала сгенерируйте изображение"}), 400

    try:
        db.publish_cat(db_cat_id)
    except Exception as e:
        return jsonify({"error": f"DB error: {e}"}), 500
    return jsonify({"success": True, "published": True})


@app.route("/api/cat/<int:db_cat_id>/unpublish", methods=["POST"])
def api_unpublish(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    owner_id = db.get_cat_owner_id(db_cat_id)
    if owner_id != user["user_id"]:
        return jsonify({"error": "Это не ваш кот"}), 403

    try:
        db.unpublish_cat(db_cat_id)
    except Exception as e:
        return jsonify({"error": f"DB error: {e}"}), 500
    return jsonify({"success": True, "published": False})


# === Admin ===

@app.route("/admin")
def admin_page():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return redirect("/")
    return render_template("admin.html")


@app.route("/api/admin/check")
def api_admin_check():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"is_admin": False}), 403
    return jsonify({"is_admin": True})


@app.route("/api/admin/analytics")
def api_admin_analytics():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    stats = db.get_analytics()
    # Serialize top_users and recent_images
    stats["top_users"] = [dict(r) for r in stats["top_users"]]
    stats["recent_images"] = [dict(r) for r in stats["recent_images"]]
    return jsonify(stats)


@app.route("/api/admin/prompts")
def api_admin_get_prompts():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({
        "system_instruction": get_system_instruction(),
        "user_prompt_template": get_user_prompt_template(),
        "prompt_model": get_prompt_model(),
        "image_model": get_image_model(),
        "defaults": {
            "system_instruction": DEFAULT_SYSTEM_INSTRUCTION,
            "user_prompt_template": DEFAULT_USER_PROMPT_TEMPLATE,
            "prompt_model": PROMPT_MODEL,
            "image_model": "gemini-3.1-flash-image-preview",
        }
    })


@app.route("/api/admin/prompts", methods=["POST"])
def api_admin_save_prompts():
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    saved = []
    if "system_instruction" in data:
        val = data["system_instruction"].strip()
        if val and val != DEFAULT_SYSTEM_INSTRUCTION:
            db.set_setting(SETTING_SYSTEM_INSTRUCTION, val)
        elif not val or val == DEFAULT_SYSTEM_INSTRUCTION:
            db.execute("DELETE FROM settings WHERE key = %s", (SETTING_SYSTEM_INSTRUCTION,))
        saved.append("system_instruction")

    if "user_prompt_template" in data:
        val = data["user_prompt_template"].strip()
        if val and val != DEFAULT_USER_PROMPT_TEMPLATE:
            db.set_setting(SETTING_USER_PROMPT_TEMPLATE, val)
        elif not val or val == DEFAULT_USER_PROMPT_TEMPLATE:
            db.execute("DELETE FROM settings WHERE key = %s", (SETTING_USER_PROMPT_TEMPLATE,))
        saved.append("user_prompt_template")

    if "prompt_model" in data:
        val = data["prompt_model"].strip()
        if val and val != PROMPT_MODEL:
            db.set_setting(SETTING_PROMPT_MODEL, val)
        elif not val or val == PROMPT_MODEL:
            db.execute("DELETE FROM settings WHERE key = %s", (SETTING_PROMPT_MODEL,))
        saved.append("prompt_model")

    if "image_model" in data:
        val = data["image_model"].strip()
        if val:
            db.set_setting(SETTING_IMAGE_MODEL, val)
        saved.append("image_model")

    return jsonify({"success": True, "saved": saved})


@app.route("/api/admin/preview-cat-data/<int:db_cat_id>")
def api_admin_preview_cat_data(db_cat_id):
    """Preview the data that gets sent to the prompt writer for a specific cat."""
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403

    row = db.get_cat(db_cat_id)
    if not row:
        return jsonify({"error": "Cat not found"}), 404

    cat = _cat_data_from_row(row)
    summary = build_cat_summary(cat, lang='en')
    data_text = _build_cat_data_text(summary)

    user_template = get_user_prompt_template()
    full_user_prompt = user_template.replace("{cat_data}", data_text)

    return jsonify({
        "cat_name": cat.name,
        "cat_class": cat.cat_class,
        "data_text": data_text,
        "full_user_prompt": full_user_prompt,
        "system_instruction_preview": get_system_instruction()[:500] + "...",
        "prompt_model": get_prompt_model(),
        "image_model": get_image_model(),
    })


@app.route("/api/admin/test-prompt-writer", methods=["POST"])
def api_admin_test_prompt_writer():
    """Run prompt writer with custom system instruction / user prompt. Returns the visual prompt text."""
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    system_instruction = data.get("system_instruction", "")
    user_prompt = data.get("user_prompt", "")
    model = data.get("model", get_prompt_model())

    if not system_instruction or not user_prompt:
        return jsonify({"error": "system_instruction and user_prompt required"}), 400

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=8000,
                temperature=0.85,
                top_p=0.92,
            ),
        )
        if response and response.text:
            return jsonify({"success": True, "visual_prompt": response.text.strip()})
        return jsonify({"error": "Empty response from model"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/test-image-gen", methods=["POST"])
def api_admin_test_image_gen():
    """Generate image from a given visual prompt. Returns base64 image data."""
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    visual_prompt = data.get("visual_prompt", "")
    model = data.get("model", get_image_model())

    if not visual_prompt:
        return jsonify({"error": "visual_prompt required"}), 400

    try:
        import base64
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=visual_prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                mime = part.inline_data.mime_type or "image/png"
                return jsonify({
                    "success": True,
                    "image_base64": img_b64,
                    "mime_type": mime,
                })
        return jsonify({"error": "No image in response"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/cats-list")
def api_admin_cats_list():
    """Get all cats across all users for admin cat selector."""
    user = require_auth()
    if not user or not db.is_admin(user["user_id"]):
        return jsonify({"error": "Forbidden"}), 403

    rows = db.query("""
        SELECT c.id, c.name, c.image_url,
               (c.data->>'cat_class') as cat_class,
               u.name as owner_name
        FROM cats c
        JOIN saves s ON c.save_id = s.id
        JOIN users u ON s.user_id = u.id
        ORDER BY c.id DESC LIMIT 500
    """)
    return jsonify([dict(r) for r in rows])


# === DB init ===

try:
    db.init_db()
except Exception as e:
    print(f"init_db error: {e}")


@app.route("/api/migrate")
def api_migrate():
    """One-time migration endpoint."""
    try:
        db.init_db()

        # Grant premium to founders
        for email in ["pafa0712@gmail.com", "insaneramzes@gmail.com"]:
            db.set_premium_by_email(email, True)

        cols = db.query("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users'
        """)
        col_names = [r["column_name"] for r in cols]

        premium_users = db.query("SELECT id, name, email, is_premium FROM users WHERE is_premium = TRUE")

        return jsonify({
            "ok": True,
            "users_columns": col_names,
            "premium_users": [dict(r) for r in premium_users],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    try:
        db.init_db()
        print("Database initialized")
    except Exception as e:
        print(f"DB init failed: {e}")

    os.makedirs(os.path.join(os.path.dirname(__file__), "static", "generated"), exist_ok=True)
    app.run(debug=True, port=5000)
