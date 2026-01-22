import json
import random
from PCScraper.scrapers import result_scraper, info_scraper, gc_scraper, stage_scraper
from dropbox_handler import dropbox_upload, dropbox_load
import random
from datetime import datetime
import streamlit as st

def check_draft(group_name, draft_track):
    """
    Checks the draft tracking dictionary to determine the next pick's details.

    Args:
        draft_track (dict): A dictionary with the structure
                            {group: {round: {pick: [rider_url, player]}}}.

    Returns:
        tuple: (current_round, current_pick, player_to_pick)
               or None if the dictionary is empty (no picks made).
    """


    
    # Assuming there's only one group based on the example structure,
    # we extract the inner draft details.
    if not draft_track:
        return None # Handle case of empty draft_track
        
    draft_rounds = draft_track[group_name]

    # Find the highest round that has been started
    # Note: Keys are strings, so we convert to int for comparison
    rounds = sorted([int(r) for r in draft_rounds.keys()])
    
    for round in rounds:
        for pick in sorted([int(r) for r in draft_rounds[str(round)].keys()]):
            if draft_rounds[str(round)][str(pick)][0] == "":
                next_round = str(round)
                next_pick = str(pick)
                next_player = draft_rounds[str(round)][str(pick)][1]
                status = "ongoing"
                return next_round, next_pick, next_player, status
    
    return "1", "1", "player", "finished"


def update_draft(group_name, r, p, pick_url):
    existing = dropbox_load("draft")

    existing[group_name][r][p][0] = pick_url

    dropbox_upload(existing, "draft")

def draft_table(groupname, draft_track):
    r, p, player, status = check_draft(groupname, draft_track)
    riders_dict = load_all_riders()
    data = {}
    for i in range(int(r)):
        data[f"Round: {str(i+1)}"] = []
        for j in range(len(draft_track[groupname]["1"].keys())):
            try: 
                name = riders_dict[draft_track[groupname][str(i+1)][str(j+1)][0]][0]
            except KeyError:
                name = ''
            data[f"Round: {str(i+1)}"].append(f'{draft_track[groupname][str(i+1)][str(j+1)][1]}: {name}')
    
    index = [f"Pick {p}" for p in draft_track[groupname]["1"].keys()]

    return index, data

def draft_table_f(groupname, draft_track):
    riders_dict = load_all_riders()
    data = {}
    for i in range(30):
        data[f"Round: {str(i+1)}"] = []
        for j in range(len(draft_track[groupname]["1"].keys())):
            try: 
                name = riders_dict[draft_track[groupname][str(i+1)][str(j+1)][0]][0]
            except KeyError:
                name = ''
            data[f"Round: {str(i+1)}"].append(f'{draft_track[groupname][str(i+1)][str(j+1)][1]}: {name}')
    
    index = [f"Pick {p}" for p in draft_track[groupname]["1"].keys()]

    return index, data

def team_table(groupname, uname, teams):
    riders_dict = load_all_riders()
    rider_names = []
    scores = []
    results = load_results()
    
    for rlink in teams[groupname][uname]:
        rname = riders_dict[rlink][0]
        rider_names.append(rname)
        score = 0
        for race in results['results']:
            for rider in results['results'][race]:
                if rider[0] == rlink:
                    score = score + int(rider[2])
        scores.append(score) # Logic for scores goes here
    
    # Return a dictionary where keys are the columns
    data = {
        'Riders': rider_names,
        'Pnts': scores
    }
    
    return data

def close_group(group, groupname):
    members = group["members"]
    players = members
    random.shuffle(players)
    r_players = list(reversed(players))

    existing = dropbox_load("draft")

    local = {}

    for i in range(30):
        local[str(i+1)] = {}
        if i % 2 == 0:
            for j in range(len(players)):
                local[str(i+1)][str(j+1)] = ["", players[j]]
            
        else:
            for j in range(len(r_players)):
                local[str(i+1)][str(j+1)] = ["", r_players[j]]

    existing[groupname] = local
    dropbox_upload(existing, "draft")
    return True


def load_all_riders():
    return dropbox_load("comp_riders")

    
def load_dist():
    return dropbox_load("point_dist")
    
def load_races():
    return dropbox_load("new_races")

    
def load_monuments():
    return dropbox_load("monuments")

    
def load_gt():
    return dropbox_load("gt")

    
def load_results():
    return dropbox_load("results")


def load_rider_names():
    return dropbox_load("riders_names")


def save_results(text):
    dropbox_upload(text, "results")

def gen_quote():
    quotes = dropbox_load("quotes")
    quote = random.choice(quotes["1"])
    names = load_rider_names()
    names_list = list(names.keys())
    names_list = names_list[:660]
    rider = random.choice(names_list)
    return f'{quote}      -       {rider}'

def names_list(group, draft):
    riders_names = load_rider_names()
    comp = load_all_riders()
    riders_names.pop('POGA\u010cAR Tadej', '')
    for r in draft[group]:
        for p in draft[group][r]:
            try:
                name = comp[draft[group][r][p][0]][0]
            except KeyError:
                name = ''
            riders_names.pop(name, '')
    return riders_names

def check_date():
    return datetime.today().strftime('%Y-%m-%d')


def finish_draft(group_name):
    draft = dropbox_load("draft")

    teams = dropbox_load("teams")
    
    teams[group_name] = {}

    for r in draft[group_name]:
        for p in draft[group_name][r]:
            name = draft[group_name][r][p][1]
            if name not in teams[group_name]:
                teams[group_name][name] = []
            rider = draft[group_name][r][p][0]
            teams[group_name][name].append(rider)

    dropbox_upload(teams, "teams")


def result_table(race):
    results = result_scraper(race)
    info = info_scraper(race)
    desg = info['Classification']
    riders_dict = load_all_riders()
    rows = []
    for index, row in results.iterrows():
        rider_url = row["Rider"]
        try:
            rider_name = riders_dict[rider_url][0]
        except KeyError:
            rider_name = rider_url
        rank = row["Rnk"]
        try:
            if int(rank) < 26:
                score = check_points(int(rank), race, desg)
                rows.append([rider_name, rank, score])
        except ValueError:
            continue
    columns = ["Rider", "Result", "Points"]
    return rows, columns

dist = load_dist()
monuments = load_monuments()
gt = load_gt()

def check_points(rank, race, desg, type='stage'):

    kind, level = desg.split(".")

    if race in monuments:
        level = "Monument"
    if race in gt:
        level = "GT"

    if kind == "1":
        return dist['one-day'][level][rank-1]
    if kind =="2":
        if type == "gc":
            return dist['GC'][level][rank-1]
        elif type == "stage":
            return dist['stage'][level][rank-1]



def update_results():
    results = load_results()
    last_update = results["date"]
    current_date = check_date()
    st.write(current_date)
    races = load_races()
    for race in races: 
        # If race completly passed
        if last_update <= races[race]["enddate"] < current_date:
            desg = races[race]["class"]
            type, lvl = desg.split('.')
            if type == "1":
                local_results = result_scraper(race)
                rows = []
                for index, row in local_results.iterrows():
                    rider_url = row["Rider"]
                    rank = row["Rnk"]
                    try:
                        if int(rank) < 26:
                            score = check_points(int(rank), race, desg)
                            rows.append([rider_url, rank, score])
                    except ValueError:
                        continue
                results["results"][race] = rows

            if type == "2":
                # First GC results
                local_results = gc_scraper(race)
                rows = []
                for index, row in local_results.iterrows():
                    rider_url = row["Rider"]
                    rank = row["Rnk"]
                    try:
                        if int(rank) < 26:
                            score = check_points(int(rank), race, desg, type="gc")
                            rows.append([rider_url, rank, score])
                    except ValueError:
                        continue
                results["results"][race+'gc/'] = rows

                # Now stages
                for stage in races[race]["stages"]:
                    local_results = result_scraper(stage)
                    rows = []
                    for index, row in local_results.iterrows():
                        rider_url = row["Rider"]
                        rank = row["Rnk"]
                        try:
                            if int(rank) < 16:
                                score = check_points(int(rank), race, desg)
                                rows.append([rider_url, rank, score])
                        except ValueError:
                            continue
                    results["results"][stage] = rows

        # if race is on the same day:
        if (races[race]["startdate"] <= current_date and current_date <= races[race]["enddate"]) or races[race]["enddate"] == current_date:
            desg = races[race]["class"]
            type, lvl = desg.split('.')
            if type == "1":
                local_results = result_scraper(race)
                if not local_results is None:
                    rows = []
                    for index, row in local_results.iterrows():
                        rider_url = row["Rider"]
                        rank = row["Rnk"]
                        try:
                            if int(rank) < 26:
                                score = check_points(int(rank), race, desg)
                                rows.append([rider_url, rank, score])
                        except ValueError:
                            continue
                    results["results"][race] = rows

            if type == "2":
                # First GC results
                local_results = gc_scraper(race)
                if not local_results is None:
                    rows = []
                    for index, row in local_results.iterrows():
                        rider_url = row["Rider"]
                        rank = row["Rnk"]
                        try:
                            if int(rank) < 26:
                                score = check_points(int(rank), race, desg, type="gc")
                                rows.append([rider_url, rank, score])
                        except ValueError:
                            continue

                    results["results"][race+'gc/'] = rows

                # Now stages
                for stage in races[race]["stages"]:
                    local_results = result_scraper(stage)
                    if not local_results is None:
                        st.write(local_results)
                        rows = []
                        for index, row in local_results.iterrows():
                            rider_url = row["Rider"]
                            rank = row["Rnk"]
                            try:
                                if int(rank) < 16:
                                    score = check_points(int(rank), race, desg)
                                    rows.append([rider_url, rank, score])
                            except ValueError:
                                continue
                        if rows:
                            results["results"][stage] = rows
            st.write(results)
    results["date"] = current_date
    save_results(results)







