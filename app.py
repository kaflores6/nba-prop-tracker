import streamlit as st
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 NBA Props")

# --- Player selection ---
active_players = sorted([p["full_name"] for p in players.get_active_players()])
player_name = st.selectbox("Search for an NBA Player", options=active_players)

# --- Stat selection ---
stat_type = st.selectbox(
    "Category",
    ["PTS", "REB", "AST", "PTS+REB", "PTS+AST", "REB+AST", "PRA", "STL", "BLK", "3PM"],
)

pick = st.selectbox("Pick", ["Over", "Under"])

# --- Split + Opponent filters ---
split = st.selectbox("Split", ["Overall", "Home", "Away"])

# Build opponent list (team abbreviations)
nba_teams = teams.get_teams()
team_abbrevs = sorted([t["abbreviation"] for t in nba_teams])
opponent = st.selectbox("Opponent (team)", ["All"] + team_abbrevs)

line = st.number_input("Line", value=19.5)

if player_name:
    try:
        nba_players = players.find_players_by_full_name(player_name)

        if not nba_players:
            st.warning("Player not found.")
        else:
            p_id = nba_players[0]["id"]

            log = playergamelog.PlayerGameLog(player_id=p_id, timeout=30).get_data_frames()[0]

            # Home/Away from MATCHUP
            log["Location"] = log["MATCHUP"].apply(lambda x: "Away" if "@" in x else "Home")

            # Opponent abbreviation from MATCHUP (last token)
            # Examples: "MIN @ LAL" -> "LAL", "MIN vs. LAL" -> "LAL"
            log["OPP"] = log["MATCHUP"].str.split().str[-1]

            # Apply split filter
            if split != "Overall":
                log = log[log["Location"] == split].copy()

            # Apply opponent filter
            if opponent != "All":
                log = log[log["OPP"] == opponent].copy()

            stat_map = {
                "PTS": ["PTS"],
                "REB": ["REB"],
                "AST": ["AST"],
                "PTS+REB": ["PTS", "REB"],
                "PTS+AST": ["PTS", "AST"],
                "REB+AST": ["REB", "AST"],
                "PRA": ["PTS", "REB", "AST"],
                "STL": ["STL"],
                "BLK": ["BLK"],
                "3PM": ["FG3M"],
            }

            cols = stat_map[stat_type]
            for c in cols:
                log[c] = pd.to_numeric(log[c], errors="coerce")

            log["StatValue"] = log[cols].sum(axis=1)

            if pick == "Over":
                log["Hit"] = log["StatValue"] > line
            else:
                log["Hit"] = log["StatValue"] < line

            if len(log) == 0:
                st.warning(f"No games found for filters: Split={split}, Opponent={opponent}")
            else:
                hit_rate = log["Hit"].mean() * 100

                label_parts = [split]
                if opponent != "All":
                    label_parts.append(f"vs {opponent}")
                label = " • ".join(label_parts)

                st.success(f"{player_name} — games: {len(log)} ({label})")
                st.metric(f"{pick} Hit Rate ({label})", f"{hit_rate:.1f}%")

                st.dataframe(
                    log[["GAME_DATE", "MATCHUP", "Location", "OPP", "StatValue", "Hit"]].head(25)
                )

    except Exception:
        st.error("NBA Servers are busy. Please wait 10 seconds and try again.")
