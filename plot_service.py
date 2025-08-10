# -*- coding: utf-8 -*-
import os
import io
import re
import base64
import numpy as np
import sympy as sp

# usar backend sin X para servidores
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))


def _fig_to_data_url():
    """Convierte la figura actual de matplotlib a data URL base64."""
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=160)
    plt.close()
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/plot", methods=["POST"])
def plot():
    """
    Body: { "prompt": "Grafica y = x**2" }
    """
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").lower()

    x = np.linspace(-10, 10, 600)
    y = np.sin(x)
    title = "y = sin(x)"
    explanation = "Ejemplo. Pide otra función: 'Grafica y = x**2'."

    try:
        if "x^2" in prompt or "x²" in prompt:
            y = x ** 2
            title = "y = x²"
            explanation = "Parábola y = x²."
        elif "cos" in prompt:
            y = np.cos(x)
            title = "y = cos(x)"
            explanation = "Función coseno."
        elif "exp" in prompt or "e^x" in prompt:
            y = np.exp(x)
            title = "y = exp(x)"
            explanation = "Función exponencial."
        elif "log" in prompt:
            mask = x > 0
            y = np.log(x[mask])
            x = x[mask]
            title = "y = log(x)"
            explanation = "Función logaritmo natural."
        elif "tan" in prompt:
            y = np.tan(x)
            title = "y = tan(x)"
            explanation = "Función tangente."
        elif "y =" in prompt or "grafic" in prompt or "grafica" in prompt or "gráfico" in prompt:
            # intenta extraer la parte 'y = ...'
            m = re.search(r"y\s*=\s*(.+)$", prompt)
            eq = m.group(1).strip() if m else prompt.split("y =")[-1].strip()
            x_sp = sp.symbols("x")
            y_sp = sp.lambdify(x_sp, sp.sympify(eq), modules="numpy")
            y = y_sp(x)
            title = f"y = {eq}"
            explanation = f"Gráfico automático de y = {eq}"

        plt.figure(figsize=(6, 3.6))
        plt.plot(x, y)
        plt.title(title)
        plt.xlabel("x")
        plt.ylabel("y")
        plt.grid(True)

        img_b64 = _fig_to_data_url()
        return jsonify({"url": img_b64, "explanation": explanation})
    except Exception as e:
        return jsonify({"url": "", "explanation": f"Error: {str(e)}"}), 400


@app.route("/histogram", methods=["POST"])
def histogram():
    """
    Body: { "values": [1,2,3] }  ó  { "text": "1, 2, 3, 4" }
    """
    data = request.get_json(force=True, silent=True) or {}
    values = data.get("values", [])

    if not values:
        text = data.get("text", "")
        try:
            values = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", text)))
        except Exception:
            return jsonify({"url": "", "explanation": "No se pudo extraer datos."}), 400

    try:
        plt.figure(figsize=(6, 3.6))
        plt.hist(values, bins="auto")
        plt.title("Histograma de datos")
        plt.xlabel("Valor")
        plt.ylabel("Frecuencia")
        plt.grid(True)

        img_b64 = _fig_to_data_url()
        return jsonify({"url": img_b64, "explanation": "Histograma generado."})
    except Exception as e:
        return jsonify({"url": "", "explanation": f"Error: {str(e)}"}), 400


@app.route("/bars", methods=["POST"])
def bars():
    """
    Body: { "labels": ["A","B"], "values": [10,20] }
    """
    data = request.get_json(force=True, silent=True) or {}
    labels = data.get("labels", [])
    values = data.get("values", [])

    if not values:
        return jsonify({"url": "", "explanation": "Debes enviar los valores."}), 400

    try:
        plt.figure(figsize=(6, 3.6))
        plt.bar(labels if labels else range(len(values)), values)
        plt.title("Gráfico de barras")

        img_b64 = _fig_to_data_url()
        return jsonify({"url": img_b64, "explanation": "Gráfico de barras generado."})
    except Exception as e:
        return jsonify({"url": "", "explanation": f"Error: {str(e)}"}), 400


@app.route("/pie", methods=["POST"])
def pie():
    """
    Body: { "labels": ["A","B"], "values": [60,40] }
    """
    data = request.get_json(force=True, silent=True) or {}
    labels = data.get("labels", [])
    values = data.get("values", [])

    if not values:
        return jsonify({"url": "", "explanation": "Debes enviar los valores."}), 400

    try:
        plt.figure(figsize=(6, 3.6))
        plt.pie(values, labels=labels if labels else None, autopct="%1.1f%%", startangle=140)
        plt.title("Gráfico de torta")

        img_b64 = _fig_to_data_url()
        return jsonify({"url": img_b64, "explanation": "Gráfico de torta generado."})
    except Exception as e:
        return jsonify({"url": "", "explanation": f"Error: {str(e)}"}), 400


@app.route("/solve", methods=["POST"])
def solve_equation():
    """
    Body: { "equation": "x**2 - 4" }
    Resuelve para x la ecuación x**2 - 4 = 0
    """
    data = request.get_json(force=True, silent=True) or {}
    eq_str = (data.get("equation") or "").strip()
    if not eq_str:
        return jsonify({"error": "Debes enviar 'equation'."}), 400

    try:
        x = sp.symbols("x")
        eq = sp.sympify(eq_str)
        solutions = sp.solve(sp.Eq(eq, 0), x)
        return jsonify({
            "solution": [str(s) for s in solutions],
            "explanation": f"Soluciones de {eq_str} = 0: {solutions}"
        })
    except Exception as e:
        return jsonify({"solution": [], "explanation": f"No se pudo resolver: {str(e)}"}), 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
