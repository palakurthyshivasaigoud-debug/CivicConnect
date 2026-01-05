import os
import random
import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from models import db, Complaint
import config
from nlp_utils import predict_category_text, analyze_sentiment, translate_text
from notifications import send_email

# Initialize app
app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
CORS(app)

# Ensure upload folder exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

def init_db():
    with app.app_context():
        db.create_all()

def gen_tracking_id():
    while True:
        tid = str(random.randint(100000, 999999))
        if not Complaint.query.filter_by(tracking_id=tid).first():
            return tid

def compute_priority(text, status):
    # urgency keywords
    priority = 0
    urgent_words = ["urgent", "emergency", "danger", "collapse", "injury", "accident"]
    for w in urgent_words:
        if w in (text or "").lower():
            priority += 5
    if status in ("Submitted", "In Progress"):
        priority += 1
    return priority

def admin_required(req):
    token = req.headers.get("X-Admin-Token") or req.args.get("admin_token")
    return token == config.ADMIN_TOKEN

# Routes

@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(config.UPLOAD_FOLDER, filename)

@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    # Supports form-data with file
    user_name = request.form.get("user_name")
    email = request.form.get("email")
    title = request.form.get("title")
    description = request.form.get("description")
    lat = request.form.get("latitude")
    lng = request.form.get("longitude")
    language = request.form.get("language") or config.DEFAULT_LANGUAGE
    image = request.files.get("image")

    filename = None
    if image:
        safe = secure_filename(image.filename)
        filename = f"{int(datetime.datetime.datetime.utcnow().timestamp())}_{safe}" if False else f"{int(datetime.datetime.utcnow().timestamp())}_{safe}"
        path = os.path.join(config.UPLOAD_FOLDER, filename)
        image.save(path)

    # Translate to English for NLP if needed
    orig_text = (title or "") + " " + (description or "")
    text_for_nlp = orig_text
    if language and language != "en":
        text_for_nlp = translate_text(orig_text, dest="en")

    category = predict_category_text(text_for_nlp)
    sentiment = analyze_sentiment(text_for_nlp)
    tracking_id = gen_tracking_id()
    status = "Submitted"
    priority = compute_priority(text_for_nlp, status)

    comp = Complaint(
        tracking_id=tracking_id,
        user_name=user_name,
        email=email,
        title=title,
        description=description,
        image_path=filename,
        category=category,
        sentiment=sentiment,
        status=status,
        priority=priority,
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
        language=language
    )
    db.session.add(comp)
    db.session.commit()

    # Notify user by email (optional)
    if email:
        subject = f"CivicConnect: Complaint Received ({tracking_id})"
        body = f"Hello {user_name or 'User'},\n\nWe received your complaint titled: {title}\nTracking ID: {tracking_id}\nStatus: {status}\n\nThank you,\nCivicConnect"
        send_email(email, subject, body)

    return jsonify({"success": True, "tracking_id": tracking_id, "status": status}), 200

@app.route("/api/complaints/<tracking_id>", methods=["GET"])
def get_complaint(tracking_id):
    comp = Complaint.query.filter_by(tracking_id=tracking_id).first()
    if not comp:
        return jsonify({"success": False, "message": "Invalid Tracking ID"}), 404
    return jsonify(comp.to_dict()), 200

@app.route("/api/complaints/user/<username>", methods=["GET"])
def get_user_complaints(username):
    comps = Complaint.query.filter_by(user_name=username).order_by(Complaint.created_at.desc()).all()
    return jsonify([c.to_dict() for c in comps]), 200

@app.route("/api/complaints/list", methods=["GET"])
def list_complaints():
    # filters: status, category
    status = request.args.get("status")
    category = request.args.get("category")
    q = Complaint.query
    if status:
        q = q.filter_by(status=status)
    if category:
        q = q.filter_by(category=category)
    comps = q.order_by(Complaint.priority.desc(), Complaint.created_at.desc()).all()
    return jsonify([c.to_dict() for c in comps]), 200

@app.route("/api/complaints/update_status/<tracking_id>", methods=["PUT", "POST"])
def update_status(tracking_id):
    if not admin_required(request):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    comp = Complaint.query.filter_by(tracking_id=tracking_id).first()
    if not comp:
        return jsonify({"success": False, "message": "Not found"}), 404
    data = request.json or request.form
    new_status = data.get("status")
    feedback = data.get("feedback")
    rating = data.get("rating")
    if new_status:
        comp.status = new_status
    if feedback is not None:
        comp.feedback = feedback
    if rating is not None:
        try:
            comp.rating = int(rating)
        except Exception:
            comp.rating = None
    comp.priority = compute_priority((comp.title or "") + " " + (comp.description or ""), comp.status)
    db.session.commit()

    # Notify user
    if comp.email:
        subject = f"CivicConnect: Update for {comp.tracking_id}"
        body = f"Hello {comp.user_name or 'User'},\n\nYour complaint {comp.tracking_id} status is now: {comp.status}\n\nThanks,\nCivicConnect"
        send_email(comp.email, subject, body)

    return jsonify({"success": True, "message": "Updated", "tracking_id": tracking_id}), 200

@app.route("/api/stats", methods=["GET"])
def stats():
    total = Complaint.query.count()
    by_status = {}
    for s, count in db.session.query(Complaint.status, db.func.count(Complaint.id)).group_by(Complaint.status).all():
        by_status[s] = count
    by_category = {}
    for c, count in db.session.query(Complaint.category, db.func.count(Complaint.id)).group_by(Complaint.category).all():
        by_category[c] = count
    avg_rating = db.session.query(db.func.avg(Complaint.rating)).scalar() or 0
    return jsonify({"total": total, "by_status": by_status, "by_category": by_category, "avg_rating": float(avg_rating)}), 200

@app.route("/api/translate", methods=["POST"])
def translate_route():
    data = request.json or {}
    text = data.get("text", "")
    dest = data.get("dest", "en")
    res = translate_text(text, dest=dest)
    return jsonify({"translated": res}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
