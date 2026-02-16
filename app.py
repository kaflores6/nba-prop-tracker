import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 NBA Props")

active_players = sorted([p["full_name"] for p in players.get_active_players()])

player_name = st.selectbox("Search for an NBA Player", options=active_players)

stat_type = st.selectbox(
    "Category",
    ["PTS","REB","AST","PTS+REB","PTS+AST","REB+AST","PRA","STL","BLK"]
)

pick = st.selectbox("Pick", ["Over", "Under"])

# NEW: overall/home/away split
split = st.selectbox("Split", ["Overall", "Home", "Away"])

line = st.number_input("Line", value=19.5)

if player_name:
    try:
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            st.warning("Player not found.")
        else:
            p_id = nba_players[0]["id"]
            log = playergamelog.PlayerGameLog(player_id=p_id, timeout=30).get_data_frames()[0]

            # Determine home/away from MATCHUP
            log["Location"] = log["MATCHUP"].apply(lambda x: "Away" if "@" in x else "Home")

            # Apply split filter
            if split != "Overall":
                log = log[log["Location"] == split].copy()

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
                st.warning(f"No games found for split: {split}")
            else:
                st.success(f"{player_name} — {split} games: {len(log)}")
                hit_rate = log["Hit"].mean() * 100
                st.metric(f"{pick} Hit Rate ({split})", f"{hit_rate:.1f}%")

                st.dataframe(
                    log[["GAME_DATE", "MATCHUP", "Location", "StatValue", "Hit"]].head(15)
                )

    except Exception:
        st.error("NBA Servers are busy. Please wait 10 seconds and try again.")
