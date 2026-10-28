"""A small CRUD expense tracker backed by MySQL."""

import os
from datetime import date
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "local-development-key-change-me")


def get_connection():
    """Open a fresh connection using environment-based settings."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "0069"),
        database=os.getenv("DB_NAME", "expense_tracker_db"),
    )


def read_expense_form():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    spent_on = request.form.get("spent_on", "").strip()
    raw_amount = request.form.get("amount", "").strip()
    errors = []
    if not title or len(title) > 100:
        errors.append("Enter a title (1–100 characters).")
    if not category or len(category) > 50:
        errors.append("Enter a category (1–50 characters).")
    try:
        amount = Decimal(raw_amount)
        if not amount.is_finite() or amount <= 0 or amount > Decimal("999999999.99"):
            raise InvalidOperation
        amount = amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        amount = None
        errors.append("Enter a positive amount with at most two decimal places.")
    try:
        parsed_date = date.fromisoformat(spent_on)
    except ValueError:
        parsed_date = None
        errors.append("Choose a valid date.")
    if parsed_date and parsed_date.isoformat() != spent_on:
        errors.append("Choose a valid date.")
    return {"title": title, "category": category, "amount": amount, "spent_on": spent_on}, errors


@app.get("/")
def index():
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, title, category, amount, spent_on FROM expenses ORDER BY spent_on DESC, id DESC")
            expenses = cursor.fetchall()
            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
            total = cursor.fetchone()["total"]
            cursor.close()
        return render_template("index.html", expenses=expenses, total=total, today=date.today().isoformat())
    except Error:
        app.logger.exception("Could not read expenses from MySQL")
        return render_template("error.html"), 503


@app.post("/expenses")
def create_expense():
    values, errors = read_expense_form()
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("index"))
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (title, category, amount, spent_on) VALUES (%s, %s, %s, %s)",
                (values["title"], values["category"], values["amount"], values["spent_on"]),
            )
            conn.commit()
            cursor.close()
        flash("Expense added.", "success")
    except Error:
        app.logger.exception("Could not add expense")
        flash("Could not save the expense. Check the database connection and try again.", "error")
    return redirect(url_for("index"))


@app.post("/expenses/<int:expense_id>/update")
def update_expense(expense_id):
    values, errors = read_expense_form()
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("index"))
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE expenses SET title=%s, category=%s, amount=%s, spent_on=%s WHERE id=%s",
                (values["title"], values["category"], values["amount"], values["spent_on"], expense_id),
            )
            conn.commit()
            changed = cursor.rowcount
            cursor.close()
        flash("Expense updated." if changed else "Expense not found.", "success" if changed else "error")
    except Error:
        app.logger.exception("Could not update expense")
        flash("Could not update the expense. Check the database connection and try again.", "error")
    return redirect(url_for("index"))


@app.post("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
            conn.commit()
            removed = cursor.rowcount
            cursor.close()
        flash("Expense deleted." if removed else "Expense not found.", "success" if removed else "error")
    except Error:
        app.logger.exception("Could not delete expense")
        flash("Could not delete the expense. Check the database connection and try again.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
