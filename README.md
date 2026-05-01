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

## SQL Injection Protection (Stage 3)

The application is protected against SQL injection through two independent layers.

### Layer 1 — Input type validation (blocks injection before it reaches the database)

Every user-supplied value is converted to a strict Python type before being used. A malicious string never reaches SQLAlchemy because it is rejected at the parsing step.

| Location | Input | Validation | Effect of an injection string |
|----------|-------|------------|-------------------------------|
| `loan_add`, `loan_edit` (`app.py` lines 180–181) | `book_id`, `member_id` from form | `request.form.get(..., type=int)` | Non-integer returns `None`; caught by the required-fields check |
| `report` (`app.py` line 355) | `member_id` from URL params | `request.args.get(..., type=int)` | Same — silently becomes `None` |
| `loan_add`, `loan_edit` (`app.py` lines 193–194) | `loan_date`, `due_date` from form | `date.fromisoformat(string)` | Non-date string raises `ValueError` before the ORM is touched |
| All write routes | `loan_id` from URL path | `<int:loan_id>` in route definition | Flask rejects non-integers at routing time, before the route function runs |

### Layer 2 — ORM parameterization (the prepared-statement guarantee)

The application uses the SQLAlchemy ORM exclusively for every database operation. The ORM never concatenates user input into SQL strings. Instead it compiles every query with `?` bind-parameter placeholders and passes values separately to the database driver.

```python
# app.py lines 380–383 — report route filter
if sel_genre:
    q = q.filter(Book.genre == sel_genre)       # → WHERE books.genre = ?   params: ('Mystery',)
if sel_member_id:
    q = q.filter(Loan.member_id == sel_member_id) # → WHERE loans.member_id = ?   params: (2,)
```

There is zero raw SQL with user-input string concatenation anywhere in the codebase. `SQLALCHEMY_ECHO = True` (line 47) prints each query and its bound parameters to the console, making this visible at runtime.

---

## Indexes (Stage 3)

Six indexes are defined in the SQLAlchemy models (`app.py` lines 62–123). They were created by adding `index=True` to the relevant column definitions; SQLAlchemy's `db.create_all()` generates them automatically on startup.

| Index name | Table | Column | Line | Queries and routes supported |
|------------|-------|--------|------|------------------------------|
| `ix_books_title` | `books` | `title` | 68 | `ORDER BY books.title` in `_load_form_choices()` — runs on every `loan_add` and `loan_edit` page load |
| `ix_books_genre` | `books` | `genre` | 73 | `SELECT DISTINCT genre ORDER BY genre` for the Report dropdown; `WHERE books.genre = ?` genre filter in `report` route |
| `ix_members_name` | `members` | `name` | 90 | `ORDER BY members.name` in `_load_form_choices()` and the Report member dropdown — the most frequently executed query in the app |
| `ix_loans_book_id` | `loans` | `book_id` | 115 | `JOIN loans→books` in the `index` route and `report` route (SQLite does **not** auto-index FK columns) |
| `ix_loans_member_id` | `loans` | `member_id` | 119 | `JOIN loans→members` in the `index` and `report` routes; also `WHERE loans.member_id = ?` member filter in `report` |
| `ix_loans_loan_date` | `loans` | `loan_date` | 123 | `ORDER BY loans.loan_date DESC` in the `index` and `report` routes; `WHERE loans.loan_date >= ?` / `<= ?` date-range filter in `report` |

**Verify indexes exist:**
```bash
sqlite3 library.db "SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name;"
```

**SQLite FK note:** Unlike primary keys, SQLite does not automatically create indexes on foreign key columns. `ix_loans_book_id` and `ix_loans_member_id` are therefore essential — without them every JOIN from `loans` to `books` or `members` requires a full table scan.

---

## Transactions and Isolation Levels (Stage 3)

### Isolation level

```python
# app.py line 53
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"isolation_level": "SERIALIZABLE"}
```

`SERIALIZABLE` is set globally on the engine. This is the strictest isolation level — it prevents dirty reads, non-repeatable reads, and phantom reads. In SQLite, it is enforced through exclusive file-level locking: only one writer can hold the database at a time. This is the appropriate choice for a library system where two staff members could attempt to issue a loan simultaneously.

### Explicit transactions on all write routes

Every route that modifies the database wraps the operation in a `try/except/rollback` block:

```python
# Pattern used in loan_add, loan_edit, loan_delete (app.py lines 167–176, 220–228, 239–246)
try:
    db.session.add(new_loan)   # or commit() / delete()
    db.session.commit()
except Exception:
    db.session.rollback()      # undo all changes if anything fails
    flash("A database error occurred. No changes were saved.", "danger")
```

If `commit()` fails for any reason, `rollback()` is called immediately so no partial change is ever persisted.

### Multi-row atomic transaction — `bulk_return_overdue`

**Route:** `POST /loans/return-overdue` (`app.py` lines 291–326)

This route marks every overdue loan as returned today in a single transaction. It is the clearest demonstration of why transactions matter: without a transaction, a crash after updating the second of five overdue loans would leave the database permanently inconsistent. The single `db.session.commit()` at line 320 makes all N updates atomic — either every row is saved, or `rollback()` at line 323 undoes them all.

**Concurrent access scenario:** If two staff members clicked "Return All Overdue" simultaneously, the `SERIALIZABLE` isolation level ensures the second transaction waits for the first to complete rather than both updating the same rows concurrently. After the first transaction commits, the second finds zero overdue loans and makes no changes.

---

## AI Usage

**Tool used:** Cursor IDE with the Claude Sonnet 4.6 AI coding.

### Tasks the AI assisted with
| Task | What AI did |
|------|-------------|
| Project structure | Suggested the single-file Flask layout (`app.py` + `seed.py` + templates) and the SQLAlchemy model design |
| Code generation | Generated and improved code snippets for the CRUD routes (`loan_add`, `loan_edit`, `loan_delete`) and the filtered report route |
| SQL queries | Helped write and debug the ORM queries for the report filters and dynamic dropdown population |
| Sample data | Generated the `seed.py` script with 10 books across 5 genres, 5 members, and 10 loans with deliberate status variety (active / returned / overdue) |
| Concepts | Explained programming concepts and error messages encountered during development (e.g., SQLAlchemy session behaviour, Jinja2 template syntax) |
| Planning | Analyzed the Stage 3 rubric and the existing codebase; identified which indexes to add, where transactions were missing, and what SQL injection protection needed to be surfaced |
| Index implementation | Generated `index=True` column flags for 6 columns with justification comments mapping each index to the specific query and route it supports |
| Transaction implementation | Generated try/except/rollback blocks for all write routes; generated the `bulk_return_overdue` route; configured `SERIALIZABLE` isolation level with explanatory comments |
| SQL injection protection | Generated the two-layer protection comment blocks and `SQLALCHEMY_ECHO = True` configuration |
| Demo scripts | Drafted timed demo scripts for all four Stage 3 sections, calibrated to fit within the 10-minute video limit |

### How the AI output was verified and modified

The following practices were applied consistently across both stages:

- **Understood all code before accepting it.** No AI-generated code was submitted without first reading and understanding it. Every design decision — the database schema, which columns to index and why, the isolation level choice, the two-layer SQL injection protection, and the atomicity guarantee of the bulk-return transaction — can be explained independently.
- **Manually tested after every change.** The application was run locally and tested in the browser after every AI-assisted modification to confirm it worked as intended.
- **Used terminal queries to verify AI-implemented features.** For example:
  - Indexes were confirmed by querying `sqlite_master`: `SELECT name, tbl_name FROM sqlite_master WHERE type='index'`
  - SQL injection protection was confirmed by applying the genre filter with `SQLALCHEMY_ECHO = True` and verifying the terminal shows `WHERE books.genre = ?` with `('Mystery',)` as a separate bound parameter.
- **Cross-checked AI suggestions against official documentation.** SQLAlchemy ORM documentation was used to verify parameterization behaviour and isolation level configuration. SQLite documentation was used to verify that foreign key columns are not automatically indexed. AI output was not accepted solely on the basis of what the AI stated.
- **Manually checked against the project handout and rubric** after each stage to confirm all requirements were met before finalising the submission.
- **AI was used to implement concepts covered in the course**, not to bypass learning them. Indexes, transactions, isolation levels, and SQL injection were all studied in CS348; AI helped apply those concepts to this specific codebase.
