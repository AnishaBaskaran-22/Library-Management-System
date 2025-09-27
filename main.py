from fastapi import FastAPI, Request, Form, Cookie,HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import mysql.connector
from fastapi import Body
from typing import List
from datetime import date
from fastapi import Request, Form
from datetime import date,datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from fastapi import Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import  text
from sqlalchemy.orm import sessionmaker
import uuid
import random
from fastapi import FastAPI, Request, Form, status
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




app = FastAPI()


templates = Jinja2Templates(directory="templates")

# ----------------- Database ------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="rudra",
        database="lib_db"
    )

app.mount("/static", StaticFiles(directory="static"), name="static")
# ----------------- Welcome and Role ------------------
@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})

@app.get("/chooserole", response_class=HTMLResponse)
def chooserole(request: Request):
    return templates.TemplateResponse("chooserole.html", {"request": request})

# ----------------- Admin Signup ------------------
@app.get("/admin_signup", response_class=HTMLResponse)
def admin_signup(request: Request):
    return templates.TemplateResponse("admin_signup.html", {"request": request})

@app.post("/admin_signup", response_class=HTMLResponse)
async def handle_admin_signup(
    request: Request,
    admin_id:str = Form(...),
    fullname: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (admin_id,fullname, username, email,password,phone_number) VALUES (%s, %s, %s, %s, %s, %s)",
                       (admin_id,fullname, username, email,password,phone_number))
        conn.commit()
        cursor.close()
        conn.close()
        response = RedirectResponse(url="/admin_dashboard", status_code=302)
        response.set_cookie(key="username", value=username)  # ✅ Set cookie
        return response
    except mysql.connector.Error as e:
        return templates.TemplateResponse("admin_signup.html", {
            "request": request,
            "error": "Database error: " + str(e)
        })

# ----------------- Admin Login ------------------
@app.get("/admin_login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin_login", response_class=HTMLResponse)
async def admin_login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            response = RedirectResponse(url="/admin_dashboard", status_code=302)
            response.set_cookie(key="username", value=username) 
            return response
        else:
            return templates.TemplateResponse("admin_login.html", {
                "request": request,
                "error": "Invalid username/password. Try again."
            })
    except Exception:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Login failed. Please try again later."
        })

# ----------------- Admin Dashboard ------------------
@app.get("/admin_dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

# ----------------- Admin Profile ------------------

@app.get("/admin_profile", response_class=HTMLResponse)
def admin_profile(request: Request, username: str = Cookie(default=None)):
    if not username:
        return RedirectResponse(url="/admin_signup", status_code=302)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT admin_id, fullname,username, email, phone_number FROM users WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            return templates.TemplateResponse("admin_profile.html", {"request": request, "admin": admin})
        else:
            return RedirectResponse("/admin_signup")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@app.get("/admin_profile", response_class=HTMLResponse)
def admin_profile(request: Request, username: str = Cookie(default=None)):
    if not username:
        return RedirectResponse(url="/admin_login", status_code=302)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT admin_id, fullname,username, email, phone_number FROM users WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            return templates.TemplateResponse("admin_profile.html", {"request": request, "admin": admin})
        else:
            return RedirectResponse("/admin_login")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.get("/admin_profile_edit", response_class=HTMLResponse)
def admin_profile_edit(request: Request, username: str = Cookie(default=None)):
    if not username:
        return RedirectResponse(url="/admin_login", status_code=302)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT admin_id, fullname, username, email, phone_number FROM users WHERE username = %s",
            (username,)
        )
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            return templates.TemplateResponse("admin_profile_edit.html", {"request": request, "admin": admin})
        else:
            return RedirectResponse("/admin_login")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/admin_profile/edit")
async def update_admin_profile(
    request: Request,
    admin_id: str = Form(...),
    fullname: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    cookie_username: str = Cookie(default=None)
):
    # To prevent username tampering, use the username from the cookie as the original user
    if cookie_username != username:
        return JSONResponse(status_code=403, content={"error": "Unauthorized update attempt."})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users SET admin_id=%s, fullname=%s, email=%s, phone_number=%s WHERE username=%s
            """,
            (admin_id, fullname, email, phone_number, username)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # on success, redirect back to profile view
        return RedirectResponse(url="/admin_profile", status_code=303)

    except Exception as e:
        # On error, send back edit form with error message
        admin = {
            "admin_id": admin_id,
            "fullname": fullname,
            "username": username,
            "email": email,
            "phone_number": phone_number,
        }
        return templates.TemplateResponse("admin_profile_edit.html", {
            "request": request,
            "admin": admin,
            "error": str(e)
        })
    


#--------------- User Signup---------------------------------
@app.get("/student_signup", response_class=HTMLResponse)
def student_signup(request: Request):
    return templates.TemplateResponse("student_signup.html", {"request": request})

@app.post("/student_signup", response_class=HTMLResponse)
async def handle_student_signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    designation: str = Form(...),
    location: str = Form(...) 
):
    try:
        # Generate unique member ID
        member_id = f"LIB-{random.randint(100000, 999999)}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
    "INSERT INTO members (member_id, name, email, password, phone_number, designation, location) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (member_id, name, email, password, phone_number, designation, location)
)

        conn.commit()
        cursor.close()
        conn.close()

      
        response = RedirectResponse(url="/student_dashboard", status_code=302)
        response.set_cookie(key="name", value=name)
        return response

    except mysql.connector.Error as err:
        return templates.TemplateResponse(
            "student_signup.html",
            {
                "request": request,
                "error": "Database error: " + str(err)
            }
        )

# ----------------- User Login ------------------

@app.get("/student_login", response_class=HTMLResponse)
def student_login(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request})

from fastapi.responses import RedirectResponse
@app.post("/student_login", response_class=HTMLResponse)
async def student_login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT member_id, name FROM members WHERE name=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return templates.TemplateResponse(
            "student_login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    response = RedirectResponse(url="/student_dashboard", status_code=302)
    response.set_cookie(key="member_id", value=user["member_id"])
    response.set_cookie(key="member_name", value=user["name"])
    return response


# ----------------- User Dashboard ------------------
@app.get("/student_dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    return templates.TemplateResponse("student_dashboard.html", {"request": request})

# ----------------- Book Operations ------------------
# ----------------- Add Operations ------------------
@app.get("/add_books", response_class=HTMLResponse)
def add_books_form(request: Request):
    return templates.TemplateResponse("add_books.html", {"request": request})

@app.post("/add_books", response_class=HTMLResponse)
async def handle_add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    stock: int = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if book already exists
        cursor.execute("SELECT * FROM books WHERE title = %s AND author = %s", (title, author))
        existing_book = cursor.fetchone()

        if existing_book:
            cursor.close()
            conn.close()
            return templates.TemplateResponse("add_books.html", {
                "request": request,
                "error": "Book already exists"
            })

        # Add book
        cursor.execute("INSERT INTO books (title, author, stock) VALUES (%s, %s, %s)", (title, author, stock))
        conn.commit()
        cursor.close()
        conn.close()

        return templates.TemplateResponse("add_books.html", {
            "request": request,
            "message": "Book added successfully"
        })

    except mysql.connector.Error as err:
        return templates.TemplateResponse("add_books.html", {
            "request": request,
            "error": f"Failed to add book: {err}"
        })

# ----------------- Delete Operations ------------------
@app.get("/delete_books", response_class=HTMLResponse)
def delete_books_page(request: Request):
    return templates.TemplateResponse("delete_books.html", {"request": request})

@app.get("/get_books")
def get_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return JSONResponse(content=books)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/delete_book/{book_id}")
def delete_book(book_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/book_lists", response_class=HTMLResponse)
def book_lists_page(request: Request):
    return templates.TemplateResponse("book_lists.html", {"request": request})

@app.get("/update_stock", response_class=HTMLResponse)
def update_stock_page(request: Request):
    return templates.TemplateResponse("update_stock.html", {"request": request})

@app.post("/get_stock")
async def get_stock(title: str = Form(...), author: str = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM books 
            WHERE LOWER(TRIM(title)) = LOWER(%s) 
              AND LOWER(TRIM(author)) = LOWER(%s)
        """
        cursor.execute(query, (title.strip(), author.strip()))
        book = cursor.fetchone()
        cursor.close()
        conn.close()

        if book:
            return JSONResponse(content={"found": True, "stock": book["stock"], "id": book["id"]})
        else:
            return JSONResponse(content={"found": False})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

# -----------------Update Operations ------------------    

@app.post("/update_stock")
async def update_stock(book_id: int = Form(...), new_stock: int = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE books SET stock = %s WHERE id = %s", (new_stock, book_id))
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/all_books")
async def all_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, author, stock FROM books")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return books
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})
 




# Enable frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL connection

@app.get("/get_books")
def get_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE stock > 0")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return books
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------------- Render Issue Book Page ------------------
@app.get("/issue_books", response_class=HTMLResponse)
def issue_books_page(request: Request):
    return templates.TemplateResponse("issue_books.html", {"request": request})

# ----------------- Get Member by ID ------------------
@app.get("/member/{member_id}")
def get_member_by_id(member_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        member = cursor.fetchone()
        cursor.close()
        conn.close()
        if not member:
            return JSONResponse(status_code=404, content={"error": "Member not found"})
        return member
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})




# ----------------- Get Member Book Count ------------------
@app.get("/member_books_count")
def member_books_count(member_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM issuedbooks WHERE member_id = %s", (member_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"count": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------------- Search Books by Title or Author ------------------
@app.get("/books/search/{query}")
def search_books(query: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        like_query = f"%{query.lower()}%"
        cursor.execute("""
            SELECT id, title, author, stock, borrowed, returned
            FROM books
            WHERE LOWER(title) LIKE %s OR LOWER(author) LIKE %s
        """, (like_query, like_query))
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        return books
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------------- Issue Books (POST) ------------------
@app.post("/issue-books", response_class=HTMLResponse)
async def issue_books_submit(
    request: Request,
    member_id: str = Form(...),
    member_name: str = Form(...),
    books: str = Form(...)
):
    try:
        # Parse books JSON
        try:
            books_info = json.loads(books)
        except json.JSONDecodeError:
            return templates.TemplateResponse(
                "issue_books.html",
                {"request": request, "error": "Invalid book data format."}
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check current number of books issued
        cursor.execute("SELECT COUNT(*) FROM issuedbooks WHERE member_id = %s", (member_id,))
        current_count = cursor.fetchone()[0]
        desired = len(books_info)
        if current_count + desired > 5:
            return templates.TemplateResponse(
                "issue_books.html",
                {
                    "request": request,
                    "error": f"Borrow limit exceeded! You can borrow only {5 - current_count} more book(s)."
                }
            )

        issue_date = date.today()
        renewal_date = issue_date + timedelta(days=30)
        return_date = issue_date + timedelta(days=60)
        success_count = 0
        error_msgs = []

        for book in books_info:
            # Duplicate check
            cursor.execute(
                "SELECT 1 FROM issuedbooks WHERE member_id=%s AND book_title=%s",
                (member_id, book["title"])
            )
            if cursor.fetchone():
                error_msgs.append(f"Book '{book['title']}' already borrowed.")
                continue

            # Stock check
            cursor.execute("SELECT stock FROM books WHERE id=%s", (book["id"],))
            row = cursor.fetchone()
            if not row or row[0] <= 0:
                error_msgs.append(f"Book '{book['title']}' is currently unavailable.")
                continue

            # Insert into issuedbooks
            cursor.execute("""
                INSERT INTO issuedbooks
                (member_id, member_name, book_title, issue_date, renewal_date, return_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (member_id, member_name, book["title"], issue_date, renewal_date, return_date))

            # Update books stock and borrowed count
            cursor.execute("""
                UPDATE books
                SET stock = stock - 1, borrowed = borrowed + 1
                WHERE id = %s
            """, (book["id"],))
            success_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        # Build feedback message
        msg = ""
        if success_count > 0:
            msg += f"{success_count} book(s) issued successfully. "
        if error_msgs:
            msg += " ".join(error_msgs)

        if error_msgs or success_count == 0:
            return templates.TemplateResponse(
                "issue_books.html",
                {"request": request, "error": msg.strip()}
            )
        else:
            # Redirect to dashboard
          
            return templates.TemplateResponse(
                 "issue_books.html",
                    {"request": request, "success": f"{success_count} book(s) issued successfully."}
    )


    except Exception as ex:
        return templates.TemplateResponse(
            "issue_books.html",
            {"request": request, "error": f"Unexpected error: {ex}"}
        )

@app.get("/books/issued/{member_id}/{book_title}")
def is_book_already_issued(member_id: str, book_title: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM issuedbooks 
            WHERE member_id = %s AND book_title = %s
        """, (member_id, book_title))
        already_issued = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return {"alreadyIssued": already_issued}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

#----------------------return books-------------------------------

@app.get("/return_books", response_class=HTMLResponse)
def return_books_page(request: Request):
    return templates.TemplateResponse("return_books.html", {"request": request})




@app.get("/issued-books/{member_id}")
def get_issued_books(member_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM issuedbooks WHERE member_id = %s", (member_id,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books



@app.post("/return-book/{issue_id}")
def return_book(issue_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Find issued book
    cursor.execute("SELECT * FROM issuedbooks WHERE id = %s", (issue_id,))
    issued = cursor.fetchone()
    if not issued:
        cursor.close()
        conn.close()
        return {"success": False, "message": "Book record not found."}

    # Insert into returnedbooks
    cursor.execute(
        "INSERT INTO returnedbooks (member_id, member_name, book_id, book_title, return_date) VALUES (%s, %s, %s, %s, %s)",
        (issued['member_id'], issued['member_name'], issued['id'], issued['book_title'], date.today())
    )

    # Update books table stock counts
    cursor.execute("SELECT * FROM books WHERE title = %s", (issued['book_title'],))
    book_row = cursor.fetchone()
    if book_row:
        cursor.execute(
            "UPDATE books SET stock = stock + 1, borrowed = borrowed - 1, returned = returned + 1 WHERE id = %s",
            (book_row['id'],)
        )

    # Delete from issuedbooks
    cursor.execute("DELETE FROM issuedbooks WHERE id = %s", (issue_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return {"success": True, "message": "Book returned successfully"}








@app.get("/admin_returned_books", response_class=HTMLResponse)
def admin_returned_books(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT member_id,member_name, book_title, return_date
            FROM returnedbooks
            ORDER BY return_date DESC
        """)
        returned_books = cursor.fetchall()
        cursor.close()
        conn.close()

        return templates.TemplateResponse("admin_returned_books.html", {
            "request": request,
            "returned_books": returned_books
        })
    except Exception as e:
        return templates.TemplateResponse("admin_returned_books.html", {
            "request": request,
            "returned_books": [],
            "error": str(e)
        })


# ----------- Admin: All Borrowed Books -----------
@app.get("/borrowed_books", response_class=HTMLResponse)
def admin_borrowed_books(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT member_id, member_name, book_title, issue_date, renewal_date, return_date
        FROM issuedbooks
        ORDER BY issue_date DESC
    """)
    borrowed_books = cursor.fetchall()
    cursor.close()
    conn.close()
    return templates.TemplateResponse(
        "borrowed_books.html",
        {"request": request, "borrowed_books": borrowed_books},
    )



@app.get("/student_profile", response_class=HTMLResponse)
async def student_profile(request: Request):
    try:
        # get username from cookie (set at login)
        username = request.cookies.get("name")
        if not username:
            return RedirectResponse(url="/student_login")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM members WHERE name = %s", (username,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if not student:
            return templates.TemplateResponse(
                "student_profile.html",
                {"request": request, "error": "Student not found"}
            )

        return templates.TemplateResponse(
            "student_profile.html",
            {"request": request, "student": student}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "student_profile.html",
            {"request": request, "error": f"Error: {str(e)}"}
        )



from fastapi.responses import Response

@app.get("/student_login")
def student_login(response: Response):
    # In a real app, verify credentials and then set cookie after login
    response.set_cookie(key="username", value="testuser")
    return {"message": "Logged in! Cookie set for 'username=testuser'."}




from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/dashboard_stats")
def dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Total Students
        cursor.execute("SELECT COUNT(*) AS totalStudents FROM members ")
        total_students = cursor.fetchone()["totalStudents"]

        # Total Books (adjust depending on table)
        cursor.execute("SELECT COUNT(*) AS totalBooks FROM books")
        total_books = cursor.fetchone()["totalBooks"]

        # Borrowed Books (not yet returned)
        cursor.execute("SELECT COUNT(*) AS borrowedBooks FROM issuedbooks ")
        borrowed_books = cursor.fetchone()["borrowedBooks"]

        # Returned Books
        cursor.execute("SELECT COUNT(*) AS returnedBooks FROM returnedbooks")
        returned_books = cursor.fetchone()["returnedBooks"]

        cursor.close()
        conn.close()

        return JSONResponse({
            "users": {"students": total_students},
            "books": {
                "total": total_books,
                "borrowed": borrowed_books,
                "returned": returned_books
            }
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})





# --- User Profile Data ---
@app.get("/student_profile_data")
def student_profile_data(member_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM members WHERE member_id=%s", (member_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"fullname": row["name"] if row else "Unknown"}


# --- Borrowed & Returned Counts ---
@app.get("/student_book_counts")
def student_book_counts(member_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Borrowed = issued but not yet returned
    cursor.execute("""
        SELECT COUNT(*) AS borrowed
        FROM issuedbooks
        WHERE member_id = %s AND return_date IS NULL
    """, (member_id,))
    borrowed = cursor.fetchone()["borrowed"]

    # Returned = rows in returnedbooks
    cursor.execute("""
        SELECT COUNT(*) AS returned
        FROM returnedbooks
        WHERE member_id = %s
    """, (member_id,))
    returned = cursor.fetchone()["returned"]

    cursor.close()
    conn.close()
    return {"borrowed": borrowed, "returned": returned}


# --- Due Soon Notifications ---
@app.get("/due_books_notifications")
def due_books_notifications(member_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = date.today()
    soon = today + timedelta(days=3)

    cursor.execute("""
        SELECT book_title, renewal_date
        FROM issuedbooks
        WHERE member_id = %s
          AND return_date IS NULL
          AND renewal_date BETWEEN %s AND %s
    """, (member_id, today, soon))
    due_books = cursor.fetchall()

    cursor.close()
    conn.close()
    return {"due_books": due_books}


@app.post("/return-book/{issue_id}")
def return_book(issue_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch issued book details
        cursor.execute("SELECT * FROM issuedbooks WHERE id=%s", (issue_id,))
        issued = cursor.fetchone()
        if not issued:
            cursor.close()
            conn.close()
            return JSONResponse(status_code=404, content={
                "success": False,
                "message": "Issued book not found."
            })

        today = datetime.today().date()
        return_date = issued['return_date']

        # Calculate how many days late (if any)
        days_late = (today - return_date).days

        fine = 0
        if days_late > 10:
            # Base fine for first 10 days late
            fine = 75
            # Additional fine for days beyond 10
            fine += (days_late - 10) * 10
        elif days_late > 0:
            # Late but <= 10 days, only base fine applies
            fine = 75

        # Get student_id from students
        cursor.execute("SELECT id FROM students WHERE roll_number=%s", (issued['roll_number'],))
        student_row = cursor.fetchone()
        student_id = student_row['id'] if student_row else None

        # Get book_id from books
        cursor.execute("SELECT id FROM books WHERE title=%s", (issued['book_title'],))
        book_row = cursor.fetchone()
        book_id = book_row['id'] if book_row else None

        if not student_id or not book_id:
            cursor.close()
            conn.close()
            return JSONResponse(status_code=400, content={
                "success": False,
                "message": "Invalid student or book data."
            })

        # Update books table: stock +1, borrowed -1, returned +1
        cursor.execute("""
            UPDATE books
            SET stock = stock + 1,
                borrowed = GREATEST(borrowed - 1, 0),
                returned = returned + 1
            WHERE id = %s
        """, (book_id,))

        # Insert into returnedbooks with fine
        cursor.execute("""
            INSERT INTO returnedbooks (student_id, roll_number, student_name, book_id, book_title, return_date, fine_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            student_id,
            issued['roll_number'],
            issued['student_name'],
            book_id,
            issued['book_title'],
            today,
            fine
        ))

        # Delete from issuedbooks
        cursor.execute("DELETE FROM issuedbooks WHERE id=%s", (issue_id,))

        conn.commit()
        cursor.close()
        conn.close()

        msg = "Book returned successfully."
        if fine > 0:
            msg += f" You have a fine of ₹{fine} for late return."

        return {"success": True, "message": msg, "fine": fine}
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": f"Error during return: {str(e)}"
        })


@app.post("/student_login", response_class=HTMLResponse)
async def student_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT member_id, name FROM members WHERE name = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            response = RedirectResponse(url="/student_dashboard", status_code=302)
            # Set cookies for member_id and username
            response.set_cookie(key="member_id", value=user["member_id"])
            response.set_cookie(key="member_name", value=user["name"])
            return response
        else:
            return templates.TemplateResponse(
                "student_login.html",
                {"request": request, "error": "Invalid username or password"}
            )
    except Exception as err:
        return templates.TemplateResponse(
            "student_login.html",
            {"request": request, "error": f"Database error: {str(err)}"}
        )
@app.get("/student_borrowed_books", response_class=HTMLResponse)
def borrowed_books(request: Request, name: str = Cookie(default=None)):
    # If cookie NOT present, you may show a blank/unauthorized page, but do NOT redirect if user is assumed logged in
    if not name:
        # Optionally, show an error or empty table
        return templates.TemplateResponse(
            "student_borrowed_books.html",
            {"request": request, "books": [], "error": "User not authenticated."}
        )
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Find member by name stored in cookie
    cursor.execute("SELECT member_id, name FROM members WHERE name=%s", (name,))
    member = cursor.fetchone()
    if not member:
        cursor.close()
        conn.close()
        # Optionally, show an error (user info not found in DB)
        return templates.TemplateResponse(
            "student_borrowed_books.html",
            {"request": request, "books": [], "error": "Member not found in DB."}
        )

    member_id = member["member_id"]
    cursor.execute("""
        SELECT book_title, issue_date, renewal_date, return_date 
        FROM issuedbooks 
        WHERE member_id=%s
    """, (member_id,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    # Always display the borrowed books for the logged-in user
    return templates.TemplateResponse("student_borrowed_books.html", {
        "request": request,
        "member_id": member_id,
        "member_name": member["name"],
        "books": books,
        "error": ""  # No error if member exists and lookup succeeded
    })
@app.post("/student_login", response_class=HTMLResponse)
async def student_login(request: Request,
                        username: str = Form(...),
                        password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # authenticate by name+password; change to email if you prefer
    cur.execute("SELECT member_id, name FROM members WHERE name=%s AND password=%s",
                (username, password))
    user = cur.fetchone()
    cur.close(); conn.close()

    if not user:
        return templates.TemplateResponse(
            "student_login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    # set cookies and go to dashboard (or straight to /returned_books)
    resp = RedirectResponse(url="/returned_books", status_code=303)
    resp.set_cookie(key="member_id", value=user["member_id"], httponly=True, samesite="lax", path="/")
    resp.set_cookie(key="member_name", value=user["name"], httponly=True, samesite="lax", path="/")
    return resp

@app.get("/returned_books", response_class=HTMLResponse)
def returned_student_books(request: Request, name: str = Cookie(default=None)):
    # If cookie NOT present, you may show a blank/unauthorized page, but do NOT redirect if user is assumed logged in
    if not name:
        # Optionally, show an error or empty table
        return templates.TemplateResponse(
            "returned_books.html",
            {"request": request, "books": [], "error": "User not authenticated."}
        )
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Find member by name stored in cookie
    cursor.execute("SELECT member_id, name FROM members WHERE name=%s", (name,))
    member = cursor.fetchone()
    if not member:
        cursor.close()
        conn.close()
        # Optionally, show an error (user info not found in DB)
        return templates.TemplateResponse(
            "returned_books.html",
            {"request": request, "books": [], "error": "Member not found in DB."}
        )

    member_id = member["member_id"]
    cursor.execute("""
        SELECT book_title, return_date 
        FROM returnedbooks 
        WHERE member_id=%s
    """, (member_id,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    # Always display the borrowed books for the logged-in user
    return templates.TemplateResponse("returned_books.html", {
        "request": request,
        "member_id": member_id,
        "member_name": member["name"],
        "returned_books": books,
        "error": ""  # No error if member exists and lookup succeeded
    })
@app.post("/student_login", response_class=HTMLResponse)
async def student_login(request: Request,
                        username: str = Form(...),
                        password: str = Form(...)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # authenticate by name+password; change to email if you prefer
    cur.execute("SELECT member_id, name FROM members WHERE name=%s AND password=%s",
                (username, password))
    user = cur.fetchone()
    cur.close(); conn.close()

    if not user:
        return templates.TemplateResponse(
            "student_login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    # set cookies and go to dashboard (or straight to /returned_books)
    resp = RedirectResponse(url="/returned_books", status_code=303)
    resp.set_cookie(key="member_id", value=user["member_id"], httponly=True, samesite="lax", path="/")
    resp.set_cookie(key="member_name", value=user["name"], httponly=True, samesite="lax", path="/")
    return resp


# ----------------- Feedback ------------------
@app.get("/feedback", response_class=HTMLResponse)
def feedback_form(request: Request):
    return templates.TemplateResponse("feedback.html", {"request": request})

@app.post("/feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    rating: int = Form(...),
    comments: str = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedbacks (name, email, rating, comments) VALUES (%s, %s, %s, %s)",
            (name, email, rating, comments)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return templates.TemplateResponse(
            "feedback.html",
            {"request": request, "success": "Thank you! Your feedback has been saved."}
        )
    except mysql.connector.Error as e:
        return templates.TemplateResponse(
            "feedback.html",
            {"request": request, "error": "Database error: " + str(e)}
        )
# ✅ Admin API: Get all feedbacks (JSON)
@app.get("/admin/feedbacks")
def get_feedbacks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, rating, comments,created_at FROM feedbacks")
        feedbacks = cursor.fetchall()
        cursor.close()
        conn.close()
        return feedbacks
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Admin Dashboard Page
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


# ✅ Admin Feedback Page
@app.get("/admin/feedback", response_class=HTMLResponse)
def admin_feedback(request: Request):
    return templates.TemplateResponse("admin_feedback.html", {"request": request})

# ✅ Send Reply Email
@app.post("/admin/reply")
def send_reply(email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    try:
        sender_email = "anishabaskaran3112@gmail.com"   # replace with your email
        sender_password = "RUDra"  # use App Password, not your main Gmail password
        receiver_email = email

        # Email structure
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        # Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        return {"status": "success", "message": "Reply sent successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        

@app.get("/student_dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    member_id = request.cookies.get("memberid")
    return templates.TemplateResponse("student_dashboard.html", {"request": request, "member_id": member_id})


@app.get("/student_signup", response_class=HTMLResponse)
def student_signup(request: Request):
    return templates.TemplateResponse("student_signup.html", {"request": request})

@app.post("/student_signup", response_class=HTMLResponse)
async def handle_student_signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    designation: str = Form(...),
    location: str = Form(...) 
):
    try:
        # Generate unique member ID
        member_id = f"LIB-{random.randint(100000, 999999)}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
    "INSERT INTO members (member_id, name, email, password, phone_number, designation, location) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (member_id, name, email, password, phone_number, designation, location)
)

        conn.commit()
        cursor.close()
        conn.close()

        # Set cookie and redirect to dashboard
        response = RedirectResponse(url="/student_dashboard", status_code=302)
        response.set_cookie(key="name", value=name)
        return response

    except mysql.connector.Error as err:
        return templates.TemplateResponse(
            "student_signup.html",
            {
                "request": request,
                "error": "Database error: " + str(err)
            }
        )

# ----------------- Student Login ------------------
@app.get("/student_login", response_class=HTMLResponse)
def student_login(request: Request):
    return templates.TemplateResponse("student_login.html", {"request": request})

from fastapi.responses import RedirectResponse
@app.post("/student_login", response_class=HTMLResponse)
async def student_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM members WHERE name = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            response = RedirectResponse(url="/student_dashboard", status_code=302)
            response.set_cookie(key="name", value=user["name"])
            return response
        else:
            return templates.TemplateResponse(
                "student_login.html",
                {"request": request, "error": "Invalid username or password"}
            )
    except mysql.connector.Error as err:
        return templates.TemplateResponse(
            "student_login.html",
            {"request": request, "error": "Database error: " + str(err)}
        )

