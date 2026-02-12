import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 NBA Props")

# Get active players once
active_players = [p['full_name'] for p in players.get_active_players()]

# ONE searchable dropdown (type-to-filter)
player_name = st.selectbox(
    "Search for an NBA Player",
    options=sorted(active_players),
)

stat_type = st.selectbox("Category", ["PTS", "REB", "AST"])
line = st.number_input("Line", value=19.5)

if player_name:
    try:
        nba_players = players.find_players_by_full_name(player_name)
        if nba_players:
            p_id = nba_players[0]['id']
            
            log = playergamelog.PlayerGameLog(
                player_id=p_id,
                timeout=30
            ).get_data_frames()[0]
            
            log['Hit'] = log[stat_type] > line
            
            st.success(f"Loaded {len(log)} games for {player_name}")
            
            hit_rate = (log['Hit'].mean()) * 100
            st.metric("Season Hit Rate", f"{hit_rate:.1f}%")
            
            st.dataframe(
                log[['GAME_DATE', 'MATCHUP', stat_type, 'Hit']].head(15)
            )
        else:
            st.warning("Player not found.")
    except Exception:
        st.error("NBA Servers are busy. Please wait 10 seconds and try again.")
