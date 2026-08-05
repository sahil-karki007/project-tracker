import streamlit as st
import json
import os

st.set_page_config(page_title="Project Tracker", layout="centered")

# ---------- Persistence (JSON file on disk) ----------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects_data.json")


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"incoming": [], "ongoing": [], "complete": [], "next_id": 1}


def save_data():
    data = {
        "incoming": st.session_state.incoming,
        "ongoing": st.session_state.ongoing,
        "complete": st.session_state.complete,
        "next_id": st.session_state.next_id,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------- Mobile-friendly CSS ----------
st.markdown(
    """
    <style>
    /* Smaller, square-ish icon buttons (Start/Done/Edit/Delete) */
    div.stButton > button {
        padding: 0.4rem 0.4rem;
        font-size: 0.95rem;
    }
    /* Tabs a bit bigger & easier to tap on phones */
    button[data-baseweb="tab"] {
        font-size: 1rem;
        padding: 0.5rem 0.7rem;
    }
    /* Reduce side padding on small screens */
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

# ---------- Session State Setup ----------
if "data_loaded" not in st.session_state:
    saved = load_data()
    st.session_state.incoming = saved["incoming"]
    st.session_state.ongoing = saved["ongoing"]
    st.session_state.complete = saved["complete"]
    st.session_state.next_id = saved["next_id"]
    st.session_state.data_loaded = True
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None


# ---------- Helper Functions ----------
def add_project(name):
    if name.strip():
        st.session_state.incoming.append(
            {"id": st.session_state.next_id, "name": name.strip()}
        )
        st.session_state.next_id += 1
        save_data()


def move_project(project, from_list, to_list):
    from_list.remove(project)
    to_list.append(project)
    save_data()


def delete_project(project, from_list):
    from_list.remove(project)
    if st.session_state.editing_id == project["id"]:
        st.session_state.editing_id = None
    save_data()


def render_row(project, current_list, move_icon=None, move_label=None, move_target=None,
               show_edit=True, strikethrough=False):
    """Renders one project as a single compact row, matching the sketch layout."""
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
                if new_name.strip():
                    project["name"] = new_name.strip()
                st.session_state.editing_id = None
                save_data()
                st.rerun()
        with cancel_col:
            if st.button("✖️", key=f"cancel_{project['id']}", use_container_width=True, help="Cancel"):
                st.session_state.editing_id = None
                st.rerun()
        return

    # Build column widths depending on which buttons are shown
    n_action_buttons = (1 if move_label else 0) + (1 if show_edit else 0) + 1  # +1 for delete
    widths = [4] + [1] * n_action_buttons
    cols = st.columns(widths)

    display_name = f"~~{project['name']}~~" if strikethrough else project["name"]
    cols[0].write(display_name)

    idx = 1
    if move_label:
        with cols[idx]:
            if st.button(move_icon, key=f"move_{project['id']}", use_container_width=True, help=move_label):
                move_project(project, current_list, move_target)
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
            delete_project(project, current_list)
            st.rerun()


# ---------- Add New Project (Incoming only) ----------
with st.form("add_project_form", clear_on_submit=True):
    new_project_name = st.text_input("Project name", placeholder="New project name")
    submitted = st.form_submit_button("➕ Add to Incoming", use_container_width=True)
    if submitted:
        add_project(new_project_name)

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
    for project in st.session_state.incoming[:]:
        render_row(
            project,
            st.session_state.incoming,
            move_icon="▶️",
            move_label="Start",
            move_target=st.session_state.ongoing,
        )

with tab_ongoing:
    if not st.session_state.ongoing:
        st.caption("No ongoing projects yet.")
    for project in st.session_state.ongoing[:]:
        render_row(
            project,
            st.session_state.ongoing,
            move_icon="✅",
            move_label="Done",
            move_target=st.session_state.complete,
        )

with tab_complete:
    if not st.session_state.complete:
        st.caption("No completed projects yet.")
    for project in st.session_state.complete[:]:
        render_row(project, st.session_state.complete, show_edit=False, strikethrough=True)
