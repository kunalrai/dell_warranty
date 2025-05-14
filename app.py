from flask import Flask, request, render_template, redirect, send_file, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from dell_support import load_service_tags, get_token, get_warranty, save_warranty_to_csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'


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
                return render_template("upload.html", error="🔒 Please buy a license to check more than 5 service tags.")

            # Step 2: Get OAuth token
            token = get_token()

            # Step 3: Fetch warranty data
            data = get_warranty(tags, token)

            # Step 4: Save to CSV
            report_path = os.path.join(REPORTS_FOLDER, "warranty_report.csv")
            save_warranty_to_csv(data, report_path)

            return send_file(report_path, as_attachment=True)

        except Exception as e:
            return render_template("upload.html", error=f"❌ Failed to generate report: {e}")

    return render_template("upload.html")


# def process_tags_to_csv(tag_file, output_csv):
#     tags = load_service_tags(tag_file)
#     token = get_token()
#     warranty_data = get_warranty(tags, token)
#     save_warranty_to_csv(warranty_data, output_csv)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     download_url = None
#     if request.method == "POST":
#         file = request.files.get("file")
#         if file and file.filename.endswith(".txt"):
#             filename = secure_filename(file.filename)
#             upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(upload_path)

#             report_filename = filename.replace(".txt", ".csv")
#             report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)

#             try:
#                 process_tags_to_csv(upload_path, report_path)
#                 flash("✅ Warranty report generated!")
#                 download_url = url_for('download_file', filename=report_filename)
#             except Exception as e:
#                 flash(f"❌ Error: {str(e)}")
#         else:
#             flash("⚠️ Please upload a valid .txt file.")
#     return render_template("index.html", download_url=download_url)
    

# @app.route("/", methods=["GET", "POST"])
# def index():
#     return render_template("index.html")

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
    return render_template("pricing_cards.html")



if __name__ == "__main__":
    app.run(debug=True)

