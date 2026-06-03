# app.py
# Builds the StreamLit user interface

import streamlit as st
import pandas as pd

from config import JOB_STATUSES, DOCUMENT_TYPES, CONTACT_TYPES
from database import (
    initialize_database,
    add_job,
    get_jobs,
    update_job_status,
    add_document,
    get_documents,
    add_application,
    get_applications,
    add_contact,
    get_contacts,
)


st.set_page_config(
    page_title="Job Search Command Center",
    page_icon="💼",
    layout="wide",
)

initialize_database()

st.title("💼 Job Search Command Center")
st.write("A personal workflow system for saving jobs, managing documents, tracking applications, contacts, follow-ups, and interviews.")


# -----------------------------
# Sidebar Navigation
# -----------------------------

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Saved Jobs",
        "Documents",
        "Applications",
        "Contacts",
        "Workflow View",
    ],
)


# -----------------------------
# Dashboard
# -----------------------------

if page == "Dashboard":
    st.header("Dashboard")

    jobs = get_jobs()
    applications = get_applications()
    documents = get_documents()
    contacts = get_contacts()

    jobs_df = pd.DataFrame(
        jobs,
        columns=[
            "ID",
            "Company",
            "Title",
            "Location",
            "Salary",
            "Status",
            "Priority",
            "Job Link",
            "Notes",
            "Date Saved",
        ],
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Saved Jobs", len(jobs))
    col2.metric("Applications", len(applications))
    col3.metric("Documents", len(documents))
    col4.metric("Contacts", len(contacts))

    if jobs:
        st.subheader("Jobs by Status")
        status_counts = jobs_df["Status"].value_counts()
        st.bar_chart(status_counts)

        st.subheader("Recent Jobs")
        st.dataframe(jobs_df.head(10), use_container_width=True)
    else:
        st.info("No jobs saved yet.")


# -----------------------------
# Saved Jobs
# -----------------------------

elif page == "Saved Jobs":
    st.header("Saved Jobs")

    with st.expander("Add New Job", expanded=True):
        with st.form("add_job_form"):
            col1, col2 = st.columns(2)

            with col1:
                company = st.text_input("Company")
                title = st.text_input("Job Title")
                location = st.text_input("Location")
                salary = st.text_input("Salary / Pay Range")

            with col2:
                job_link = st.text_input("Job Link")
                status = st.selectbox("Status", JOB_STATUSES)
                priority = st.slider("Priority", 1, 5, 3)

            job_description = st.text_area("Job Description", height=200)
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Job")

            if submitted:
                if company and title:
                    add_job(
                        company,
                        title,
                        location,
                        job_link,
                        salary,
                        job_description,
                        status,
                        priority,
                        notes,
                    )
                    st.success("Job saved.")
                else:
                    st.error("Company and job title are required.")

    jobs = get_jobs()

    if jobs:
        df = pd.DataFrame(
            jobs,
            columns=[
                "ID",
                "Company",
                "Title",
                "Location",
                "Salary",
                "Status",
                "Priority",
                "Job Link",
                "Notes",
                "Date Saved",
            ],
        )

        st.subheader("All Saved Jobs")
        st.dataframe(df, use_container_width=True)

        st.subheader("Update Job Status")

        selected_job_id = st.selectbox("Select Job ID", df["ID"].tolist())
        new_status = st.selectbox("New Status", JOB_STATUSES)

        if st.button("Update Status"):
            update_job_status(selected_job_id, new_status)
            st.success("Status updated. Refresh the page to see the change.")
    else:
        st.info("No jobs saved yet.")


# -----------------------------
# Documents
# -----------------------------

elif page == "Documents":
    st.header("Documents")

    with st.expander("Add Document", expanded=True):
        with st.form("add_document_form"):
            name = st.text_input("Document Name")
            document_type = st.selectbox("Document Type", DOCUMENT_TYPES)
            file_path = st.text_input("File Path or Link")
            related_company = st.text_input("Related Company")
            related_job_title = st.text_input("Related Job Title")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Document")

            if submitted:
                if name:
                    add_document(
                        name,
                        document_type,
                        file_path,
                        related_company,
                        related_job_title,
                        notes,
                    )
                    st.success("Document saved.")
                else:
                    st.error("Document name is required.")

    documents = get_documents()

    if documents:
        df = pd.DataFrame(
            documents,
            columns=[
                "ID",
                "Name",
                "Type",
                "File Path",
                "Related Company",
                "Related Job Title",
                "Notes",
                "Date Added",
            ],
        )

        st.subheader("Saved Documents")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No documents saved yet.")


# -----------------------------
# Applications
# -----------------------------

elif page == "Applications":
    st.header("Applications")

    jobs = get_jobs()
    documents = get_documents()

    job_options = {
        f"{job[0]} - {job[1]} - {job[2]}": job[0]
        for job in jobs
    }

    document_options = {
        f"{doc[0]} - {doc[1]} ({doc[2]})": doc[0]
        for doc in documents
    }

    with st.expander("Log Application", expanded=True):
        with st.form("add_application_form"):
            selected_job = st.selectbox(
                "Related Job",
                list(job_options.keys()) if job_options else ["No saved jobs available"],
            )

            selected_resume = st.selectbox(
                "Resume Used",
                ["None"] + list(document_options.keys()),
            )

            selected_cover_letter = st.selectbox(
                "Cover Letter Used",
                ["None"] + list(document_options.keys()),
            )

            date_applied = st.date_input("Date Applied")
            application_portal = st.text_input("Application Portal")
            username_used = st.text_input("Username / Email Used")
            follow_up_date = st.date_input("Follow-Up Date")
            outcome = st.text_input("Outcome")
            notes = st.text_area("Application Notes")

            submitted = st.form_submit_button("Save Application")

            if submitted:
                if job_options and selected_job in job_options:
                    job_id = job_options[selected_job]

                    resume_id = None
                    if selected_resume != "None":
                        resume_id = document_options[selected_resume]

                    cover_letter_id = None
                    if selected_cover_letter != "None":
                        cover_letter_id = document_options[selected_cover_letter]

                    add_application(
                        job_id,
                        resume_id,
                        cover_letter_id,
                        str(date_applied),
                        application_portal,
                        username_used,
                        str(follow_up_date),
                        outcome,
                        notes,
                    )

                    update_job_status(job_id, "Applied")
                    st.success("Application logged.")
                else:
                    st.error("Save a job first before logging an application.")

    applications = get_applications()

    if applications:
        df = pd.DataFrame(
            applications,
            columns=[
                "ID",
                "Company",
                "Title",
                "Date Applied",
                "Application Portal",
                "Follow-Up Date",
                "Outcome",
                "Notes",
            ],
        )

        st.subheader("Application History")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No applications logged yet.")


# -----------------------------
# Contacts
# -----------------------------

elif page == "Contacts":
    st.header("Contacts")

    with st.expander("Add Contact", expanded=True):
        with st.form("add_contact_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name")
                company = st.text_input("Company")
                role = st.text_input("Role")

            with col2:
                contact_type = st.selectbox("Contact Type", CONTACT_TYPES)
                email = st.text_input("Email")
                linkedin = st.text_input("LinkedIn")

            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Contact")

            if submitted:
                if name:
                    add_contact(
                        name,
                        company,
                        role,
                        contact_type,
                        email,
                        linkedin,
                        notes,
                    )
                    st.success("Contact saved.")
                else:
                    st.error("Contact name is required.")

    contacts = get_contacts()

    if contacts:
        df = pd.DataFrame(
            contacts,
            columns=[
                "ID",
                "Name",
                "Company",
                "Role",
                "Type",
                "Email",
                "LinkedIn",
                "Notes",
                "Date Added",
            ],
        )

        st.subheader("Saved Contacts")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No contacts saved yet.")


# -----------------------------
# Workflow View
# -----------------------------

elif page == "Workflow View":
    st.header("Workflow View")

    jobs = get_jobs()

    if jobs:
        df = pd.DataFrame(
            jobs,
            columns=[
                "ID",
                "Company",
                "Title",
                "Location",
                "Salary",
                "Status",
                "Priority",
                "Job Link",
                "Notes",
                "Date Saved",
            ],
        )

        for status in JOB_STATUSES:
            status_df = df[df["Status"] == status]

            if not status_df.empty:
                st.subheader(status)
                st.dataframe(status_df, use_container_width=True)
    else:
        st.info("No jobs in workflow yet.")