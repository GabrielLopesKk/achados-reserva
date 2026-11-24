"""Rotas da API e entrega do front-end estático."""
import hmac
import os
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from . import ai, images, matching, privacy
from .catalog import COLORS, ITEM_TYPES, LOCATIONS, SENSITIVE_TYPES, STATUSES
from .db import get_db

bp = Blueprint("api", __name__)


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


@bp.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify(error=err.message), err.status


@bp.app_errorhandler(413)
def too_large(_err):
    return jsonify(error="Foto muito grande. O limite é 6 MB."), 413


# ---------- helpers ----------
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def staff_required():
    expected = current_app.config["STAFF_TOKEN"]
    if not expected:
        raise ApiError("O acesso da recepção não está configurado.", 503)
    given = request.headers.get("X-Staff-Token", "")
    if not hmac.compare_digest(given.encode(), expected.encode()):
        raise ApiError("Token da recepção inválido.", 401)


def is_staff():
    try:
        staff_required()
        return True
    except ApiError:
        return False


def choice(value, allowed, label, default=None):
    value = (value or default or "").strip()
    if value not in allowed:
        raise ApiError(f"Valor inválido para {label}.")
    return value


def text(value, label, max_len, min_len=0):
    value = (value or "").strip()
    if len(value) < min_len or len(value) > max_len:
        raise ApiError(f"{label}: use de {min_len} a {max_len} caracteres.")
    return value


def past_date(value, label):
    try:
        parsed = date.fromisoformat((value or "").strip())
    except ValueError as exc:
        raise ApiError(f"{label}: use o formato AAAA-MM-DD.") from exc
    if parsed > date.today():
        raise ApiError(f"{label}: a data não pode estar no futuro.")
    return parsed.isoformat()


def serialize_item(row, staff=False):
    """Visão pública do item: nunca inclui contatos; fotos sensíveis ficam ocultas."""
    hide_photo = bool(row["sensitive"]) and not staff
    return {
        "id": row["id"], "item_type": row["item_type"], "color": row["color"],
        "marks": row["marks"], "description": row["description"],
        "location": row["location"], "found_date": row["found_date"],
        "status": row["status"], "sensitive": bool(row["sensitive"]),
        "ai_source": row["ai_source"], "created_at": row["created_at"],
        "photo_url": None if hide_photo else f"/api/photos/{row['photo']}",
    }


def visible_items():
    """Itens expiram da busca pública após VISIBILITY_DAYS; devolvidos saem da busca."""
    limit = (datetime.now(timezone.utc)
             - timedelta(days=current_app.config["VISIBILITY_DAYS"])).isoformat(timespec="seconds")
    rows = get_db().execute(
        "SELECT * FROM items WHERE status != 'returned' AND created_at >= ? ORDER BY id DESC",
        (limit,),
    ).fetchall()
    return rows


# ---------- meta & IA ----------
@bp.get("/api/meta")
def meta():
    return jsonify(types=ITEM_TYPES, colors=COLORS, locations=LOCATIONS, statuses=STATUSES)


def read_photo_upload():
    file = request.files.get("photo")
    if not file:
        raise ApiError("Envie uma foto do objeto.")
    data = file.read()
    try:
        _fmt, media_type = images.read_image(data)
    except images.InvalidImage as exc:
        raise ApiError(str(exc)) from exc
    return data, media_type


@bp.post("/api/ai/describe")
def ai_describe():
    data, media_type = read_photo_upload()
    return jsonify(ai.describe(data, media_type, current_app.config))


# ---------- itens encontrados ----------
@bp.post("/api/items")
def create_item():
    data, _ = read_photo_upload()
    form = request.form
    kind = choice(form.get("item_type"), ITEM_TYPES, "tipo", "outro")
    color = choice(form.get("color"), COLORS, "cor", "outra")
    location = choice(form.get("location"), LOCATIONS, "local")
    found = past_date(form.get("found_date"), "Data")
    marks = text(form.get("marks"), "Marcas", 200)
    description = text(form.get("description"), "Descrição", 500)
    sensitive = form.get("sensitive") == "true" or kind in SENSITIVE_TYPES
    ai_source = choice(form.get("ai_source"), ["none", "local", "anthropic"], "origem", "none")
    photo = images.save_photo(data, current_app.config["UPLOAD_DIR"])

    db = get_db()
    cur = db.execute(
        "INSERT INTO items (photo,item_type,color,marks,description,location,found_date,"
        "sensitive,ai_source,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (photo, kind, color, marks, description, location, found, int(sensitive),
         ai_source, now_iso()),
    )
    db.commit()
    row = db.execute("SELECT * FROM items WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(serialize_item(row)), 201


@bp.get("/api/items")
def list_items():
    args = request.args
    q = matching.normalize(args.get("q", "")).split()
    rows = []
    for row in visible_items():
        if args.get("type") and row["item_type"] != args["type"]:
            continue
        if args.get("color") and row["color"] != args["color"]:
            continue
        if args.get("location") and row["location"] != args["location"]:
            continue
        if args.get("status") and row["status"] != args["status"]:
            continue
        haystack = matching.normalize(f"{row['description']} {row['marks']} {row['item_type']}")
        if all(word in haystack for word in q):
            rows.append(serialize_item(row))
    return jsonify(items=rows)


def get_item_or_404(item_id):
    row = get_db().execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise ApiError("Item não encontrado.", 404)
    return row


@bp.get("/api/items/<int:item_id>")
def get_item(item_id):
    return jsonify(serialize_item(get_item_or_404(item_id), staff=is_staff()))


@bp.get("/api/photos/<name>")
def photo(name):
    row = get_db().execute("SELECT sensitive FROM items WHERE photo=?", (name,)).fetchone()
    if row is None:
        raise ApiError("Foto não encontrada.", 404)
    if row["sensitive"]:
        staff_required()  # fotos com dados pessoais só para a recepção
    return send_from_directory(current_app.config["UPLOAD_DIR"], name)


# ---------- interesse e devolução ----------
@bp.post("/api/items/<int:item_id>/claims")
def create_claim(item_id):
    item = get_item_or_404(item_id)
    if item["status"] == "returned":
        raise ApiError("Este item já foi devolvido.", 409)
    body = request.get_json(silent=True) or {}
    name = text(body.get("name"), "Nome", 80, 2)
    contact = text(body.get("contact"), "Contato", 120, 5)
    message = text(body.get("message"), "Mensagem", 300)
    code = privacy.new_secret()
    db = get_db()
    db.execute(
        "INSERT INTO claims (item_id,name,contact,message,code_hash,created_at) VALUES (?,?,?,?,?,?)",
        (item_id, name, contact, message, privacy.hash_secret(code), now_iso()),
    )
    db.execute("UPDATE items SET status='awaiting_pickup' WHERE id=?", (item_id,))
    db.commit()
    return jsonify(pickup_code=code, status="awaiting_pickup"), 201


@bp.get("/api/staff/items")
def staff_items():
    staff_required()
    rows = get_db().execute(
        "SELECT * FROM items WHERE status != 'returned' ORDER BY id DESC").fetchall()
    return jsonify(items=[serialize_item(r, staff=True) for r in rows])


@bp.get("/api/staff/items/<int:item_id>/claims")
def staff_claims(item_id):
    staff_required()
    get_item_or_404(item_id)
    rows = get_db().execute(
        "SELECT id,name,contact,message,created_at FROM claims WHERE item_id=? ORDER BY id",
        (item_id,)).fetchall()
    return jsonify(claims=[{
        "id": r["id"], "name": r["name"], "contact_masked": privacy.mask_contact(r["contact"]),
        "message": r["message"], "created_at": r["created_at"]} for r in rows])


@bp.patch("/api/items/<int:item_id>/status")
def update_status(item_id):
    staff_required()
    get_item_or_404(item_id)
    body = request.get_json(silent=True) or {}
    status = choice(body.get("status"), STATUSES, "status")
    db = get_db()
    if status == "returned":
        code = (body.get("code") or "").strip()
        claims = db.execute("SELECT code_hash FROM claims WHERE item_id=?", (item_id,)).fetchall()
        if not code or not any(privacy.same_secret(code, c["code_hash"]) for c in claims):
            raise ApiError("Código de retirada inválido.", 403)
    db.execute("UPDATE items SET status=? WHERE id=?", (status, item_id))
    db.commit()
    return jsonify(serialize_item(get_item_or_404(item_id), staff=True))


# ---------- relatos de perda ----------
@bp.post("/api/reports")
def create_report():
    body = request.get_json(silent=True) or {}
    report = {
        "description": text(body.get("description"), "Descrição", 500, 5),
        "item_type": choice(body.get("item_type"), ITEM_TYPES, "tipo", "outro"),
        "color": choice(body.get("color"), COLORS, "cor", "outra"),
        "location": choice(body.get("location"), LOCATIONS, "local"),
        "lost_date": past_date(body.get("lost_date"), "Data"),
        "contact": text(body.get("contact"), "Contato", 120, 5),
    }
    token = privacy.new_secret(8)
    db = get_db()
    cur = db.execute(
        "INSERT INTO reports (description,item_type,color,location,lost_date,contact,"
        "token_hash,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (*report.values(), privacy.hash_secret(token), now_iso()),
    )
    db.commit()
    return jsonify(id=cur.lastrowid, token=token), 201


@bp.get("/api/reports/<int:report_id>/matches")
def report_matches(report_id):
    row = get_db().execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    token = request.headers.get("X-Report-Token", "")
    if row is None or not privacy.same_secret(token, row["token_hash"]):
        raise ApiError("Relato não encontrado ou token inválido.", 404)
    items = [dict(r) for r in visible_items()]
    ranked = matching.rank(dict(row), items)
    return jsonify(candidates=[
        {"item": serialize_item(c["item"]), "score": c["score"], "reasons": c["reasons"]}
        for c in ranked], note="Sugestões automáticas: confirme com a recepção antes de retirar.")


# ---------- front-end estático ----------
@bp.get("/")
def index():
    return send_from_directory(current_app.config["FRONTEND_DIR"], "index.html")


@bp.get("/<path:filename>")
def static_files(filename):
    if filename.startswith("api/") or filename.startswith("tests/") or filename == "package.json":
        raise ApiError("Não encontrado.", 404)
    if not os.path.isfile(os.path.join(current_app.config["FRONTEND_DIR"], filename)):
        raise ApiError("Não encontrado.", 404)
    return send_from_directory(current_app.config["FRONTEND_DIR"], filename)
