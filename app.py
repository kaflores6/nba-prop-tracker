import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏀 NBA Prop Dashboard")

player_name = st.text_input("Enter Player Name", "LeBron James")
stat_type = st.selectbox("Category", ["PTS", "REB", "AST"])
line = st.number_input("Line", value=19.5)

if player_name:
    try:
        # 1. Find the Player
        nba_players = players.find_players_by_full_name(player_name)
        if nba_players:
            p_id = nba_players[0]['id']
            
            # 2. Fetch Data (This is where the 'Certificates' fix matters!)
            log = playergamelog.PlayerGameLog(player_id=p_id, timeout=30).get_data_frames()[0]
            
            # 3. Process Hits
            log['Hit'] = log[stat_type] > line
            
            # 4. Success! Show the data
            st.success(f"Loaded {len(log)} games for {player_name}")
            
            # Metrics to fix your spreadsheet math errors
            hit_rate = (log['Hit'].sum() / len(log)) * 100
            st.metric("Season Hit Rate", f"{hit_rate:.1f}%")
            
            st.dataframe(log[['GAME_DATE', 'MATCHUP', stat_type, 'Hit']].head(15))
        else:
            st.warning("Player not found.")
    except Exception as e:
        st.error("NBA Servers are busy. Please wait 10 seconds and try again.")