import pdfplumber
import csv
import io
import os
from flask import Flask, request, send_file

app = Flask(__name__)

@app.route("/", methods=["POST"])
def extract_tables_from_pdf():
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400

    pdf_file = request.files['file']

    try:
        all_rows = []

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        # On ne garde que les tableaux avec plusieurs colonnes significatives
                        if table and len(table[0]) >= 2:
                            for row in table:
                                if any(cell and cell.strip() for cell in row):
                                    all_rows.append(row)

        if not all_rows:
            return {"error": "No valid table rows found"}, 400

        # Création du fichier CSV en mémoire
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        for row in all_rows:
            writer.writerow(row)

        csv_file.seek(0)

        return send_file(
            io.BytesIO(csv_file.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='resultat.csv'
        )

    except Exception as e:
        return {"error": str(e)}, 500

# Port requis pour Google Cloud Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))