from flask import Flask, render_template, request, jsonify
import requests
import base64
import json
from datetime import datetime

app = Flask(__name__)

# M-Pesa API credentials (use sandbox credentials for testing)
CONSUMER_KEY = "YOUR_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"
SHORTCODE = "174379"  # Test shortcode
PASSKEY = "YOUR_PASSKEY"  # Sandbox passkey
BASE_URL = "https://sandbox.safaricom.co.ke"  # Change to live URL for production

# In-memory database for simplicity
students = []

# Function to get the access token
def get_access_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(url, headers=headers)
    access_token = response.json().get("access_token")
    return access_token

# Home route (registration form)
@app.route("/")
def home():
    return render_template("register.html")

# Registration route
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    students.append({"name": name, "email": email, "password": password})
    return render_template("login.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        for student in students:
            if student["email"] == email and student["password"] == password:
                return redirect("/payment")
        return "Invalid credentials!"
    return render_template("login.html")

# Payment page route
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if request.method == "POST":
        amount = request.form["amount"]
        phone = request.form["phone"]

        # Initiate STK Push
        access_token = get_access_token()
        url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{SHORTCODE}{PASSKEY}{timestamp}".encode()).decode()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,  # Customer's phone number
            "PartyB": SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": "https://yourdomain.com/payment/callback",  # Replace with your callback URL
            "AccountReference": "StudentAssignment",
            "TransactionDesc": "Payment for Assignment",
        }

        response = requests.post(url, headers=headers, json=payload)
        return jsonify(response.json())  # Send M-Pesa response to the browser

    return render_template("payment.html")

# Callback route to handle M-Pesa response
@app.route("/payment/callback", methods=["POST"])
def payment_callback():
    data = request.json
    print("Callback received:", data)
    # Process the callback data (e.g., save payment status to database)
    return jsonify({"ResultCode": 0, "ResultDesc": "Success"})

if __name__ == "__main__":
    app.run(debug=True)
