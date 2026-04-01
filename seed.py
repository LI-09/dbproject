"""
seed.py — populate Books, Members, and Loans with sample data.

Run once after the database has been created:
    python seed.py

Safe to run multiple times: skips all inserts if Books already exist.
All loan dates are computed relative to today so that the derived
status logic (active / overdue / returned) is always correct.
"""

from datetime import date, timedelta
from app import app, db, Book, Member, Loan


def seed():
    with app.app_context():
        # Idempotency guard: do nothing if Books already exist.
        if Book.query.first():
            print("Database already seeded — skipping.")
            return

        today = date.today()

        # ----------------------------------------------------------------
        # Books — 10 titles across 5 genres so the genre filter in
        # Requirement 2 produces visibly different results.
        # ----------------------------------------------------------------
        books = [
            Book(title="The Great Gatsby",              author="F. Scott Fitzgerald", genre="Fiction",        isbn="9780743273565"),
            Book(title="1984",                          author="George Orwell",        genre="Fiction",        isbn="9780451524935"),
            Book(title="Gone Girl",                     author="Gillian Flynn",        genre="Mystery",        isbn="9780307588371"),
            Book(title="The Girl with the Dragon Tattoo", author="Stieg Larsson",     genre="Mystery",        isbn="9780307454546"),
            Book(title="Dune",                          author="Frank Herbert",        genre="Science Fiction",isbn="9780441013593"),
            Book(title="The Martian",                   author="Andy Weir",            genre="Science Fiction",isbn="9780553418026"),
            Book(title="Sapiens",                       author="Yuval Noah Harari",    genre="History",        isbn="9780062316097"),
            Book(title="The Guns of August",            author="Barbara Tuchman",      genre="History",        isbn="9780345476098"),
            Book(title="Steve Jobs",                    author="Walter Isaacson",      genre="Biography",      isbn="9781451648539"),
            Book(title="Educated",                      author="Tara Westover",        genre="Biography",      isbn="9780399590504"),
        ]
        db.session.add_all(books)
        db.session.flush()   # assign book_id values before creating Loans

        # ----------------------------------------------------------------
        # Members — 5 people so the member filter shows distinct results.
        # ----------------------------------------------------------------
        members = [
            Member(name="Alice Johnson", email="alice@example.com",  phone="555-1001"),
            Member(name="Bob Smith",     email="bob@example.com",    phone="555-1002"),
            Member(name="Carol White",   email="carol@example.com",  phone="555-1003"),
            Member(name="David Lee",     email="david@example.com",  phone="555-1004"),
            Member(name="Emma Davis",    email="emma@example.com",   phone="555-1005"),
        ]
        db.session.add_all(members)
        db.session.flush()   # assign member_id values before creating Loans

        # Convenience aliases so loan rows below are readable.
        gatsby, orwell, gone_girl, dragon, dune, martian, sapiens, guns, jobs, educated = books
        alice, bob, carol, david, emma = members

        # ----------------------------------------------------------------
        # Loans — 10 rows with deliberate status variety:
        #   4 ACTIVE  : return_date is NULL, due_date is in the future
        #   3 RETURNED: return_date is set
        #   3 OVERDUE : return_date is NULL, due_date is in the past
        #
        # All dates are offsets from today so status never goes stale.
        # ----------------------------------------------------------------
        loans = [
            # ---- ACTIVE loans ----
            Loan(book=gatsby,  member=alice, loan_date=today-timedelta(10), due_date=today+timedelta(4)),
            Loan(book=sapiens, member=bob,   loan_date=today-timedelta(5),  due_date=today+timedelta(9)),
            Loan(book=jobs,    member=david,  loan_date=today-timedelta(8),  due_date=today+timedelta(6)),
            Loan(book=educated,member=emma,   loan_date=today-timedelta(3),  due_date=today+timedelta(11)),

            # ---- RETURNED loans ----
            Loan(book=dune,    member=alice, loan_date=today-timedelta(30), due_date=today-timedelta(10),
                 return_date=today-timedelta(5)),
            Loan(book=orwell,  member=carol, loan_date=today-timedelta(25), due_date=today-timedelta(8),
                 return_date=today-timedelta(1)),
            Loan(book=dragon,  member=david, loan_date=today-timedelta(35), due_date=today-timedelta(15),
                 return_date=today-timedelta(10)),

            # ---- OVERDUE loans ----
            Loan(book=gone_girl, member=bob,  loan_date=today-timedelta(20), due_date=today-timedelta(2)),
            Loan(book=martian,   member=carol, loan_date=today-timedelta(15), due_date=today-timedelta(3)),
            Loan(book=guns,      member=emma,  loan_date=today-timedelta(40), due_date=today-timedelta(20)),
        ]
        db.session.add_all(loans)
        db.session.commit()

        print("Seeded successfully:")
        print(f"  {len(books)} books across 5 genres")
        print(f"  {len(members)} members")
        print(f"  {len(loans)} loans  (4 active, 3 returned, 3 overdue)")


if __name__ == "__main__":
    seed()
