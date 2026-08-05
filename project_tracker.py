import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="Project Tracker",
    page_icon="https://raw.githubusercontent.com/sahil-karki007/project-tracker/main/app_icon.png",
    layout="centered",
)

# ---------- Mobile-friendly CSS ----------
st.markdown(
    """
    <style>
    div.stButton > button {
        padding: 0.4rem 0.4rem;
        font-size: 0.95rem;
    }
    button[data-baseweb="tab"] {
        font-size: 1rem;
        padding: 0.5rem 0.7rem;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📋 Project Tracker")

# ---------- Supabase Connection ----------
@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = get_client()


def refresh_state():
    """Pull the latest data from Supabase and split it into the 3 lists."""
    response = supabase.table("projects").select("*").order("id").execute()
    rows = response.data
    st.session_state.incoming = [r for r in rows if r["status"] == "incoming"]
    st.session_state.ongoing = [r for r in rows if r["status"] == "ongoing"]
    st.session_state.complete = [r for r in rows if r["status"] == "complete"]


# ---------- Session State Setup ----------
if "data_loaded" not in st.session_state:
    refresh_state()
    st.session_state.data_loaded = True
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


# ---------- Helper Functions (all write to Supabase, then refresh) ----------
def add_project(name):
    if name.strip():
        supabase.table("projects").insert({"name": name.strip(), "status": "incoming"}).execute()
        refresh_state()


def move_project(project_id, new_status):
    supabase.table("projects").update({"status": new_status}).eq("id", project_id).execute()
    refresh_state()


def delete_project(project_id):
    supabase.table("projects").delete().eq("id", project_id).execute()
    if st.session_state.editing_id == project_id:
        st.session_state.editing_id = None
    refresh_state()


def rename_project(project_id, new_name):
    if new_name.strip():
        supabase.table("projects").update({"name": new_name.strip()}).eq("id", project_id).execute()
    st.session_state.editing_id = None
    refresh_state()


def render_row(project, move_icon=None, move_label=None, move_target_status=None,
               show_edit=True, strikethrough=False):
    """Renders one project as a single compact row."""
    is_editing = st.session_state.editing_id == project["id"]

    if is_editing:
        name_col, save_col, cancel_col = st.columns([4, 1, 1])
        with name_col:
            new_name = st.text_input(
                "Rename",
                value=project["name"],
                key=f"rename_input_{project['id']}",
                label_visibility="collapsed",
            )
        with save_col:
            if st.button("💾", key=f"save_{project['id']}", use_container_width=True, help="Save"):
                rename_project(project["id"], new_name)
                st.rerun()
        with cancel_col:
            if st.button("✖️", key=f"cancel_{project['id']}", use_container_width=True, help="Cancel"):
                st.session_state.editing_id = None
                st.rerun()
        return

    n_action_buttons = (1 if move_label else 0) + (1 if show_edit else 0) + 1  # +1 for delete
    widths = [4] + [1] * n_action_buttons
    cols = st.columns(widths)

    display_name = f"~~{project['name']}~~" if strikethrough else project["name"]
    cols[0].write(display_name)

    idx = 1
    if move_label:
        with cols[idx]:
            if st.button(move_icon, key=f"move_{project['id']}", use_container_width=True, help=move_label):
                move_project(project["id"], move_target_status)
                st.rerun()
        idx += 1

    if show_edit:
        with cols[idx]:
            if st.button("✏️", key=f"edit_{project['id']}", use_container_width=True, help="Edit"):
                st.session_state.editing_id = project["id"]
                st.rerun()
        idx += 1

    with cols[idx]:
        if st.button("🗑️", key=f"delete_{project['id']}", use_container_width=True, help="Delete"):
            delete_project(project["id"])
            st.rerun()


# ---------- Add New Project (Incoming only) ----------
with st.form("add_project_form", clear_on_submit=True):
    new_project_name = st.text_input("Project name", placeholder="New project name")
    submitted = st.form_submit_button("➕ Add to Incoming", use_container_width=True)
    if submitted:
        add_project(new_project_name)
        st.rerun()

st.divider()

# ---------- Tabs (Incoming / Ongoing / Completed) ----------
tab_incoming, tab_ongoing, tab_complete = st.tabs(
    [
        f"📥 Incoming ({len(st.session_state.incoming)})",
        f"🚧 Ongoing ({len(st.session_state.ongoing)})",
        f"🏁 Completed ({len(st.session_state.complete)})",
    ]
)

with tab_incoming:
    if not st.session_state.incoming:
        st.caption("No incoming projects yet. Add one above.")
    for project in st.session_state.incoming:
        render_row(
            project,
            move_icon="▶️",
            move_label="Start",
            move_target_status="ongoing",
        )

with tab_ongoing:
    if not st.session_state.ongoing:
        st.caption("No ongoing projects yet.")
    for project in st.session_state.ongoing:
        render_row(
            project,
            move_icon="✅",
            move_label="Done",
            move_target_status="complete",
        )

with tab_complete:
    if not st.session_state.complete:
        st.caption("No completed projects yet.")
    for project in st.session_state.complete:
        render_row(project, show_edit=False, strikethrough=True)
