import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configurações da API Backend
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

@app.route("/")
def index():
    """Página principal do frontend."""
    return render_template("index.html")

@app.route("/documents", methods=["GET"])
def list_documents():
    """Proxy para listar documentos."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route("/documents/<filename>", methods=["DELETE"])
def delete_document(filename):
    """Proxy para deletar um documento."""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{filename}", timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route("/health")
def health():
    """Verifica a saúde do backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload():
    """Proxy para o endpoint de upload do backend."""
    print("DEBUG: Recebido pedido de upload no Flask")
    if "files" not in request.files:
        print("DEBUG: Nenhum arquivo encontrado em request.files")
        return jsonify({"detail": "Nenhum arquivo enviado"}), 400
    
    files = request.files.getlist("files")
    print(f"DEBUG: Processando {len(files)} arquivos")
    
    upload_files = []
    for f in files:
        print(f"DEBUG: Lendo arquivo: {f.filename}")
        upload_files.append(("files", (f.filename, f.read(), f.content_type)))
    
    try:
        print(f"DEBUG: Enviando para o backend: {API_BASE_URL}/documents")
        response = requests.post(
            f"{API_BASE_URL}/documents",
            files=upload_files,
            timeout=120
        )
        print(f"DEBUG: Resposta do backend: {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"DEBUG: Erro no relay: {str(e)}")
        return jsonify({"detail": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask():
    """Proxy para o endpoint de pergunta do backend."""
    data = request.json
    try:
        response = requests.post(
            f"{API_BASE_URL}/question",
            json=data,
            timeout=90
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
