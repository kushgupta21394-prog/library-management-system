# Library Management System - Python + SQLite
import sqlite3
from datetime import date, timedelta

LOAN_DAYS = 14
FINE_PER_DAY = 2

conn = sqlite3.connect("library.db")
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    available INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS issued (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    member_id INTEGER,
    issue_date TEXT,
    due_date TEXT,
    return_date TEXT
);
""")
conn.commit()


def add_book():
    title = input("Title: ").strip()
    author = input("Author: ").strip()
    cur.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    print("Book added. ID =", cur.lastrowid)


def add_member():
    name = input("Member name: ").strip()
    cur.execute("INSERT INTO members (name) VALUES (?)", (name,))
    conn.commit()
    print("Member added. ID =", cur.lastrowid)


def search_books():
    word = "%" + input("Search title or author: ").strip() + "%"
    cur.execute("SELECT book_id, title, author, available FROM books "
                "WHERE title LIKE ? OR author LIKE ?", (word, word))
    rows = cur.fetchall()
    if not rows:
        print("No books found.")
        return
    print(f"{'ID':<5}{'Title':<30}{'Author':<20}Status")
    for r in rows:
        status = "Available" if r[3] else "Issued"
        print(f"{r[0]:<5}{r[1]:<30}{r[2]:<20}{status}")


def issue_book():
    book_id = input("Book ID: ")
    member_id = input("Member ID: ")
    cur.execute("SELECT available FROM books WHERE book_id = ?", (book_id,))
    book = cur.fetchone()
    cur.execute("SELECT 1 FROM members WHERE member_id = ?", (member_id,))
    member = cur.fetchone()
    if book is None or member is None:
        print("Invalid book or member ID.")
        return
    if not book[0]:
        print("Book is already issued.")
        return
    today = date.today()
    due = today + timedelta(days=LOAN_DAYS)
    cur.execute("INSERT INTO issued (book_id, member_id, issue_date, due_date) "
                "VALUES (?, ?, ?, ?)", (book_id, member_id, str(today), str(due)))
    cur.execute("UPDATE books SET available = 0 WHERE book_id = ?", (book_id,))
    conn.commit()
    print("Book issued. Due date:", due)


def return_book():
    book_id = input("Book ID to return: ")
    cur.execute("SELECT issue_id, due_date FROM issued "
                "WHERE book_id = ? AND return_date IS NULL", (book_id,))
    record = cur.fetchone()
    if record is None:
        print("This book is not currently issued.")
        return
    today = date.today()
    late_days = (today - date.fromisoformat(record[1])).days
    fine = max(0, late_days) * FINE_PER_DAY
    cur.execute("UPDATE issued SET return_date = ? WHERE issue_id = ?", (str(today), record[0]))
    cur.execute("UPDATE books SET available = 1 WHERE book_id = ?", (book_id,))
    conn.commit()
    print("Book returned.", f"Late fine: Rs {fine}" if fine else "No fine.")


def overdue_books():
    cur.execute("""SELECT b.title, m.name, i.due_date FROM issued i
                   JOIN books b ON b.book_id = i.book_id
                   JOIN members m ON m.member_id = i.member_id
                   WHERE i.return_date IS NULL AND i.due_date < ?""", (str(date.today()),))
    rows = cur.fetchall()
    if not rows:
        print("No overdue books.")
        return
    for title, name, due in rows:
        days = (date.today() - date.fromisoformat(due)).days
        print(f"{title} - {name} - due {due} ({days} days late, fine Rs {days * FINE_PER_DAY})")


def main():
    while True:
        print("\n1.Add book 2.Add member 3.Search books")
        print("4.Issue book 5.Return book 6.Overdue list 7.Exit")
        choice = input("Choose: ")
        if choice == "1":
            add_book()
        elif choice == "2":
            add_member()
        elif choice == "3":
            search_books()
        elif choice == "4":
            issue_book()
        elif choice == "5":
            return_book()
        elif choice == "6":
            overdue_books()
        elif choice == "7":
            conn.close()
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


main()
