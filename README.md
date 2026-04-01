# Library Lending System — CS348 Stage 2

A minimal database-backed web application that satisfies the Stage 2
deliverables of the CS348 semester project.

**Stack:** Python · Flask · SQLite · SQLAlchemy · Jinja2 · Bootstrap 5 (CDN)

---

## Project Purpose

A library lending system where library staff can:

1. **Check out books** to members, update loan records, and delete them
   (Requirement 1 — CRUD on the main table).
2. **Run a filtered report** on loans, with live statistics that change as
   data changes (Requirement 2 — report interface).

---

## Database Schema

```
Books
  book_id   INTEGER  PRIMARY KEY (autoincrement)
  title     TEXT     NOT NULL
  author    TEXT     NOT NULL
  genre     TEXT     NOT NULL
  isbn      TEXT

Members
  member_id INTEGER  PRIMARY KEY (autoincrement)
  name      TEXT     NOT NULL
  email     TEXT     NOT NULL
  phone     TEXT

Loans                                            ← main table (Requirement 1)
  loan_id     INTEGER  PRIMARY KEY (autoincrement)
  book_id     INTEGER  NOT NULL  REFERENCES Books(book_id)
  member_id   INTEGER  NOT NULL  REFERENCES Members(member_id)
  loan_date   DATE     NOT NULL
  due_date    DATE     NOT NULL
  return_date DATE     (nullable — NULL means the book has not been returned)
```

**Design note — no status column:** Loan status (active / overdue / returned)
is derived at runtime from `return_date` and `due_date` via the `Loan.status`
Python property. Storing it as a column would risk inconsistency when
`return_date` is updated without also updating `status`.

---

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the database with sample books, members, and loans (run once)
python seed.py

# 4. Start the development server
python app.py
```

Open **http://127.0.0.1:5000** in a browser.

> **Re-seeding:** To reset the database to the original sample data, delete
> `library.db` and re-run `python seed.py`.

---

## Project Structure

```
app.py              Flask application — models + all routes (single file)
seed.py             One-time script to populate Books, Members, and Loans
requirements.txt    Python package dependencies
templates/
  base.html         Bootstrap 5 layout and navbar
  index.html        Loan list — home page (Requirement 1)
  loan_form.html    Add / Edit loan form (Requirement 1)
  report.html       Filtered report with statistics (Requirement 2)
library.db          SQLite database file (auto-created on first run)
```

---

## Requirement 1 — CRUD on Loans

**Main table:** `Loans`

| Action | Route | HTTP | What happens in the DB |
|---|---|---|---|
| View all | `GET /` | GET | `SELECT` all loans joined to Book and Member |
| Add loan | `GET /loans/add` | GET | Renders form with DB-populated dropdowns |
| Save new loan | `POST /loans/add` | POST | `INSERT INTO loans` |
| Edit loan | `GET /loans/<id>/edit` | GET | Renders pre-filled form |
| Save changes | `POST /loans/<id>/edit` | POST | `UPDATE loans SET ...` |
| Delete loan | `POST /loans/<id>/delete` | POST | `DELETE FROM loans WHERE loan_id = ?` |

**Key code — `app.py` lines 107–201:**

```python
def _load_form_choices():
    books   = Book.query.order_by(Book.title).all()    # SELECT from books
    members = Member.query.order_by(Member.name).all() # SELECT from members
    return books, members
```

Both `loan_add` and `loan_edit` call `_load_form_choices()` to build the
dropdown options dynamically. The template loop:

```jinja
{% for book in books %}
  <option value="{{ book.book_id }}">{{ book.title }}</option>
{% endfor %}
```

No book titles or member names are hard-coded anywhere.

---

## Requirement 2 — Loan Report

**Route:** `GET /report`

### Filter controls

| Control | Input type | Populated how |
|---|---|---|
| Loan Date From | Date input | Manual entry |
| Loan Date To | Date input | Manual entry |
| Genre | Dropdown | `SELECT DISTINCT genre FROM books ORDER BY genre` — **from DB** |
| Member | Dropdown | `SELECT member_id, name FROM members ORDER BY name` — **from DB** |
| Status | Dropdown | Hard-coded: All / Active / Returned / Overdue (structural enum) |

All filters are optional and combinable. The form uses GET so the
filter state is visible in the URL and the browser Back button works.

### Filter query (`app.py` lines 229–244)

```python
q = Loan.query.join(Book).join(Member).order_by(Loan.loan_date.desc())

if date_from_str:  q = q.filter(Loan.loan_date >= date.fromisoformat(date_from_str))
if date_to_str:    q = q.filter(Loan.loan_date <= date.fromisoformat(date_to_str))
if sel_genre:      q = q.filter(Book.genre == sel_genre)
if sel_member_id:  q = q.filter(Loan.member_id == sel_member_id)

loans = q.all()

if sel_status != "all":           # status is derived, not stored
    loans = [l for l in loans if l.status == sel_status]
```

Each filter is only applied when the user provides a value. All SQL
conditions are AND-combined automatically by SQLAlchemy.

### Statistics (`app.py` lines 247–251)

```python
total       = len(loans)
returned    = sum(1 for l in loans if l.status == "returned")
active      = sum(1 for l in loans if l.status == "active")
overdue     = sum(1 for l in loans if l.status == "overdue")
return_rate = round(returned / total * 100, 1) if total > 0 else 0.0
```

Statistics are computed over the already-filtered result set, so they
always match exactly what is shown in the table below them.

---

## Dynamic UI Controls (Stage 2, point c)

Four dropdown lists are populated from live database queries every time
the relevant page loads. None of their options are hard-coded.

| Dropdown | Page | Query |
|---|---|---|
| Book selector | Add Loan, Edit Loan | `Book.query.order_by(Book.title).all()` |
| Member selector | Add Loan, Edit Loan | `Member.query.order_by(Member.name).all()` |
| Genre filter | Report | `db.session.query(Book.genre).distinct().order_by(Book.genre)` |
| Member filter | Report | `Member.query.order_by(Member.name).all()` |

**Demo proof:** Add a new book with a new genre (e.g., "Self-Help") directly
in the SQLite shell — the genre filter dropdown on the Report page will
include "Self-Help" on the next request with zero code changes.

---

## AI Usage

This project was developed with AI assistance (Cursor / Claude).

- **Tools used:** Cursor IDE with Claude model.
- **Tasks AI assisted with:** Code scaffolding for Flask routes and Jinja
  templates, SQLAlchemy query patterns, Bootstrap layout, and seed data
  generation.
