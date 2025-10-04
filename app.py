from flask import Flask, render_template, request, flash, send_file
import os
from datetime import datetime
from agents import safety_analysis_tool, compliance_checker_tool, generate_hse_report, export_to_pdf_unicode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

REPORTS_DIR = os.path.join(app.root_path, "static", "reports")
UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

PDF_DIRECTIVE_PATH = os.path.join(app.root_path, "directive-cfst.pdf")

@app.route("/")
def index():
    return render_template("main.html")

@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        try:
            description = request.form.get("description")
            company_name = request.form.get("companyName", "Entreprise XYZ")
            if not description or description.strip() == "":
                flash("Veuillez remplir la description du danger.")
                return render_template("form.html")

            uploaded_file = request.files.get("photo")
            photo_path = None
            if uploaded_file and uploaded_file.filename != "":
                filename = secure_filename(uploaded_file.filename)
                photo_path = os.path.join(UPLOAD_DIR, filename)
                uploaded_file.save(photo_path)
                print(f"Photo uploadée: {photo_path}")

            # --- Analyse SafetyAgent ---
            print(f"Analyse du danger: {description} | Image: {photo_path if photo_path else 'Aucune'}")
            agent_output = safety_analysis_tool(text=description, image_path=photo_path)
            print(f"Résultat SafetyAgent: {agent_output}")

            # --- Vérification conformité ---
            print("Vérification de conformité...")
            compliance_report = compliance_checker_tool(
                agent_output=agent_output,
                pdf_path=PDF_DIRECTIVE_PATH
            )
            print(f"Rapport de conformité: {compliance_report}")

            # --- Génération rapport HSE ---
            print("Génération du rapport HSE...")
            rapport_hse = generate_hse_report(agent_output, compliance_report, company_name=company_name)
            if photo_path:
                rapport_hse += f"\n\nPhoto jointe: {photo_path}"
            print(f"Rapport généré: {len(rapport_hse)} caractères")

            # --- Création PDF ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"rapport_hse_{timestamp}.pdf"
            pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
            export_to_pdf_unicode(rapport_hse, filename=pdf_path)

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Le fichier PDF n'a pas pu être créé: {pdf_path}")

            print(f"PDF créé: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=pdf_filename,
                mimetype="application/pdf"
            )

        except Exception as e:
            print(f"Erreur: {str(e)}")
            flash(f"Erreur lors de la génération du rapport: {str(e)}")
            return render_template("form.html")

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)