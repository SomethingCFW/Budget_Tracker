# app.py
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


# App & DB setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Models
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)              # <-- amount present
    category = db.Column(db.String(100), nullable=False)
    is_income = db.Column(db.Boolean, default=False)
    account = db.Column(db.String(50), nullable=False) # <-- account (Checking/HYSA/ROTH)
    date = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"<Transaction {self.id} {self.description} {self.amount}>"


# Routes
@app.route("/")
def index():
    now = datetime.utcnow()

    # Start of current month (1st day at 00:00)
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Start of current week (Monday at 00:00)
    start_week = now - timedelta(days=now.weekday())
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Transactions lists
    month_transactions = Transaction.query.filter(Transaction.date >= start_month).order_by(Transaction.date.desc()).all()
    week_transactions = Transaction.query.filter(Transaction.date >= start_week).order_by(Transaction.date.desc()).all()

    # Summaries grouped by account (income)
    month_income_summary = db.session.query(
        Transaction.account,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.date >= start_month,
        Transaction.is_income == True
    ).group_by(Transaction.account).all()

    week_income_summary = db.session.query(
        Transaction.account,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.date >= start_week,
        Transaction.is_income == True
    ).group_by(Transaction.account).all()

    # Summaries grouped by account (expense)
    month_expense_summary = db.session.query(
        Transaction.account,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.date >= start_month,
        Transaction.is_income == False
    ).group_by(Transaction.account).all()

    week_expense_summary = db.session.query(
        Transaction.account,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).filter(
        Transaction.date >= start_week,
        Transaction.is_income == False
    ).group_by(Transaction.account).all()

    # Totals for the month (for net calculations)
    month_income_total = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.date >= start_month, Transaction.is_income == True
    ).scalar() or 0.0

    # Expenses excluding HYSA and ROTH (so savings/roth contributions are excluded)
    month_expense_excl_savings = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.date >= start_month,
        Transaction.is_income == False,
        ~Transaction.account.in_(["HYSA", "ROTH"])
    ).scalar() or 0.0

    month_net_excluding_savings = month_income_total - month_expense_excl_savings

    # Weekly totals too
    week_income_total = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.date >= start_week, Transaction.is_income == True
    ).scalar() or 0.0

    week_expense_excl_savings = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.date >= start_week,
        Transaction.is_income == False,
        ~Transaction.account.in_(["HYSA", "ROTH"])
    ).scalar() or 0.0

    week_net_excluding_savings = week_income_total - week_expense_excl_savings

    return render_template(
        "index.html",
        month_transactions=month_transactions,
        week_transactions=week_transactions,
        month_income_summary=month_income_summary,
        week_income_summary=week_income_summary,
        month_expense_summary=month_expense_summary,
        week_expense_summary=week_expense_summary,
        month_net_excluding_savings=month_net_excluding_savings,
        week_net_excluding_savings=week_net_excluding_savings
    )

@app.route('/')
@app.route('/transactions')
def transactions():
    # Get the year and month from query params, or default to current month
    year = request.args.get('year', default=None, type=int)
    month = request.args.get('month', default=None, type=int)

    query = Transaction.query

    if year and month:
        # Filter by year and month
        query = query.filter(
            db.extract('year', Transaction.date) == year,
            db.extract('month', Transaction.date) == month
        )
    transactions = query.order_by(Transaction.date.desc()).all()

    return render_template('transaction.html', transactions=transactions)


@app.route("/add", methods=["POST"])
def add_transaction():
    # read form fields (amount is required)
    description = request.form.get("description", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "Uncategorized").strip()
    account = request.form.get("account", "Checking").strip()
    is_income = True if request.form.get("is_income") == "on" else False

# simple validation
    try:
        amount = float(amount_raw)
    except Exception:
        return "Invalid amount", 400

    tx = Transaction(
        description=description or "No description",
        amount=amount,
        category=category or "Uncategorized",
        account=account or "Checking",
        is_income=is_income
    )
    db.session.add(tx)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:tx_id>", methods=["POST", "GET"])
def delete_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    db.session.delete(tx)
    db.session.commit()
    return redirect(url_for("index"))


# Create tables & run
if __name__ == "__main__":
    # make sure instance folder exists (Flask often uses instance/ for sqlite)
    instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    with app.app_context():
        db.create_all()   # create tables if they don't exist

    app.run(host="0.0.0.0", port=5000, debug=True)