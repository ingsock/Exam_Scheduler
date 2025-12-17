from flask import Flask, render_template, request, jsonify, send_file


from scheduler import Subject, calculate_penalty
from solvers import simulated_annealing, genetic_algorithm
from forms_integration import FormsManager
from export import generate_word_schedule

app = Flask(__name__)

# Global State (In-memory for simplicity, normally DB)
STATE = {
    "num_days": 20,
    "holidays": [],  # List of day indices
    "allowed_emails": [],
    "form_id": "",
    "subjects": ["Math", "Physics", "Chemistry", "Biology", "History"],
    "last_schedule": None,  # Store the Schedule object
    "last_scheduler_output": {},  # Store output like input list, etc.
    "start_date": "2025-01-01",  # Default start date
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.json
        if "num_days" in data:
            STATE["num_days"] = int(data["num_days"])
        if "holidays" in data:
            STATE["holidays"] = [int(d) for d in data["holidays"]]
        if "allowed_emails" in data:
            if isinstance(data["allowed_emails"], str):
                STATE["allowed_emails"] = [
                    e.strip() for e in data["allowed_emails"].split("\n") if e.strip()
                ]
            else:
                STATE["allowed_emails"] = data["allowed_emails"]
        if "subjects" in data:
            STATE["subjects"] = [s.strip() for s in data["subjects"] if s.strip()]
        if "form_id" in data:
            STATE["form_id"] = data["form_id"].strip()
        if "start_date" in data:
            STATE["start_date"] = data["start_date"]

        return jsonify({"status": "success", "state": STATE})
    return jsonify(STATE)


@app.route("/api/create_form", methods=["POST"])
def create_form():
    data = request.json
    title = data.get("title", "Exam Schedule Form")
    subjects = [Subject(n) for n in STATE["subjects"]]

    try:
        manager = FormsManager()
        url = manager.create_exam_form(title, subjects)
        # Extract ID from URL if possible, or user has to input it.
        # URL format: .../d/{form_id}/viewform
        # simple parsing:
        parts = url.split("/d/")
        if len(parts) > 1:
            form_id = parts[1].split("/")[0]
            STATE["form_id"] = form_id

        return jsonify(
            {"status": "success", "url": url, "form_id": STATE.get("form_id")}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/run_schedule", methods=["POST"])
def run_schedule():
    # 1. Poll Responses
    form_id = STATE["form_id"]
    if not form_id:
        return jsonify({"status": "error", "message": "No Form ID provided."}), 400

    try:
        manager = FormsManager()
        allowed_emails = (
            set(STATE["allowed_emails"]) if STATE["allowed_emails"] else None
        )
        subjects_objs = [Subject(n) for n in STATE["subjects"]]

        students = manager.fetch_and_parse(form_id, allowed_emails, subjects_objs)

        if not students:
            return jsonify(
                {"status": "error", "message": "No valid student responses found."}
            ), 400

        # 2. Run Solvers
        holidays_set = set(STATE["holidays"])
        num_days = STATE["num_days"]

        # Run Genetic Algorithm (usually faster/better in test) or SA
        # Let's run SA for speed if small, or GA.
        # User prompt said "compare... and choose highest".
        # We can run both.

        sa_schedule = simulated_annealing(
            subjects_objs, students, num_days, holidays_set
        )
        sa_penalty = calculate_penalty(sa_schedule, students)

        ga_schedule = genetic_algorithm(subjects_objs, students, num_days, holidays_set)
        ga_penalty = calculate_penalty(ga_schedule, students)

        best = sa_schedule if sa_penalty < ga_penalty else ga_schedule
        best_algo = (
            "Simulated Annealing" if sa_penalty < ga_penalty else "Genetic Algorithm"
        )

        STATE["last_schedule"] = best

        # Format for Frontend
        # List of { day: X, subject: Y }
        schedule_list = []
        for subj, day in best.assignments.items():
            schedule_list.append({"day": day, "subject": subj.name})

        return jsonify(
            {
                "status": "success",
                "algo": best_algo,
                "penalty": min(sa_penalty, ga_penalty),
                "schedule": schedule_list,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/export/word", methods=["GET"])
def export_word():
    if not STATE["last_schedule"]:
        return "No schedule generated yet.", 400

    filename = generate_word_schedule(STATE["last_schedule"], STATE["start_date"])
    if filename:
        return send_file(filename, as_attachment=True)
    else:
        return "Error generating file.", 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
