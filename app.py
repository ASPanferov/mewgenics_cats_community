"""Mewgenics Cat Viewer — Flask app for local dev and Vercel deployment."""

import json
import os
import tempfile

from flask import Flask, render_template, jsonify, request, redirect, make_response

from cat_parser import load_all_cats, get_save_info, CatData, CatStats
from prompt_builder import build_prompt, build_cat_summary_ru
from auth import get_google_auth_url, exchange_code, create_jwt, get_current_user
import db
import storage

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# === Helpers ===

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
        stat_focus=d.get("stat_focus", ""),
        cat_class=d.get("cat_class", "Colorless"),
        basic_attack=d.get("basic_attack", ""),
        abilities=d.get("abilities", []),
        passives=d.get("passives", []),
        items=d.get("items", []),
        mutations=d.get("mutations", {}),
        stats=stats,
        status=d.get("status", "OK"),
    )


def _cat_to_db_data(cat):
    return {
        "name": cat.name,
        "voice": cat.voice,
        "gender": cat.gender,
        "stat_focus": cat.stat_focus,
        "cat_class": cat.cat_class,
        "basic_attack": cat.basic_attack,
        "abilities": cat.abilities,
        "passives": cat.passives,
        "items": cat.items,
        "mutations": cat.mutations,
        "status": cat.status,
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
            "max_generations": db.MAX_GENERATIONS,
        }
    })


# === Pages ===

@app.route("/")
def index():
    return render_template("index.html", page="feed")


@app.route("/cabinet")
def cabinet():
    return render_template("index.html", page="cabinet")


# === Public feed API ===

@app.route("/api/feed")
def api_feed():
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 100)

    rows = db.get_published_cats(limit=limit, offset=offset)
    total = db.get_published_count()

    result = []
    for row in rows:
        cat = _cat_data_from_row(row)
        summary = build_cat_summary_ru(cat)
        summary["db_id"] = row["id"]
        summary["image_url"] = row.get("image_url")
        summary["owner_name"] = row.get("owner_name", "")
        summary["owner_avatar"] = row.get("owner_avatar", "")
        summary["published_at"] = row["published_at"].isoformat() if row.get("published_at") else None
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

    result = []
    for row in rows:
        cat = _cat_data_from_row(row)
        summary = build_cat_summary_ru(cat)
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


@app.route("/api/cat/<int:db_cat_id>/prompt")
def api_cat_prompt(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    row = db.get_cat(db_cat_id)
    if not row:
        return jsonify({"error": "Кот не найден"}), 404

    cat = _cat_data_from_row(row)
    return jsonify({"prompt": build_prompt(cat), "cat": build_cat_summary_ru(cat)})


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
    prompt = build_prompt(cat)

    data = request.get_json(silent=True) or {}
    if data.get("custom_prompt"):
        prompt = data["custom_prompt"]

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
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

    db.publish_cat(db_cat_id)
    return jsonify({"success": True, "published": True})


@app.route("/api/cat/<int:db_cat_id>/unpublish", methods=["POST"])
def api_unpublish(db_cat_id):
    user = require_auth()
    if not user:
        return jsonify({"error": "Требуется авторизация"}), 401

    owner_id = db.get_cat_owner_id(db_cat_id)
    if owner_id != user["user_id"]:
        return jsonify({"error": "Это не ваш кот"}), 403

    db.unpublish_cat(db_cat_id)
    return jsonify({"success": True, "published": False})


# === DB init ===

try:
    db.init_db()
except Exception:
    pass


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
