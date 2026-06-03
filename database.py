# database.py
# Handles SQLite database logic  

import sqlite3
from pathlib import Path


DB_PATH = Path("data/jobsearch.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            job_link TEXT,
            salary TEXT,
            job_description TEXT,
            status TEXT NOT NULL,
            priority INTEGER DEFAULT 3,
            notes TEXT,
            date_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT,
            related_company TEXT,
            related_job_title TEXT,
            notes TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_document_id INTEGER,
            cover_letter_document_id INTEGER,
            date_applied TEXT,
            application_portal TEXT,
            username_used TEXT,
            follow_up_date TEXT,
            outcome TEXT,
            notes TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            FOREIGN KEY(resume_document_id) REFERENCES documents(id),
            FOREIGN KEY(cover_letter_document_id) REFERENCES documents(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            role TEXT,
            contact_type TEXT,
            email TEXT,
            linkedin TEXT,
            notes TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            interview_date TEXT,
            interview_type TEXT,
            interviewer TEXT,
            preparation_notes TEXT,
            questions_asked TEXT,
            follow_up_sent TEXT DEFAULT 'No',
            outcome TEXT,
            notes TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Jobs
# -----------------------------

def add_job(company, title, location, job_link, salary, job_description, status, priority, notes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (
            company,
            title,
            location,
            job_link,
            salary,
            job_description,
            status,
            priority,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company,
        title,
        location,
        job_link,
        salary,
        job_description,
        status,
        priority,
        notes,
    ))

    conn.commit()
    conn.close()


def get_jobs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company,
            title,
            location,
            salary,
            status,
            priority,
            job_link,
            notes,
            date_saved
        FROM jobs
        ORDER BY date_saved DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def update_job_status(job_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET status = ?
        WHERE id = ?
    """, (status, job_id))

    conn.commit()
    conn.close()


# -----------------------------
# Documents
# -----------------------------

def add_document(name, document_type, file_path, related_company, related_job_title, notes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documents (
            name,
            document_type,
            file_path,
            related_company,
            related_job_title,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        document_type,
        file_path,
        related_company,
        related_job_title,
        notes,
    ))

    conn.commit()
    conn.close()


def get_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            document_type,
            file_path,
            related_company,
            related_job_title,
            notes,
            date_added
        FROM documents
        ORDER BY date_added DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# -----------------------------
# Applications
# -----------------------------

def add_application(
    job_id,
    resume_document_id,
    cover_letter_document_id,
    date_applied,
    application_portal,
    username_used,
    follow_up_date,
    outcome,
    notes,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (
            job_id,
            resume_document_id,
            cover_letter_document_id,
            date_applied,
            application_portal,
            username_used,
            follow_up_date,
            outcome,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        resume_document_id,
        cover_letter_document_id,
        date_applied,
        application_portal,
        username_used,
        follow_up_date,
        outcome,
        notes,
    ))

    conn.commit()
    conn.close()


def get_applications():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            applications.id,
            jobs.company,
            jobs.title,
            applications.date_applied,
            applications.application_portal,
            applications.follow_up_date,
            applications.outcome,
            applications.notes
        FROM applications
        LEFT JOIN jobs ON applications.job_id = jobs.id
        ORDER BY applications.date_applied DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# -----------------------------
# Contacts
# -----------------------------

def add_contact(name, company, role, contact_type, email, linkedin, notes):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO contacts (
            name,
            company,
            role,
            contact_type,
            email,
            linkedin,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        company,
        role,
        contact_type,
        email,
        linkedin,
        notes,
    ))

    conn.commit()
    conn.close()


def get_contacts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            company,
            role,
            contact_type,
            email,
            linkedin,
            notes,
            date_added
        FROM contacts
        ORDER BY date_added DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows