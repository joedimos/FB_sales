from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from sqlalchemy import or_

from src.storage.database import SessionLocal, init_db
from src.storage.models import CRMData, Lead, LeadStatus, Vehicle

app = Flask(__name__)


def serialize_lead(lead: Lead) -> dict:
    crm = lead.crm_data
    vehicle = lead.vehicle
    details = (crm.standardized_data or {}) if crm else {}
    score = lead.predicted_likelihood
    return {
        "id": lead.id,
        "crm_lead_id": crm.crm_lead_id if crm else str(lead.id),
        "crm_source": crm.crm_source if crm else "Unknown",
        "status": lead.current_status.value if lead.current_status else "new",
        "score": round(float(score) * 100) if score is not None else None,
        "customer": details.get("customer_name") or details.get("name") or f"Lead {lead.id}",
        "vehicle": " ".join(str(x) for x in [vehicle.year, vehicle.make, vehicle.model] if x) if vehicle else "Vehicle not assigned",
        "price": vehicle.price if vehicle else None,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        "message": lead.initial_message or details.get("initial_message") or "",
    }


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(Lead).count():
            return
        examples = [
            ("FB-1042", "Maya Johnson", "2023", "Honda", "CR-V", 28950, 0.91, LeadStatus.CONTACTED, "Is this still available? I can come in after work."),
            ("FB-1043", "Chris Miller", "2021", "Ford", "F-150", 34700, 0.74, LeadStatus.APPOINTMENT, "Can you send the out-the-door price?"),
            ("FB-1044", "Taylor Smith", "2022", "Toyota", "Camry", 25900, 0.58, LeadStatus.NEW, "Interested in financing options."),
            ("FB-1045", "Jordan Lee", "2020", "Chevrolet", "Equinox", 21800, 0.31, LeadStatus.STALE, "What is the mileage?"),
        ]
        for index, (crm_id, customer, year, make, model, price, score, status, message) in enumerate(examples, start=1):
            vehicle = Vehicle(vin=f"DEMO{index:013d}", make=make, model=model, year=int(year), price=price, mileage=32000 + index * 5100, days_on_lot=12 + index * 8)
            crm = CRMData(crm_lead_id=crm_id, crm_source="Facebook Marketplace", raw_data={}, standardized_data={"customer_name": customer})
            db.add_all([vehicle, crm])
            db.flush()
            db.add(Lead(crm_data_fk=crm.id, vehicle_id=vehicle.id, current_status=status, initial_message=message, predicted_likelihood=score, created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
        db.commit()
    finally:
        db.close()


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/api/leads")
def list_leads():
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "all").strip().lower()
    db = SessionLocal()
    try:
        q = db.query(Lead).join(Lead.crm_data).join(Lead.vehicle)
        if status != "all":
            try:
                q = q.filter(Lead.current_status == LeadStatus(status))
            except ValueError:
                pass
        if query:
            like = f"%{query}%"
            q = q.filter(or_(CRMData.crm_lead_id.ilike(like), Vehicle.make.ilike(like), Vehicle.model.ilike(like), Lead.initial_message.ilike(like)))
        leads = q.order_by(Lead.predicted_likelihood.desc().nullslast(), Lead.updated_at.desc()).all()
        return jsonify([serialize_lead(lead) for lead in leads])
    finally:
        db.close()


@app.get("/api/summary")
def summary():
    db = SessionLocal()
    try:
        leads = db.query(Lead).all()
        scored = [float(x.predicted_likelihood) for x in leads if x.predicted_likelihood is not None]
        return jsonify({
            "total": len(leads),
            "hot": sum(1 for score in scored if score >= .75),
            "appointments": sum(1 for lead in leads if lead.current_status in (LeadStatus.APPOINTMENT, LeadStatus.SHOWED, LeadStatus.TEST_DRIVE)),
            "won": sum(1 for lead in leads if lead.current_status == LeadStatus.WON),
            "average_score": round(sum(scored) / len(scored) * 100) if scored else 0,
        })
    finally:
        db.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    app.run(host="0.0.0.0", port=5000, debug=False)
