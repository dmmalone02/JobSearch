# app.py
# Builds the Streamlit user interface

from datetime import date, timedelta

import streamlit as st
import pandas as pd

from config import JOB_STATUSES, DOCUMENT_TYPES, CONTACT_TYPES
from database import (
    initialize_database,
    add_job,
    get_jobs,
    get_job,
    update_job,
    update_job_status,
    delete_job,
    add_document,
    get_documents,
    delete_document,
    add_application,
    get_applications,
    update_application_outcome,
    delete_application,
    add_contact,
    get_contacts,
    delete_contact,
    add_interview,
    get_interviews,
    mark_follow_up_sent,
    delete_interview,
)

JOB_COLUMNS = [
    "ID", "Company", "Title", "Location", "Salary",
    "Status", "Priority", "Job Link", "Notes", "Date Saved",
]

APPLICATION_COLUMNS = [
    "ID", "Company", "Title", "Date Applied",
    "Application Portal", "Follow-Up Date", "Outcome", "Notes",
]

INTERVIEW_COLUMNS = [
    "ID", "Company", "Title", "Interview Date", "Type",
    "Interviewer", "Follow-Up Sent", "Outcome", "Notes",
]

INTERVIEW_TYPES = [
    "Phone Screen", "Technical", "Behavioral",
    "Panel", "Onsite", "Final Round", "Other",
]


st.set_page_config(
    page_title="Job Search Command Center",
    page_icon="💼",
    layout="wide",
)

initialize_database()

st.title("💼 Job Search Command Center")
st.caption(
    "A personal workflow system for saving jobs, managing documents, "
    "tracking applications, contacts, follow-ups, and interviews."
)


def jobs_dataframe():
    jobs = get_jobs()
    if not jobs:
        return None
    return pd.DataFrame(jobs, columns=JOB_COLUMNS)


def applications_dataframe():
    applications = get_applications()
    if not applications:
        return None
    return pd.DataFrame(applications, columns=APPLICATION_COLUMNS)


def interviews_dataframe():
    interviews = get_interviews()
    if not interviews:
        return None
    return pd.DataFrame(interviews, columns=INTERVIEW_COLUMNS)


def show_jobs_table(df):
    """Render a jobs dataframe with a clickable job link column."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Job Link": st.column_config.LinkColumn("Job Link"),
            "Priority": st.column_config.NumberColumn("Priority", format="%d ⭐"),
        },
    )


def job_label_map(jobs):
    return {f"#{job[0]} — {job[1]} — {job[2]}": job[0] for job in jobs}


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
        "Interviews",
        "Contacts",
        "Workflow View",
    ],
)


# -----------------------------
# Dashboard
# -----------------------------

if page == "Dashboard":
    st.header("Dashboard")

    jobs_df = jobs_dataframe()
    apps_df = applications_dataframe()
    interviews_df = interviews_dataframe()
    documents = get_documents()
    contacts = get_contacts()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Saved Jobs", len(jobs_df) if jobs_df is not None else 0)
    col2.metric("Applications", len(apps_df) if apps_df is not None else 0)
    col3.metric("Interviews", len(interviews_df) if interviews_df is not None else 0)
    col4.metric("Documents", len(documents))
    col5.metric("Contacts", len(contacts))

    today = pd.Timestamp(date.today())

    # --- Upcoming interviews ---
    if interviews_df is not None:
        upcoming_interviews = interviews_df.copy()
        upcoming_interviews["Interview Date"] = pd.to_datetime(
            upcoming_interviews["Interview Date"], errors="coerce"
        )
        upcoming_interviews = upcoming_interviews.dropna(subset=["Interview Date"])
        upcoming_interviews = upcoming_interviews[
            upcoming_interviews["Interview Date"] >= today
        ].sort_values("Interview Date")

        if not upcoming_interviews.empty:
            st.subheader("📅 Upcoming Interviews")
            for _, row in upcoming_interviews.head(5).iterrows():
                st.info(
                    f"**{row['Company']}** — {row['Title']} · {row['Type']} "
                    f"on {row['Interview Date'].date()}"
                    + (f" with {row['Interviewer']}" if row["Interviewer"] else "")
                )

        # --- Interview thank-you note reminders ---
        needs_followup = interviews_df.copy()
        needs_followup["Interview Date"] = pd.to_datetime(
            needs_followup["Interview Date"], errors="coerce"
        )
        needs_followup = needs_followup.dropna(subset=["Interview Date"])
        needs_followup = needs_followup[
            (needs_followup["Interview Date"] < today)
            & (needs_followup["Follow-Up Sent"] != "Yes")
        ]

        if not needs_followup.empty:
            st.subheader("✉️ Thank-You Notes To Send")
            for _, row in needs_followup.iterrows():
                st.warning(
                    f"You haven't sent a follow-up for your "
                    f"{row['Interview Date'].date()} interview with "
                    f"**{row['Company']}** ({row['Title']})."
                )

    # --- Application follow-up reminders ---
    if apps_df is not None:
        reminders = apps_df.copy()
        reminders["Follow-Up Date"] = pd.to_datetime(
            reminders["Follow-Up Date"], errors="coerce"
        )
        reminders = reminders.dropna(subset=["Follow-Up Date"])

        soon = today + pd.Timedelta(days=7)
        overdue = reminders[reminders["Follow-Up Date"] < today]
        upcoming = reminders[
            (reminders["Follow-Up Date"] >= today)
            & (reminders["Follow-Up Date"] <= soon)
        ]

        if not overdue.empty or not upcoming.empty:
            st.subheader("🔔 Application Follow-Ups")

            for _, row in overdue.iterrows():
                st.error(
                    f"Overdue: follow up with **{row['Company']}** "
                    f"({row['Title']}) — was due {row['Follow-Up Date'].date()}"
                )

            for _, row in upcoming.iterrows():
                st.warning(
                    f"Coming up: follow up with **{row['Company']}** "
                    f"({row['Title']}) on {row['Follow-Up Date'].date()}"
                )

    if jobs_df is not None:
        left, right = st.columns(2)

        with left:
            st.subheader("Jobs by Status")
            status_counts = jobs_df["Status"].value_counts()
            st.bar_chart(status_counts)

        with right:
            st.subheader("Top Priority Jobs")
            top = jobs_df.sort_values(
                ["Priority", "Date Saved"], ascending=[False, False]
            ).head(5)
            show_jobs_table(top[["Company", "Title", "Status", "Priority", "Job Link"]])

        st.subheader("Recently Saved")
        show_jobs_table(jobs_df.head(10))
    else:
        st.info("No jobs saved yet. Head to **Saved Jobs** to add your first one.")


# -----------------------------
# Saved Jobs
# -----------------------------

elif page == "Saved Jobs":
    st.header("Saved Jobs")

    with st.expander("Add New Job", expanded=False):
        with st.form("add_job_form", clear_on_submit=True):
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
                        company, title, location, job_link, salary,
                        job_description, status, priority, notes,
                    )
                    st.success("Job saved.")
                    st.rerun()
                else:
                    st.error("Company and job title are required.")

    jobs_df = jobs_dataframe()

    if jobs_df is not None:
        st.subheader("All Saved Jobs")

        # --- Search and filter ---
        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            search = st.text_input("Search by company or title", "")
        with fcol2:
            status_filter = st.multiselect("Status", JOB_STATUSES)
        with fcol3:
            min_priority = st.slider("Min priority", 1, 5, 1)

        filtered = jobs_df.copy()
        if search:
            mask = (
                filtered["Company"].str.contains(search, case=False, na=False)
                | filtered["Title"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        if status_filter:
            filtered = filtered[filtered["Status"].isin(status_filter)]
        filtered = filtered[filtered["Priority"] >= min_priority]

        st.caption(f"Showing {len(filtered)} of {len(jobs_df)} jobs")
        show_jobs_table(filtered)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Jobs as CSV",
            data=csv,
            file_name="saved_jobs.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Edit or Delete a Job")

        job_labels = job_label_map(get_jobs())
        selected_label = st.selectbox("Select Job", list(job_labels.keys()))
        selected_id = job_labels[selected_label]

        job = get_job(selected_id)
        # get_job returns: id, company, title, location, job_link, salary,
        #                  job_description, status, priority, notes, date_saved

        with st.form("edit_job_form"):
            col1, col2 = st.columns(2)

            with col1:
                e_company = st.text_input("Company", value=job[1] or "")
                e_title = st.text_input("Job Title", value=job[2] or "")
                e_location = st.text_input("Location", value=job[3] or "")
                e_salary = st.text_input("Salary / Pay Range", value=job[5] or "")

            with col2:
                e_job_link = st.text_input("Job Link", value=job[4] or "")
                e_status = st.selectbox(
                    "Status",
                    JOB_STATUSES,
                    index=JOB_STATUSES.index(job[7]) if job[7] in JOB_STATUSES else 0,
                )
                e_priority = st.slider("Priority", 1, 5, int(job[8] or 3))

            e_description = st.text_area("Job Description", value=job[6] or "", height=200)
            e_notes = st.text_area("Notes", value=job[9] or "")

            save_edit = st.form_submit_button("Save Changes")

            if save_edit:
                if e_company and e_title:
                    update_job(
                        selected_id, e_company, e_title, e_location,
                        e_job_link, e_salary, e_description,
                        e_status, e_priority, e_notes,
                    )
                    st.success("Job updated.")
                    st.rerun()
                else:
                    st.error("Company and job title are required.")

        with st.expander("🗑️ Delete This Job"):
            st.warning(
                "Deleting a job also deletes its logged applications and "
                "interviews. This cannot be undone."
            )
            confirm = st.checkbox("I understand, delete this job permanently")
            if st.button("Delete Job", type="primary", disabled=not confirm):
                delete_job(selected_id)
                st.success("Job deleted.")
                st.rerun()
    else:
        st.info("No jobs saved yet.")


# -----------------------------
# Documents
# -----------------------------

elif page == "Documents":
    st.header("Documents")

    with st.expander("Add Document", expanded=False):
        with st.form("add_document_form", clear_on_submit=True):
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
                        name, document_type, file_path,
                        related_company, related_job_title, notes,
                    )
                    st.success("Document saved.")
                    st.rerun()
                else:
                    st.error("Document name is required.")

    documents = get_documents()

    if documents:
        df = pd.DataFrame(
            documents,
            columns=[
                "ID", "Name", "Type", "File Path",
                "Related Company", "Related Job Title", "Notes", "Date Added",
            ],
        )

        st.subheader("Saved Documents")

        type_filter = st.multiselect("Filter by type", DOCUMENT_TYPES)
        view_df = df[df["Type"].isin(type_filter)] if type_filter else df

        st.dataframe(view_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Delete a Document")

        doc_labels = {
            f"#{row.ID} — {row.Name} ({row.Type})": row.ID
            for row in df.itertuples()
        }
        selected_doc = st.selectbox("Select Document", list(doc_labels.keys()))
        st.caption(
            "Deleting a document won't delete applications that used it — "
            "they'll just no longer reference it."
        )
        if st.button("Delete Document"):
            delete_document(doc_labels[selected_doc])
            st.success("Document deleted.")
            st.rerun()
    else:
        st.info("No documents saved yet.")


# -----------------------------
# Applications
# -----------------------------

elif page == "Applications":
    st.header("Applications")

    jobs = get_jobs()
    documents = get_documents()

    job_options = job_label_map(jobs)

    resume_options = {
        f"#{doc[0]} — {doc[1]}": doc[0]
        for doc in documents
        if doc[2] and "resume" in str(doc[2]).lower()
    } or {
        f"#{doc[0]} — {doc[1]} ({doc[2]})": doc[0]
        for doc in documents
    }

    cover_letter_options = {
        f"#{doc[0]} — {doc[1]}": doc[0]
        for doc in documents
        if doc[2] and "cover" in str(doc[2]).lower()
    } or {
        f"#{doc[0]} — {doc[1]} ({doc[2]})": doc[0]
        for doc in documents
    }

    if not jobs:
        st.warning("Save a job first before logging an application.")
    else:
        with st.expander("Log Application", expanded=False):
            with st.form("add_application_form", clear_on_submit=True):
                selected_job = st.selectbox("Related Job", list(job_options.keys()))

                col1, col2 = st.columns(2)
                with col1:
                    selected_resume = st.selectbox(
                        "Resume Used", ["None"] + list(resume_options.keys())
                    )
                    date_applied = st.date_input("Date Applied", value=date.today())
                    application_portal = st.text_input("Application Portal")
                    username_used = st.text_input("Username / Email Used")
                with col2:
                    selected_cover_letter = st.selectbox(
                        "Cover Letter Used",
                        ["None"] + list(cover_letter_options.keys()),
                    )
                    follow_up_date = st.date_input(
                        "Follow-Up Date", value=date.today() + timedelta(days=7)
                    )
                    outcome = st.text_input("Outcome")

                notes = st.text_area("Application Notes")

                submitted = st.form_submit_button("Save Application")

                if submitted:
                    job_id = job_options[selected_job]

                    resume_id = (
                        resume_options[selected_resume]
                        if selected_resume != "None"
                        else None
                    )
                    cover_letter_id = (
                        cover_letter_options[selected_cover_letter]
                        if selected_cover_letter != "None"
                        else None
                    )

                    add_application(
                        job_id, resume_id, cover_letter_id,
                        str(date_applied), application_portal, username_used,
                        str(follow_up_date), outcome, notes,
                    )

                    update_job_status(job_id, "Applied")
                    st.success("Application logged.")
                    st.rerun()

    apps_df = applications_dataframe()

    if apps_df is not None:
        st.subheader("Application History")
        st.dataframe(apps_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Update Outcome / Delete")

        app_labels = {
            f"#{row.ID} — {row.Company} — {row.Title} (applied {row._4})": row.ID
            for row in apps_df.itertuples()
        }
        selected_app = st.selectbox("Select Application", list(app_labels.keys()))
        selected_app_id = app_labels[selected_app]

        ocol1, ocol2 = st.columns([3, 1])
        with ocol1:
            new_outcome = st.text_input(
                "New Outcome (e.g. Rejected, Phone Screen, Offer)"
            )
        with ocol2:
            st.write("")
            st.write("")
            if st.button("Update Outcome", use_container_width=True):
                update_application_outcome(selected_app_id, new_outcome)
                st.success("Outcome updated.")
                st.rerun()

        if st.button("🗑️ Delete Application"):
            delete_application(selected_app_id)
            st.success("Application deleted.")
            st.rerun()
    else:
        st.info("No applications logged yet.")


# -----------------------------
# Interviews
# -----------------------------

elif page == "Interviews":
    st.header("Interviews")

    jobs = get_jobs()
    job_options = job_label_map(jobs)

    if not jobs:
        st.warning("Save a job first before logging an interview.")
    else:
        with st.expander("Log Interview", expanded=False):
            with st.form("add_interview_form", clear_on_submit=True):
                selected_job = st.selectbox("Related Job", list(job_options.keys()))

                col1, col2 = st.columns(2)
                with col1:
                    interview_date = st.date_input("Interview Date", value=date.today())
                    interview_type = st.selectbox("Interview Type", INTERVIEW_TYPES)
                with col2:
                    interviewer = st.text_input("Interviewer(s)")
                    follow_up_sent = st.selectbox("Follow-Up Sent?", ["No", "Yes"])

                preparation_notes = st.text_area("Preparation Notes")
                questions_asked = st.text_area("Questions Asked")
                outcome = st.text_input("Outcome")
                notes = st.text_area("Notes")

                submitted = st.form_submit_button("Save Interview")

                if submitted:
                    job_id = job_options[selected_job]
                    add_interview(
                        job_id, str(interview_date), interview_type,
                        interviewer, preparation_notes, questions_asked,
                        follow_up_sent, outcome, notes,
                    )
                    update_job_status(job_id, "Interviewing")
                    st.success("Interview logged.")
                    st.rerun()

    interviews_df = interviews_dataframe()

    if interviews_df is not None:
        st.subheader("Interview History")
        st.dataframe(interviews_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Manage Interviews")

        int_labels = {
            f"#{row.ID} — {row.Company} — {row._5} on {row._4}": row.ID
            for row in interviews_df.itertuples()
        }
        selected_int = st.selectbox("Select Interview", list(int_labels.keys()))
        selected_int_id = int_labels[selected_int]

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            if st.button("✉️ Mark Follow-Up Sent", use_container_width=True):
                mark_follow_up_sent(selected_int_id)
                st.success("Marked as sent.")
                st.rerun()
        with mcol2:
            if st.button("🗑️ Delete Interview", use_container_width=True):
                delete_interview(selected_int_id)
                st.success("Interview deleted.")
                st.rerun()
    else:
        st.info("No interviews logged yet.")


# -----------------------------
# Contacts
# -----------------------------

elif page == "Contacts":
    st.header("Contacts")

    with st.expander("Add Contact", expanded=False):
        with st.form("add_contact_form", clear_on_submit=True):
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
                        name, company, role, contact_type,
                        email, linkedin, notes,
                    )
                    st.success("Contact saved.")
                    st.rerun()
                else:
                    st.error("Contact name is required.")

    contacts = get_contacts()

    if contacts:
        df = pd.DataFrame(
            contacts,
            columns=[
                "ID", "Name", "Company", "Role", "Type",
                "Email", "LinkedIn", "Notes", "Date Added",
            ],
        )

        st.subheader("Saved Contacts")

        search = st.text_input("Search contacts", "")
        view_df = df
        if search:
            mask = (
                df["Name"].str.contains(search, case=False, na=False)
                | df["Company"].str.contains(search, case=False, na=False)
            )
            view_df = df[mask]

        st.dataframe(
            view_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "LinkedIn": st.column_config.LinkColumn("LinkedIn"),
            },
        )

        st.divider()
        st.subheader("Delete a Contact")

        contact_labels = {
            f"#{row.ID} — {row.Name} ({row.Company})": row.ID
            for row in df.itertuples()
        }
        selected_contact = st.selectbox("Select Contact", list(contact_labels.keys()))
        if st.button("Delete Contact"):
            delete_contact(contact_labels[selected_contact])
            st.success("Contact deleted.")
            st.rerun()
    else:
        st.info("No contacts saved yet.")


# -----------------------------
# Workflow View
# -----------------------------

elif page == "Workflow View":
    st.header("Workflow View")

    jobs_df = jobs_dataframe()

    if jobs_df is not None:
        statuses_with_jobs = [
            s for s in JOB_STATUSES if not jobs_df[jobs_df["Status"] == s].empty
        ]

        if not statuses_with_jobs:
            st.info("No jobs in workflow yet.")
        else:
            for i in range(0, len(statuses_with_jobs), 3):
                chunk = statuses_with_jobs[i : i + 3]
                cols = st.columns(3)

                for col, status in zip(cols, chunk):
                    status_df = jobs_df[jobs_df["Status"] == status]
                    with col:
                        st.subheader(f"{status} ({len(status_df)})")
                        for row in status_df.itertuples():
                            with st.container(border=True):
                                st.markdown(f"**{row.Company}**")
                                st.caption(row.Title)
                                meta = []
                                if row.Location:
                                    meta.append(str(row.Location))
                                if row.Salary:
                                    meta.append(str(row.Salary))
                                if meta:
                                    st.caption(" · ".join(meta))
                                st.caption(f"Priority: {'⭐' * int(row.Priority)}")
    else:
        st.info("No jobs in workflow yet.")