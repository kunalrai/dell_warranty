from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from dell_support import load_service_tags, get_token, get_warranty, save_warranty_to_csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

def process_tags_to_csv(tag_file, output_csv):
    tags = load_service_tags(tag_file)
    token = get_token()
    warranty_data = get_warranty(tags, token)
    save_warranty_to_csv(warranty_data, output_csv)

@app.route("/", methods=["GET", "POST"])
def index():
    download_url = None
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".txt"):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            report_filename = filename.replace(".txt", ".csv")
            report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)

            try:
                process_tags_to_csv(upload_path, report_path)
                flash("✅ Warranty report generated!")
                download_url = url_for('download_file', filename=report_filename)
            except Exception as e:
                flash(f"❌ Error: {str(e)}")
        else:
            flash("⚠️ Please upload a valid .txt file.")
    return render_template("index.html", download_url=download_url)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['REPORT_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
