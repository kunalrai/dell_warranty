from flask import Flask, request, render_template, redirect, send_file, url_for, flash, send_from_directory, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import plotly.express as px
import plotly.utils
import pandas as pd
from datetime import datetime, timedelta
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


# Define folders first
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warranty.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db = SQLAlchemy(app)

# Model definition
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_tag = db.Column(db.String(80), unique=True, nullable=False)
    model = db.Column(db.String(120))
    warranty_type = db.Column(db.String(80))
    warranty_start = db.Column(db.DateTime)
    warranty_end = db.Column(db.DateTime)
    service_level = db.Column(db.String(80))
    location = db.Column(db.String(120))
    cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Import data from CSV to database
def import_csv_to_db(csv_path):
    df = pd.read_csv(csv_path)
    
    # Convert date strings to datetime
    df['StartDate'] = pd.to_datetime(df['StartDate'], format='%d-%b-%Y')
    df['EndDate'] = pd.to_datetime(df['EndDate'], format='%d-%b-%Y')
    
    # Clear existing data
    Asset.query.delete()
    
    # Import new data
    for _, row in df.iterrows():
        asset = Asset(
            service_tag=row['ServiceTag'],
            model=row['Model'],
            warranty_type=row['EntitlementType'],
            warranty_start=row['StartDate'],
            warranty_end=row['EndDate'],
            service_level=row['ServiceLevelCode'],
        )
        db.session.add(asset)
    
    db.session.commit()

# Create database tables
with app.app_context():
    db.create_all()

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

limiter = Limiter(get_remote_address, app=app, default_limits=["1000 per day", "1000 per minute"])


@app.errorhandler(429)
def ratelimit_handler(e):
    flash("You’ve reached the free limit. Please buy a license to continue.")
    return redirect(url_for("pricing"))

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
            if len(tags) > 100:
                return render_template("upload.html", error="Please buy a license to check more than 100 service tags.")

            # Step 2: Get OAuth token
            token = get_token()

            # Step 3: Fetch warranty data
            data = get_warranty(tags, token)            # Step 4: Save to CSV and database
            report_path = os.path.join(REPORTS_FOLDER, "warranty_report.csv")
            save_warranty_to_csv(data, report_path)
              # Import the data into the database
            import_csv_to_db(report_path)

            # Redirect to dashboard instead of downloading
            flash('Data imported successfully!', 'success')
            return redirect(url_for('dashboard'))

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

@app.route('/static/sitemap.xml')

def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/static/robots.txt')

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
    amounts = {"starter": 2000, "pro": 150000, "enterprise": 1000000}  # in paise
    
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

# Dashboard routes
@app.route('/dashboard')
def dashboard():    # Get data from database
    assets = Asset.query.all()
    if not assets:
        flash('No warranty data available. Please upload service tags first.', 'warning')
        return redirect(url_for('upload'))

    # Convert to DataFrame for visualizations
    df = pd.DataFrame([{
        'Model': a.model,
        'EntitlementType': a.warranty_type,
        'ServiceLevelCode': a.service_level,
        'StartDate': a.warranty_start,
        'EndDate': a.warranty_end
    } for a in assets])
    
    # Get key metrics
    total_assets = len(df)
    current_date = datetime.now()
    ninety_days = current_date + timedelta(days=90)
    
    expiring_soon = len(df[
        (df['EndDate'] > pd.Timestamp(current_date)) & 
        (df['EndDate'] <= pd.Timestamp(ninety_days))
    ])
    
    expired = len(df[df['EndDate'] < pd.Timestamp(current_date)])

    # Create charts
    if not df.empty:
        # Warranty type distribution
        warranty_pie = px.pie(
            df, 
            names='EntitlementType', 
            title='Warranty Type Distribution',
            hole=0.3
        )

        # Service level distribution
        service_bar = px.bar(
            df.groupby('ServiceLevelCode').size().reset_index(name='count'),
            x='ServiceLevelCode',
            y='count',
            title='Service Level Distribution',
            color='ServiceLevelCode'
        )

        # Timeline chart
        timeline = px.timeline(
            df,
            x_start='StartDate',
            x_end='EndDate',
            y='Model',
            title='Warranty Coverage Timeline',
            color='EntitlementType'
        )
        timeline.update_layout(
            xaxis_title="Date",
            yaxis_title="Model",
            height=600
        )
    else:
        # Create empty charts if no data
        warranty_pie = px.pie(
            pd.DataFrame({'EntitlementType': ['No Data'], 'value': [1]}),
            values='value',
            names='EntitlementType',
            title='No Warranty Data Available'
        )
        service_bar = px.bar(
            pd.DataFrame({'ServiceLevelCode': ['No Data'], 'count': [0]}),
            x='ServiceLevelCode',
            y='count',
            title='No Service Level Data Available'
        )
        timeline = px.timeline(
            pd.DataFrame({
                'Model': ['No Data'],
                'StartDate': [datetime.now()],
                'EndDate': [datetime.now()]
            }),
            x_start='StartDate',
            x_end='EndDate',
            y='Model',
            title='No Timeline Data Available'
        )

    # Convert charts to JSON for template
    charts = {
        'warranty_pie': warranty_pie.to_json(),
        'service_bar': service_bar.to_json(),
        'timeline': timeline.to_json()
    }

    # Get unique models for filter
    models = df['Model'].unique().tolist() if not df.empty else []

    return render_template('dashboard.html',
                         total_assets=total_assets,
                         expiring_soon=expiring_soon,
                         expired=expired,
                         charts=charts,
                         models=models)

@app.route('/api/assets')
def get_assets():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    model_filter = request.args.get('model', '')

    # Query database
    query = Asset.query
    if model_filter:
        query = query.filter(Asset.model == model_filter)    # Get paginated data
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    if not pagination.items:
        return jsonify({
            'data': [],
            'total': 0,
            'pages': 0,
            'current_page': page
        })

    # Convert to list of dictionaries
    data = [{
        'service_tag': asset.service_tag,
        'model': asset.model,
        'warranty_type': asset.warranty_type,
        'warranty_start': asset.warranty_start.strftime('%d-%b-%Y'),
        'warranty_end': asset.warranty_end.strftime('%d-%b-%Y'),
        'service_level': asset.service_level
    } for asset in pagination.items]

    return jsonify({
        'data': data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/export-csv')
def export_csv():
    model_filter = request.args.get('model', '')
    
    # Query database
    query = Asset.query
    if model_filter:
        query = query.filter(Asset.model == model_filter)
    
    assets = query.all()
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'ServiceTag': asset.service_tag,
        'Model': asset.model,
        'EntitlementType': asset.warranty_type,
        'StartDate': asset.warranty_start.strftime('%d-%b-%Y'),
        'EndDate': asset.warranty_end.strftime('%d-%b-%Y'),
        'ServiceLevelCode': asset.service_level
    } for asset in assets])
    
    # Apply model filter if specified
    if model_filter:
        df = df[df['Model'] == model_filter]
    
    # Create a new file for export
    export_path = os.path.join(REPORTS_FOLDER, 'export.csv')
    df.to_csv(export_path, index=False)
    
    return send_file(export_path,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='warranty_export.csv')

# Background task for email alerts
def check_expiring_warranties():
    with app.app_context():
        current_date = datetime.now()
        ninety_days = current_date + timedelta(days=90)
        
        # Get assets expiring in the next 90 days
        expiring_assets = Asset.query.filter(
            Asset.warranty_end > current_date,
            Asset.warranty_end <= ninety_days
        ).all()
        
        # TODO: Implement email sending logic
        for asset in expiring_assets:
            days_remaining = (asset.warranty_end - current_date).days
            print(f"Alert: Warranty for {asset.service_tag} ({asset.model}) expires in {days_remaining} days")

# Set up scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_expiring_warranties, 'interval', days=1)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)

