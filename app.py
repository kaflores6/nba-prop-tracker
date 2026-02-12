import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 NBA Props")

# Active player list
active_players = sorted([p["full_name"] for p in players.get_active_players()])

# ONE searchable dropdown (type to filter)
player_name = st.selectbox(
    "Search for an NBA Player",
    options=active_players,
)

# Categories (your list + PRA)
stat_type = st.selectbox(
    "Category",
    [
        "PTS",
        "REB",
        "AST",
        "PTS+REB",
        "PTS+AST",
        "REB+AST",
        "PRA",
        "STL",
        "BLK",
    ],
)

line = st.number_input("Line", value=19.5)

if player_name:
    try:
        # Find player id
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            st.warning("Player not found.")
        else:
            p_id = nba_players[0]["id"]

            # Fetch game log
            log = playergamelog.PlayerGameLog(player_id=p_id, timeout=30).get_data_frames()[0]

            # Map category -> columns to sum
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

            # Ensure numeric (sometimes API returns as object)
            for c in cols:
                log[c] = pd.to_numeric(log[c], errors="coerce")

            # Compute value + hit
            log["StatValue"] = log[cols].sum(axis=1)
            log["Hit"] = log["StatValue"] > line

            st.success(f"Loaded {len(log)} games for {player_name}")

            hit_rate = log["Hit"].mean() * 100
            st.metric("Season Hit Rate", f"{hit_rate:.1f}%")

            # Show recent games (game log is typically newest first)
            st.dataframe(
                log[["GAME_DATE", "MATCHUP", "StatValue", "Hit"]].head(15)
            )

    except Exception:
        st.error("NBA Servers are busy. Please wait 10 seconds and try again.")
        
