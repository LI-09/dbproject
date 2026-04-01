# Stage 2 Demo Script
## CS348 Library Lending System

**Target duration:** 5–8 minutes  
**Format:** Screen recording with voice narration  
**Start state:** Fresh database — run `python seed.py` first, then `python app.py`

---

## Before You Record

```bash
cd dbproject
source venv/bin/activate
rm -f library.db          # ensure clean state
python seed.py            # loads 10 books, 5 members, 10 loans
python app.py             # starts server at http://127.0.0.1:5000
```

Have two windows open side-by-side:
- **Left:** browser at http://127.0.0.1:5000
- **Right:** your code editor showing `app.py` (use split-screen or alt-tab)

---

## Demo Script

---

### [0:00 – 0:45] Introduction and Database Design (S2-A)

**Say:**
> "This is a Library Lending System built with Python, Flask, SQLite, and
> SQLAlchemy. I'll walk through the database design and then demonstrate
> both required features."

**Switch to `app.py`, scroll to lines 25–83. Say:**
> "I have three tables. `Books` stores the library catalog. `Members` stores
> library cardholders. `Loans` is my main table — it records which member
> borrowed which book, when, and when they returned it."

**Point to lines 67–71. Say:**
> "Each Loan has a foreign key to Books and a foreign key to Members, which
> enforces referential integrity. There is no `status` column because status
> is fully derivable: if `return_date` is set, the loan is returned; if
> `due_date` has passed with no return, it's overdue; otherwise it's active."

**Point to lines 73–80. Say:**
> "This `status` property computes that logic on demand, with no risk of
> the column getting out of sync."

---

### [0:45 – 1:30] Home Page — Loan List

**Switch to browser, open http://127.0.0.1:5000. Say:**
> "The home page lists all loans in the database. You can see the derived
> status badges — blue for active, green for returned, red for overdue.
> These are computed live from `return_date` and `due_date` every time the
> page loads."

---

### [1:30 – 3:00] Requirement 1 — Add a Loan (S2-B, S2-J, S2-K)

**Click "+ New Loan". Say:**
> "Here is the Add Loan form."

**Point at the Book dropdown. Say:**
> "Notice this Book dropdown is populated from the database — not hard-coded.
> Let me show you how."

**Switch to `app.py`, lines 107–114. Say:**
> "This function `_load_form_choices` runs two SELECT queries: one on the
> Books table and one on the Members table. Both `loan_add` and `loan_edit`
> call this function, so the dropdowns are always up to date."

**Switch to `loan_form.html`, lines 16–24. Say:**
> "The Jinja template loops over the books list to build each option tag.
> No title is written in the template itself."

**Switch back to browser. Fill in the form:**
- Book: select any book, e.g. "The Great Gatsby — Fiction"
- Member: select "Bob Smith"
- Loan Date: today
- Due Date: two weeks from today

**Click "Add Loan". Say:**
> "The form POSTs to `/loans/add`. The route reads the form values, validates
> them, and runs an INSERT."

**Point to the new row in the loan list. Say:**
> "The new loan appears at the top of the list with Status: Active."

---

### [3:00 – 4:00] Requirement 1 — Edit a Loan (S2-C)

**Click "Edit" on the loan you just added. Say:**
> "The Edit form pre-fills with the current values. Notice the book and
> member dropdowns show the correct current selection."

**Point to lines 155–192 in `app.py`. Say:**
> "On GET, the route fetches the loan by primary key and passes it to the
> template along with the full book and member lists from the DB. The template
> uses `if loan.book_id == book.book_id` to mark the right option selected."

**Click "Mark Returned Today" in the browser. Say:**
> "This JavaScript button fills in today's date in the Return Date field.
> The current status shown below confirms it was Active before."

**Click "Save Changes". Say:**
> "The route runs UPDATE on the Loans table. The status badge has changed
> to Returned."

---

### [4:00 – 4:30] Requirement 1 — Delete a Loan (S2-D)

**Click "Delete" on any loan. Say:**
> "A browser confirmation dialog prevents accidental deletion."

**Click OK. Say:**
> "The form POSTs to `/loans/<id>/delete`. The route fetches the loan,
> calls `db.session.delete()`, and commits. The row is gone from the list."

**Point to lines 195–201 in `app.py`. Say:**
> "That is the entire delete route — fetch, delete, commit, redirect,
> and flash a confirmation message."

---

### [4:30 – 6:30] Requirement 2 — Report (S2-F, S2-G, S2-H, S2-I, S2-J, S2-K)

**Click "Report" in the navbar.**

#### Show: report before any filter (S2-H, first state)

**Say:**
> "The report page loads with no filters, showing all loans and their
> statistics. Right now: 10 total, 4 active, 3 returned, 3 overdue,
> return rate 30%."

**Note the stats on screen. Say:**
> "I want to show the report changing after a data change. Let me note
> these numbers — Total=10, Active=4."

#### Show: dynamic dropdowns (S2-J, S2-K)

**Point to the Genre dropdown. Say:**
> "This Genre dropdown is built dynamically. Let me show the query."

**Switch to `app.py`, lines 213–216. Say:**
> "This line runs `SELECT DISTINCT genre FROM books ORDER BY genre`.
> The result list — Fiction, History, Mystery, Science Fiction, Biography —
> is passed to the template, and the Jinja loop builds each option tag."

**Point to lines 217–218. Say:**
> "The Member dropdown works the same way: a SELECT on the members table,
> passed to the template. Nothing is written out in HTML."

#### Show: filters working (S2-F, S2-G)

**Switch to browser. Select Genre = "Science Fiction", click Apply Filters. Say:**
> "Filtering by Science Fiction gives 2 loans — Dune and The Martian.
> The statistics update to reflect only the filtered set: 1 active, 1 overdue,
> return rate 0%."

**Select Member = "Alice Johnson", click Apply Filters. Say:**
> "Filtering by member shows only Alice's loans. Her return rate is 50%."

**Select Status = "Overdue", click Apply Filters. Say:**
> "Three overdue loans across all members."

**Click Clear Filters. Say:**
> "Back to all 10 loans."

#### Show: report after a data change (S2-H, second state)

**Open a new tab with http://127.0.0.1:5000 (the home page).**
**Click "Edit" on any active loan. Click "Mark Returned Today". Click "Save Changes".**

**Switch back to the Report tab. Click Apply Filters (or just reload the page). Say:**
> "The report now shows: Total=10, Active=3, Returned=4, Return Rate=40%.
> The report reflects the data change we just made. This is the 'before and
> after' the handout requires."

#### Show: report source code (S2-I)

**Switch to `app.py`, lines 229–244. Say:**
> "The filter query starts by joining Loans to Books and Members. Each filter
> is only added when the user provided a value — so with no filters, you get
> all rows; with filters, you get the intersection. The status filter runs
> in Python because status is derived, not stored."

**Point to lines 247–251. Say:**
> "Statistics are computed over the filtered result set using Python
> comprehensions — simple to understand and always consistent with the table."

---

### [6:30 – 7:00] Wrap-up

**Say:**
> "To summarize: the database has three tables with proper foreign keys.
> Requirement 1 provides full add, edit, and delete on the Loans table,
> with book and member dropdowns always loaded from the database.
> Requirement 2 provides a filtered report with five filter controls,
> two of which — genre and member — are populated from the database,
> and five summary statistics that update live as data changes.
> All of this is implemented in a single `app.py` file with four Jinja
> templates and no hard-coded data in the UI."

---

## Key Code Locations (Quick Reference)

| What to show | File | Lines |
|---|---|---|
| Database models (PKs, FKs) | `app.py` | 25–83 |
| `status` derived property | `app.py` | 73–80 |
| Dynamic dropdown query (Req 1) | `app.py` | 107–114 |
| Insert loan | `app.py` | 140–145 |
| Update loan | `app.py` | 180–188 |
| Delete loan | `app.py` | 195–201 |
| Book dropdown template loop | `loan_form.html` | 16–24 |
| Member dropdown template loop | `loan_form.html` | 31–41 |
| Genre query (Req 2) | `app.py` | 213–216 |
| Member query (Req 2) | `app.py` | 217–218 |
| Conditional filter chain | `app.py` | 229–244 |
| Statistics computation | `app.py` | 247–251 |
| Genre dropdown in template | `report.html` | 40–48 |
| Member dropdown in template | `report.html` | 57–65 |

---

## Anticipated TA Questions and Answers

**Q: Why is status not stored as a column?**  
A: Because it is a derived attribute — it can be computed exactly from
`return_date` and `due_date`. Storing it redundantly would create a risk
of inconsistency: if we update `return_date` and forget to update `status`,
the data would be wrong. Deriving it in Python eliminates that risk entirely.

**Q: Why is the status filter in Requirement 2 hard-coded?**  
A: The status values (active, overdue, returned) are a structural enumeration
defined by the data model, not data stored in any table. Hard-coding them is
correct. Only values that ARE stored in the database — like genres and member
names — need to be loaded dynamically.

**Q: How do you prove the dropdowns are dynamic and not hard-coded?**  
A: Point to `_load_form_choices()` and the two queries in `report()`. Then
show: if you INSERT a new book with genre "Self-Help" directly in SQLite,
the Report page will show "Self-Help" in the Genre dropdown on the next
request with zero code changes.

**Q: What if a book is deleted but loans still reference it?**  
A: SQLite enforces the foreign key constraint (REFERENCES Books), so the
delete would fail. In practice, in this system Books are only managed via
the seed script and are not deleted through the UI, so this case does not
arise in the demo.

**Q: Is the report query efficient?**  
A: For the demo dataset it is fast. In Stage 3, we will add indexes on
`loans.book_id`, `loans.member_id`, and `loans.loan_date` to support the
report query and the form dropdowns. We can discuss that in Stage 3.
