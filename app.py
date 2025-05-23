from flask import Flask, request, render_template, redirect, send_file, url_for, flash, send_from_directory,jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from werkzeug.utils import secure_filename
from dell_support import load_service_tags, get_token, get_warranty, save_warranty_to_csv
import razorpay
from flask_cors import CORS

# Get the directory where app.py is located
base_dir = os.path.dirname(os.path.abspath(__file__))
# Load the .env file from that directory

from dotenv import load_dotenv
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(override=True)


app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'

# Clerk Configuration
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
CLERK_PUBLISHABLE_KEY = os.environ.get('CLERK_PUBLISHABLE_KEY')
CLERK_API_URL = "https://api.clerk.dev/v1"

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
# RAZORPAY_KEY_ID = "rzp_test_jMpRm1HDX5ZT4x"
# RAZORPAY_KEY_SECRET = "PERAVYmOCKh4ZygDuRzEJWzi"




# Debug environment variables
print(f"Current working directory: {os.getcwd()}")
print(f"Loading .env from: {dotenv_path}")
print(f"RAZORPAY_KEY_SECRET  from env: {RAZORPAY_KEY_SECRET}")

rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

limiter = Limiter(get_remote_address, app=app, default_limits=["100 per day", "100 per minute"])


@app.errorhandler(429)
def ratelimit_handler(e):
    flash("You’ve reached the free limit. Please buy a license to continue.")
    return redirect(url_for("pricing"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("tags_file")
        if not file or not file.filename.endswith(".txt"):
            return render_template("upload.html", error="Please upload a valid .txt file.")

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # Step 1: Load tags from uploaded file
            tags = load_service_tags(filepath)

            # Enforce license check
            if len(tags) > 5:
                return render_template("upload.html", error="Please buy a license to check more than 5 service tags.")

            # Step 2: Get OAuth token
            token = get_token()

            # Step 3: Fetch warranty data
            data = get_warranty(tags, token)

            # Step 4: Save to CSV
            report_path = os.path.join(REPORTS_FOLDER, "warranty_report.csv")
            save_warranty_to_csv(data, report_path)

            return send_file(report_path, as_attachment=True)

        except Exception as e:
            return render_template("upload.html", error=f"Failed to generate report: {e}")

    return render_template("upload.html")




@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['REPORT_FOLDER'], filename, as_attachment=True)

@app.route("/health")

def health():
    return "OK", 200

@app.route("/")

def home():
    return render_template("home.html") 
@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")

@app.route("/pricing")

def pricing():
    return render_template("pricing_cards.html", key_id=RAZORPAY_KEY_ID)

@app.route("/policies")

def policies():
    return render_template("policies.html")

@app.route("/login")

def login():
    return render_template("login.html")

@app.route('/sitemap.xml')

def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')

def robots_txt():
    return send_from_directory('static', 'robots.txt')

@app.route("/checkout")

def checkout():
    plan = request.args.get("plan", "free")
    return render_template("checkout.html", plan=plan)

@app.route("/purchase", methods=["POST"])

def purchase():
    plan = request.form.get("plan")
    # TODO: Add your payment gateway integration or license assignment here
    # For now, just redirect to pricing page with a flash message or confirmation
    flash(f"Purchase flow for {plan} plan is not implemented yet.", "info")
    return redirect(url_for("pricing"))

@app.route("/order", methods=["POST"])

def create_order():
   
        # Try to get data from JSON first, then fall back to form data
    if request.is_json:
        plan = request.json.get("plan")
    else:
        # Try to get from form data or URL parameters
        plan = request.form.get("plan") or request.args.get("plan")
    
    print(f"Creating order for plan: {plan}")
    amounts = {"starter": 200, "pro": 150000, "enterprise": 1000000}  # in paise
    
    if not plan:
        return jsonify({"error": "No plan specified"}), 400
    
    if plan not in amounts:
        return jsonify({"error": "Invalid plan"}), 400
    
    try:
        order_data = {
            "amount": amounts[plan],
            "currency": "INR"
        }
        razorpay_order = rz_client.order.create(data=order_data)
        return jsonify({"order_id": razorpay_order['id'], "amount": amounts[plan]})
    except Exception as e:
        print(f"Razorpay error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/verify", methods=["POST"])

def verify_payment():
    data = request.json
    try:
        rz_client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })
        
        # TODO: Update user's subscription in database
        # For now, just return success
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 400



if __name__ == "__main__":
    app.run(debug=True)

