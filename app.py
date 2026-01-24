import streamlit as st
import json
import countryflag # type: ignore
import tools # type: ignore
from streamlit_autorefresh import st_autorefresh # type: ignore
import pandas as pd
from tools import update_results
from dropbox_handler import dropbox_upload, dropbox_load
import bcrypt


import sys
sys.stdout.reconfigure(encoding='utf-8')

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "glogged_in" not in st.session_state:
    st.session_state.glogged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "group" not in st.session_state:
    st.session_state.group =""
if "page" not in st.session_state:
    st.session_state.page ="home"
if "quote" not in st.session_state:
    st.session_state.quote = tools.gen_quote()
draft_status = "ongoing"

# PAGES --------------------------------------------

# --- Group PAGE ---
def group_page():
    st.image("BeaversLogoButton.svg")
    st.title("🔐 Group Portal")

    groups = dropbox_load("groups") or {}

    tab_login, tab_create = st.tabs(["Join group", "Create new group"])

    # --- JOIN EXISTING GROUP ---
    with tab_login:
        groupname = st.text_input("Group name")
        if st.button("Continue"):
            if groupname in groups:
                st.session_state.group = groupname
                st.session_state.glogged_in = True
                st.rerun()
            else:
                st.error("Group does not exist")

    # --- CREATE NEW GROUP ---
    with tab_create:
        new_group = st.text_input("New group name")
        leader = st.text_input("Group leader username")
        password = st.text_input("Leader password", type="password")

        if st.button("Create group"):
            if new_group in groups:
                st.error("Group already exists")
                return

            users = dropbox_load("users") or {}

            users[leader] = {
                "password": hash_password(password),
                "group": new_group,
                "role": "leader"
            }

            groups[new_group] = {
                "leader": leader,
                "complete": False,
                "members": [leader]
            }

            dropbox_upload(users, "users")
            dropbox_upload(groups, "groups")

            st.success("Group created!")
            st.session_state.group = new_group
            st.session_state.glogged_in = True
            st.rerun()


# --- LOGIN PAGE ---
def login_page():
    st.title(f"Welcome to {st.session_state.group}")

    users = dropbox_load("users") or {}
    groups = dropbox_load("groups")

    group = groups[st.session_state.group]
    group_complete = group["complete"]

    tab_login, tab_register = st.tabs(["Login", "Create account"])

    # --- LOGIN ---
    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in users and verify_password(password, users[username]["password"]):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    # --- REGISTER ---
    with tab_register:
        if group_complete:
            st.warning("This group is closed. No new accounts allowed.")
        else:
            new_user = st.text_input("Username", key="reg_user")
            new_pass = st.text_input("Password", type="password", key="reg_pass")

            if st.button("Create account"):
                if new_user in users:
                    st.error("User already exists")
                    return

                users[new_user] = {
                    "password": hash_password(new_pass),
                    "group": st.session_state.group,
                    "role": "member"
                }

                groups[st.session_state.group]["members"].append(new_user)

                dropbox_upload(users, "users")
                dropbox_upload(groups, "groups")

                st.success("Account created. Please log in.")

# --- MAIN APP PAGE ---
def main_app():
    st.sidebar.write(f"👋 Welcome, {st.session_state.username}")
    st.sidebar.button("**Home**", type="tertiary", on_click=home)
    st.sidebar.button("**Ranking**", type="tertiary", on_click=ranking)
    st.sidebar.button("**My Team**", type="tertiary", on_click=team)
    st.sidebar.button("**Rider Ranking**", type="tertiary", on_click=riderranking)
    st.sidebar.button("**Draft**", type="tertiary", on_click=draft)
    st.sidebar.button("**Log out**", type="tertiary", on_click=logout)
    
    groups = dropbox_load("groups")
    group = groups[st.session_state.group]

    if st.session_state.username == group["leader"]:
        st.sidebar.markdown("### Group Admin")
        st.sidebar.markdown(f"Members: {', '.join(group['members'])}")

        if not group["complete"]:
            if st.sidebar.button("✅ Mark group complete"):
                group["complete"] = True
                close = tools.close_group(group, st.session_state.group)
                dropbox_upload(groups, "groups")
                st.sidebar.success("Group closed!")
                st.rerun()

    if st.session_state.page == "home":
        st.title("HOME")
        st.write(st.session_state.quote)
        last_race_module()
    elif st.session_state.page == "draft":
        draft_page()
    elif st.session_state.page == 'team':
        team_page()
    elif st.session_state.page == 'ranking':
        ranking_page()
    elif st.session_state.page == 'rider':
        rider_page()

def draft_page():

    groups = dropbox_load("groups")
    if not groups[st.session_state.group]["complete"]:
        st.warning("Draft cannot start until the group is complete.")
        return


    


    draft_track = dropbox_load("draft")
    r, p, player, status = tools.check_draft(st.session_state.group, draft_track)
    
    if status == "ongoing":
        if player != st.session_state.username:
            st_autorefresh(interval=8000, key="draft_refresh")
        st.title(f"Draft Ongoing")
        st.title(f"Round: {r} Pick: {p} Player: {player}")
        indx, data = tools.draft_table(st.session_state.group, draft_track)
        table = pd.DataFrame(data, index=indx)
        ttable = table.T
        st.table(ttable)
        if player == st.session_state.username:
            names_list = tools.names_list(st.session_state.group, draft_track)
            selected_rider = st.selectbox('Select rider:', names_list, index=None)
            if selected_rider:
                rider_idx = rider_names[selected_rider]
                slct_rider_url = list(riders_dict.keys())[rider_idx]
                
                flag = countryflag.getflag(riders_dict[slct_rider_url][2])
                team_name = riders_dict[slct_rider_url][1]

                
                st.markdown(
                f"""
                <div style="
                    border:1px solid rgba(200,200,200,0.3);
                    border-radius:8px;
                    padding:12px 15px;
                    margin-top:10px;
                    background-color:rgba(240,240,240,0.4);
                ">
                    <h3 style="margin-bottom:5px;">{flag} {selected_rider}</h3>
                    <p style="margin-top:0px;"><b>Team:</b> {team_name}</p>
                </div>
                """,
                unsafe_allow_html=True
                )
                st.write("")
                if st.button("Confirm"):
                    st.session_state.quote = tools.gen_quote()
                    tools.update_draft(st.session_state.group, r, p, slct_rider_url)
                    st.rerun()
        else:
            st.write(st.session_state.quote)
    elif status == "finished":
        tools.finish_draft(st.session_state.group)
        st.title("Draft Finished")
        indx, data = tools.draft_table_f(st.session_state.group, draft_track)
        table = pd.DataFrame(data, index=indx)
        ttable = table.T
        st.table(ttable)


def team_page():
    #update_results()
    draft_track = dropbox_load("draft")
    r, p, player, status = tools.check_draft(st.session_state.group, draft_track)
    if status == 'ongoing':
        st.title("Draft not finished, check back after draft!")
    if status == 'finished':
        teams = load_teams()
        data = tools.team_table(st.session_state.group, st.session_state.username, teams)
        table = pd.DataFrame(data).set_index('Riders').sort_values(by='Pnts', ascending=False)
        st.table(table)

def ranking_page():
    #update_results()
    teams = load_teams()
    group = {'Team': [],'Points': []}
    for team in teams[st.session_state.group]:
        data = tools.team_table(st.session_state.group, team, teams)
        tbl = pd.DataFrame(data).set_index('Riders')
        total = tbl['Pnts'].sum()
        group['Team'].append(team)
        group['Points'].append(total)
    table = pd.DataFrame(group).set_index('Team').sort_values(by='Points', ascending=False)
    st.table(table)

def rider_page():
    data = tools.rider_table()
    tbl = pd.DataFrame(data).set_index('Riders').sort_values(by='Pnts', ascending=False)
    st.table(tbl)




def last_race_module():
    data = tools.latest_results()
    st.write("**Results from today**")
    for race in data['today']:
        st.write(f'Top 25 from {race}')
        table = pd.DataFrame(data['today'][race]).set_index("Place")
        st.table(table)
    st.write("**Results from yesterday**")
    for race in data['yesterday']:
        st.write(f'Top 25 from {race}')
        table = pd.DataFrame(data['yesterday'][race]).set_index("Place")
        st.table(table)



# Functions --------------------------------------------------------------------

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.glogged_in = False
    st.session_state.username = ""
    st.session_state.group = ""
    st.session_state.page = "home"
    st.rerun()

def draft():
    st.session_state.page = "draft"

def home():
    st.session_state.page = "home"
def team():
    st.session_state.page = "team"
def ranking():
    st.session_state.page = "ranking"
def riderranking():
    st.session_state.page = "rider"

def load_all_riders():
    return dropbox_load("comp_riders")

def load_rider_names():
    return dropbox_load("riders_names")


def load_teams():
    return dropbox_load("teams")


def save_draft(draft):
    dropbox_upload(draft, "draft")
        # {group: {round: {pick: [rider url, player]}}}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())



# --- APP FLOW ---
riders_dict = load_all_riders()
rider_names = load_rider_names()
all_riders_names = list(rider_names.keys())

draft_track = dropbox_load("draft")
races = dropbox_load("new_races")


if st.session_state.glogged_in and not st.session_state.logged_in:
    login_page()
elif st.session_state.glogged_in and st.session_state.logged_in:
    main_app()
else:
    group_page()



