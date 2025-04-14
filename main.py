import pdfplumber
import csv
import io
import os
import re
from flask import Flask, request, send_file

app = Flask(__name__)

def extract_student_id(cell):
    match = re.search(r'\b\d{5,}\b', cell)
    return match.group(0) if match else None

@app.route("/", methods=["POST"])
def extract_final_grades():
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400

    pdf_file = request.files['file']

    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Nom", "Note"])  # ⬅️ Seulement deux colonnes

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        row = [cell.strip() if cell else "" for cell in row]

                        # Trouver l'ID étudiant
                        student_id = None
                        for cell in row:
                            student_id = extract_student_id(cell)
                            if student_id:
                                break
                        if not student_id:
                            continue

                        # Trouver la note (chiffre à la fin de la ligne)
                        note = ""
                        for cell in reversed(row):
                            if re.match(r"^\d+([.,]\d+)?$", cell):
                                note = cell.replace(',', '.')
                                break

                        writer.writerow([student_id, note])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='notes.csv'
        )

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))