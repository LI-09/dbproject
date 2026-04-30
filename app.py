import os
from datetime import date, timedelta

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------
# App and database configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Store the SQLite file in the same directory as this script.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'library.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "cs348-library"   # needed for flash messages (used in later steps)

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models  (Stage 2 requirement: S2-A — database design with PKs and FKs)
# ---------------------------------------------------------------------------

class Book(db.Model):
    __tablename__ = "books"

    book_id = db.Column(db.Integer, primary_key=True)
    # index=True → ix_books_title: supports ORDER BY books.title in _load_form_choices(),
    # which runs on every Add Loan and Edit Loan page load to build the book dropdown.
    title   = db.Column(db.Text, nullable=False, index=True)
    author  = db.Column(db.Text, nullable=False)
    # index=True → ix_books_genre: supports (1) SELECT DISTINCT genre FROM books ORDER BY genre
    # that populates the genre dropdown on every Report page load, and (2) the WHERE books.genre = ?
    # filter in the Report filtered query.
    genre   = db.Column(db.Text, nullable=False, index=True)
    isbn    = db.Column(db.Text)

    # One book can appear in many loans.
    loans = db.relationship("Loan", backref="book", lazy=True)

    def __repr__(self):
        return f"<Book {self.book_id}: {self.title}>"


class Member(db.Model):
    __tablename__ = "members"

    member_id = db.Column(db.Integer, primary_key=True)
    # index=True → ix_members_name: supports ORDER BY members.name in both
    # _load_form_choices() (every Add/Edit Loan form) and the Report member dropdown —
    # the most frequently executed query in the app.
    name      = db.Column(db.Text, nullable=False, index=True)
    email     = db.Column(db.Text, nullable=False)
    phone     = db.Column(db.Text)

    # One member can have many loans.
    loans = db.relationship("Loan", backref="member", lazy=True)

    def __repr__(self):
        return f"<Member {self.member_id}: {self.name}>"


class Loan(db.Model):
    """
    Main table for Requirement 1 (add / edit / delete).

    Status is intentionally NOT stored as a column because it is fully
    derivable from return_date and due_date.  Storing it would risk
    inconsistency.  Use the `status` property instead.
    """
    __tablename__ = "loans"

    loan_id     = db.Column(db.Integer, primary_key=True)
    # index=True → ix_loans_book_id: SQLite does NOT auto-index FK columns.
    # This index supports the JOIN loans→books in the Main Loan Listing (GET /)
    # and in the Report filtered query (GET /report).
    book_id     = db.Column(db.Integer, db.ForeignKey("books.book_id"),     nullable=False, index=True)
    # index=True → ix_loans_member_id: supports (1) the JOIN loans→members in the Main
    # Loan Listing and Report, and (2) WHERE loans.member_id = ? when the user applies
    # the member filter in the Report.
    member_id   = db.Column(db.Integer, db.ForeignKey("members.member_id"), nullable=False, index=True)
    # index=True → ix_loans_loan_date: supports (1) ORDER BY loans.loan_date DESC in both
    # the Main Loan Listing and the Report (eliminates a full-table sort), and (2) the
    # WHERE loans.loan_date >= ? / <= ? date-range filter in the Report.
    loan_date   = db.Column(db.Date,    nullable=False, index=True)
    due_date    = db.Column(db.Date,    nullable=False)
    return_date = db.Column(db.Date,    nullable=True)   # NULL = not yet returned

    @property
    def status(self):
        """Derive loan status at runtime — no redundant stored column."""
        if self.return_date is not None:
            return "returned"
        if self.due_date < date.today():
            return "overdue"
        return "active"

    def __repr__(self):
        return f"<Loan {self.loan_id}>"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    loans = (
        Loan.query
        .join(Book)
        .join(Member)
        .order_by(Loan.loan_date.desc())
        .all()
    )
    return render_template("index.html", loans=loans)


# ---------------------------------------------------------------------------
# Requirement 1 — Add / Edit / Delete Loans
# (S2-B, S2-C, S2-D, S2-E, S2-J, S2-K)
# ---------------------------------------------------------------------------

def _load_form_choices():
    """
    Query Books and Members from the database to populate the form dropdowns.
    This is the dynamic DB-driven UI population required by S2-J and S2-K.
    """
    books   = Book.query.order_by(Book.title).all()
    members = Member.query.order_by(Member.name).all()
    return books, members


@app.route("/loans/add", methods=["GET", "POST"])
def loan_add():
    books, members = _load_form_choices()

    if request.method == "POST":
        book_id        = request.form.get("book_id",   type=int)
        member_id      = request.form.get("member_id", type=int)
        loan_date_str  = request.form.get("loan_date")
        due_date_str   = request.form.get("due_date")

        if not all([book_id, member_id, loan_date_str, due_date_str]):
            flash("All fields are required.", "danger")
            return render_template("loan_form.html", loan=None,
                                   books=books, members=members)

        loan_date = date.fromisoformat(loan_date_str)
        due_date  = date.fromisoformat(due_date_str)

        if due_date < loan_date:
            flash("Due date cannot be before the loan date.", "danger")
            return render_template("loan_form.html", loan=None,
                                   books=books, members=members)

        new_loan = Loan(book_id=book_id, member_id=member_id,
                        loan_date=loan_date, due_date=due_date)
        db.session.add(new_loan)
        db.session.commit()
        flash("Loan added successfully.", "success")
        return redirect(url_for("index"))

    # Sensible defaults: loan starts today, due in 14 days.
    today = date.today()
    return render_template("loan_form.html", loan=None,
                           books=books, members=members,
                           default_loan_date=today,
                           default_due_date=today + timedelta(days=14))


@app.route("/loans/<int:loan_id>/edit", methods=["GET", "POST"])
def loan_edit(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    books, members = _load_form_choices()

    if request.method == "POST":
        book_id         = request.form.get("book_id",     type=int)
        member_id       = request.form.get("member_id",   type=int)
        loan_date_str   = request.form.get("loan_date")
        due_date_str    = request.form.get("due_date")
        return_date_str = request.form.get("return_date") or None

        if not all([book_id, member_id, loan_date_str, due_date_str]):
            flash("Book, Member, Loan Date, and Due Date are required.", "danger")
            return render_template("loan_form.html", loan=loan,
                                   books=books, members=members)

        loan_date = date.fromisoformat(loan_date_str)
        due_date  = date.fromisoformat(due_date_str)

        if due_date < loan_date:
            flash("Due date cannot be before the loan date.", "danger")
            return render_template("loan_form.html", loan=loan,
                                   books=books, members=members)

        loan.book_id     = book_id
        loan.member_id   = member_id
        loan.loan_date   = loan_date
        loan.due_date    = due_date
        loan.return_date = (date.fromisoformat(return_date_str)
                            if return_date_str else None)

        db.session.commit()
        flash(f"Loan #{loan_id} updated successfully.", "success")
        return redirect(url_for("index"))

    return render_template("loan_form.html", loan=loan,
                           books=books, members=members)


@app.route("/loans/<int:loan_id>/delete", methods=["POST"])
def loan_delete(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    db.session.delete(loan)
    db.session.commit()
    flash(f"Loan #{loan_id} deleted.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Requirement 2 — Report with filters and statistics
# (S2-F, S2-G, S2-H, S2-I, S2-J, S2-K)
# ---------------------------------------------------------------------------

@app.route("/report")
def report():
    # ── Dynamic filter options from the DB (S2-J, S2-K) ──────────────────
    # Genre values: SELECT DISTINCT genre FROM books ORDER BY genre
    genres = [
        row[0]
        for row in db.session.query(Book.genre).distinct().order_by(Book.genre).all()
    ]
    # Member list: SELECT member_id, name FROM members ORDER BY name
    members = Member.query.order_by(Member.name).all()

    # ── Read filter parameters from URL query string ──────────────────────
    date_from_str = request.args.get("date_from") or None
    date_to_str   = request.args.get("date_to")   or None
    sel_genre     = request.args.get("genre")      or None
    sel_member_id = request.args.get("member_id",  type=int) or None
    sel_status    = request.args.get("status")     or "all"

    # ── Build the filtered query (S2-F, S2-I) ────────────────────────────
    # Start with all loans, joined to Book and Member for access to their fields.
    q = Loan.query.join(Book).join(Member).order_by(Loan.loan_date.desc())

    if date_from_str:
        q = q.filter(Loan.loan_date >= date.fromisoformat(date_from_str))
    if date_to_str:
        q = q.filter(Loan.loan_date <= date.fromisoformat(date_to_str))
    if sel_genre:
        q = q.filter(Book.genre == sel_genre)
    if sel_member_id:
        q = q.filter(Loan.member_id == sel_member_id)

    loans = q.all()

    # Status is derived (not stored), so apply that filter in Python.
    if sel_status != "all":
        loans = [l for l in loans if l.status == sel_status]

    # ── Compute statistics over the filtered result set (S2-G) ────────────
    total    = len(loans)
    returned = sum(1 for l in loans if l.status == "returned")
    active   = sum(1 for l in loans if l.status == "active")
    overdue  = sum(1 for l in loans if l.status == "overdue")
    return_rate = round(returned / total * 100, 1) if total > 0 else 0.0

    stats = {
        "total":       total,
        "returned":    returned,
        "active":      active,
        "overdue":     overdue,
        "return_rate": return_rate,
    }

    return render_template(
        "report.html",
        loans=loans,
        stats=stats,
        genres=genres,
        members=members,
        # Pass selected values back so the form re-populates after submit.
        date_from_str=date_from_str or "",
        date_to_str=date_to_str     or "",
        sel_genre=sel_genre         or "",
        sel_member_id=sel_member_id or "",
        sel_status=sel_status,
    )


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
