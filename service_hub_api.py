from flask import Flask, jsonify, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)
DATA_FILE = "micro_service_hub.xlsx"

# Load data
def load_data():
    services = pd.read_excel(DATA_FILE, sheet_name="Services")
    bookings = pd.read_excel(DATA_FILE, sheet_name="Bookings")
    feedback = pd.read_excel(DATA_FILE, sheet_name="Feedback")
    return services, bookings, feedback

# API Endpoints (unchanged)
@app.route("/api/services", methods=["GET"])
def get_services():
    services, _, _ = load_data()
    return jsonify(services.to_dict(orient="records"))

@app.route("/api/services/available", methods=["GET"])
def get_available_services():
    services, _, _ = load_data()
    available = services[services["Availability"] == "Available"]
    return jsonify(available.to_dict(orient="records"))

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    _, bookings, _ = load_data()
    return jsonify(bookings.to_dict(orient="records"))

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    _, _, feedback = load_data()
    return jsonify(feedback.to_dict(orient="records"))

@app.route("/api/provider/<provider>/rating", methods=["GET"])
def get_provider_rating(provider):
    services, bookings, feedback = load_data()
    provider_services = services[services["Provider"] == provider]["Service_ID"]
    provider_bookings = bookings[bookings["Service_ID"].isin(provider_services)]["Booking_ID"]
    provider_feedback = feedback[feedback["Booking_ID"].isin(provider_bookings)]
    rating = provider_feedback["Rating"].mean() if not provider_feedback.empty else 0.0
    return jsonify({"provider": provider, "rating": rating})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    services, bookings, feedback = load_data()
    stats = {
        "total_services": len(services),
        "available_services": len(services[services["Availability"] == "Available"]),
        "completed_bookings": len(bookings[bookings["Status"] == "Completed"]),
        "average_rating": feedback["Rating"].mean() if not feedback.empty else 0.0
    }
    return jsonify(stats)

# Frontend Routes
@app.route("/", methods=["GET"])
def home():
    services, _, _ = load_data()
    available_services = services[services["Availability"] == "Available"]
    return render_template("front.html", section="home", services=available_services.to_dict(orient="records"))

@app.route("/book/<service_id>", methods=["GET", "POST"])
def book_service(service_id):
    services, _, _ = load_data()
    service = services[services["Service_ID"] == service_id]
    if service.empty:
        return "Service not found", 404
    if request.method == "POST":
        booking_id = request.form["booking_id"]
        client = request.form["client"]
        booking_date = request.form["booking_date"]
        completion_date = request.form["completion_date"]
        from service_hub import book_service
        result = book_service(booking_id, service_id, client, booking_date, completion_date)
        return redirect(url_for("home"))
    return render_template("front.html", section="book", service=service.iloc[0].to_dict())

@app.route("/feedback/<booking_id>", methods=["GET", "POST"])
def submit_feedback(booking_id):
    _, bookings, _ = load_data()
    booking = bookings[bookings["Booking_ID"] == booking_id]
    if booking.empty:
        return "Booking not found", 404
    if booking["Status"].iloc[0] != "Completed":
        return "Booking not completed", 400
    if request.method == "POST":
        feedback_id = request.form["feedback_id"]
        client = request.form["client"]
        rating = int(request.form["rating"])
        comment = request.form["comment"]
        from service_hub import add_feedback
        result = add_feedback(feedback_id, booking_id, client, rating, comment)
        return redirect(url_for("home"))
    return render_template("front.html", section="feedback", booking_id=booking_id)

@app.route("/stats", methods=["GET"])
def stats():
    services, bookings, feedback = load_data()
    stats = {
        "total_services": len(services),
        "available_services": len(services[services["Availability"] == "Available"]),
        "completed_bookings": len(bookings[bookings["Status"] == "Completed"]),
        "average_rating": feedback["Rating"].mean() if not feedback.empty else 0.0
    }
    return render_template("front.html", section="stats", stats=stats)

if __name__ == "__main__":
    app.run(debug=True, port=5000)