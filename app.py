import streamlit as st
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog
import pandas as pd

st.set_page_config(layout="wide")
st.title("The Batcave")

# ----------------------------
# Helpers
# ----------------------------
def add_derived_columns(df):
    df = df.copy()

    numeric_cols = [
        "MIN", "PTS", "REB", "AST", "STL", "BLK",
        "FG3M", "FGM", "FGA", "FTM", "FTA", "TOV"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["PRA"] = df["PTS"] + df["REB"] + df["AST"]
    df["PTS+REB"] = df["PTS"] + df["REB"]
    df["PTS+AST"] = df["PTS"] + df["AST"]
    df["REB+AST"] = df["REB"] + df["AST"]

    return df


def get_stat_columns():
    return {
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


def calc_hit_column(df, stat_type, line, pick):
    df = df.copy()
    stat_map = get_stat_columns()
    cols = stat_map[stat_type]
    df["StatValue"] = df[cols].sum(axis=1)

    if pick == "Over":
        df["Hit"] = df["StatValue"] > line
    else:
        df["Hit"] = df["StatValue"] < line

    return df


def build_per_game_stats(df):
    if len(df) == 0:
        return {
            "GP": 0,
            "MIN": 0.0,
            "PTS": 0.0,
            "REB": 0.0,
            "AST": 0.0,
            "STL": 0.0,
            "BLK": 0.0,
            "3PM": 0.0,
            "FGM": 0.0,
            "FGA": 0.0,
            "FTM": 0.0,
            "FTA": 0.0,
            "TOV": 0.0,
            "PRA": 0.0,
        }

    return {
        "GP": len(df),
        "MIN": df["MIN"].mean(),
        "PTS": df["PTS"].mean(),
        "REB": df["REB"].mean(),
        "AST": df["AST"].mean(),
        "STL": df["STL"].mean(),
        "BLK": df["BLK"].mean(),
        "3PM": df["FG3M"].mean(),
        "FGM": df["FGM"].mean(),
        "FGA": df["FGA"].mean(),
        "FTM": df["FTM"].mean(),
        "FTA": df["FTA"].mean(),
        "TOV": df["TOV"].mean(),
        "PRA": df["PRA"].mean(),
    }


def show_stat_block(title, stats_dict):
    st.markdown(f"### {title}")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("GP", stats_dict["GP"])
    c1.metric("PTS", f"{stats_dict['PTS']:.1f}")
    c1.metric("REB", f"{stats_dict['REB']:.1f}")
    c1.metric("AST", f"{stats_dict['AST']:.1f}")

    c2.metric("MIN", f"{stats_dict['MIN']:.1f}")
    c2.metric("STL", f"{stats_dict['STL']:.1f}")
    c2.metric("BLK", f"{stats_dict['BLK']:.1f}")
    c2.metric("3PM", f"{stats_dict['3PM']:.1f}")

    c3.metric("FGM", f"{stats_dict['FGM']:.1f}")
    c3.metric("FGA", f"{stats_dict['FGA']:.1f}")
    c3.metric("FTM", f"{stats_dict['FTM']:.1f}")
    c3.metric("FTA", f"{stats_dict['FTA']:.1f}")

    c4.metric("TOV", f"{stats_dict['TOV']:.1f}")
    c4.metric("PRA", f"{stats_dict['PRA']:.1f}")


# ----------------------------
# Inputs
# ----------------------------
active_players = sorted([p["full_name"] for p in players.get_active_players()])
player_name = st.selectbox("Search for an NBA Player", options=active_players)

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
        "3PM",
    ],
)

pick = st.selectbox("Pick", ["Over", "Under"])
split = st.selectbox("Split", ["Overall", "Home", "Away"])

nba_teams = teams.get_teams()
team_abbrevs = sorted([t["abbreviation"] for t in nba_teams])
opponent = st.selectbox("Opponent (team)", ["All"] + team_abbrevs)

game_range = st.selectbox(
    "Game Sample",
    ["All Games", "Last 5", "Last 10", "Last 15", "Last 20"]
)

line = st.number_input("Line", value=19.5)

# ----------------------------
# Main
# ----------------------------
if player_name:
    try:
        nba_players = players.find_players_by_full_name(player_name)

        if not nba_players:
            st.warning("Player not found.")
        else:
            p_id = nba_players[0]["id"]

            log = playergamelog.PlayerGameLog(
                player_id=p_id,
                timeout=30
            ).get_data_frames()[0]

            # PlayerGameLog includes standard game log box-score fields such as
            # MIN, FGM, FGA, FG3M, FTM, FTA, REB, AST, STL, BLK, TOV, and PTS. :contentReference[oaicite:1]{index=1}

            log["GAME_DATE"] = pd.to_datetime(log["GAME_DATE"])
            log = log.sort_values("GAME_DATE", ascending=False).copy()

            # Home / Away
            log["Location"] = log["MATCHUP"].apply(
                lambda x: "Away" if "@" in x else "Home"
            )

            # Opponent abbreviation from MATCHUP
            log["OPP"] = log["MATCHUP"].str.split().str[-1]

            log = add_derived_columns(log)

            # Save full season stats BEFORE filters
            season_log = log.copy()

            # Apply filters
            filtered_log = log.copy()

            if split != "Overall":
                filtered_log = filtered_log[filtered_log["Location"] == split].copy()

            if opponent != "All":
                filtered_log = filtered_log[filtered_log["OPP"] == opponent].copy()

            if game_range != "All Games":
                n_games = int(game_range.split()[1])
                filtered_log = filtered_log.head(n_games).copy()

            filtered_log = calc_hit_column(filtered_log, stat_type, line, pick)

            # ----------------------------
            # Player header
            # ----------------------------
            top_left, top_right = st.columns([1, 3])

            with top_left:
                # This headshot URL is an inferred NBA CDN pattern based on player id.
                # If a specific player image fails, Streamlit will just show the fallback text.
                headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"
                st.image(headshot_url, caption=player_name, use_container_width=True)

            with top_right:
                st.subheader(player_name)

                label_parts = [split]
                if opponent != "All":
                    label_parts.append(f"vs {opponent}")
                label_parts.append(game_range)
                label = " • ".join(label_parts)

                st.write(f"**Current filter:** {label}")
                st.write(f"**Prop:** {pick} {line} {stat_type}")

                if len(filtered_log) == 0:
                    st.warning(
                        f"No games found for filters: Split={split}, Opponent={opponent}, Sample={game_range}"
                    )
                else:
                    hit_rate = filtered_log["Hit"].mean() * 100
                    st.metric(f"{pick} Hit Rate", f"{hit_rate:.1f}%")

            # ----------------------------
            # Stats blocks
            # ----------------------------
            season_stats = build_per_game_stats(season_log)
            filtered_stats = build_per_game_stats(filtered_log)

            st.divider()
            show_stat_block("Season Per-Game Stats", season_stats)

            st.divider()
            show_stat_block(f"Filtered Per-Game Stats ({label})", filtered_stats)

            # ----------------------------
            # Game log table
            # ----------------------------
            if len(filtered_log) > 0:
                st.divider()
                st.markdown("### Filtered Game Log")

                display_cols = [
                    "GAME_DATE",
                    "MATCHUP",
                    "Location",
                    "OPP",
                    "MIN",
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG3M",
                    "PRA",
                    "StatValue",
                    "Hit",
                ]

                st.dataframe(
                    filtered_log[display_cols].head(25),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"NBA servers are busy or an error occurred: {e}")
        
