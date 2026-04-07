import streamlit as st
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog
import pandas as pd

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="The Goon Cave",
    page_icon="🏀",
    layout="wide"
)

# ----------------------------
# Custom styling
# ----------------------------
st.markdown("""
<style>
/* Main app width / zoomed out feel */
.block-container {
    max-width: 1200px;
    padding-top: 1rem;
    padding-bottom: 1.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Main background + text */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Card style */
.custom-card {
    background: rgba(30, 41, 59, 0.95);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}

/* Section title */
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #f8fafc;
}

/* Small muted text */
.muted-text {
    color: #94a3b8;
    font-size: 0.95rem;
}

/* Green / red badges */
.green-badge {
    display: inline-block;
    background: rgba(34, 197, 94, 0.18);
    color: #4ade80;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.9rem;
    border: 1px solid rgba(74, 222, 128, 0.35);
}

.red-badge {
    display: inline-block;
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.9rem;
    border: 1px solid rgba(248, 113, 113, 0.35);
}

/* Header title */
.main-title {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 0.2rem;
}

.main-subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown("<div class='main-title'>🏀 NBA Props Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='main-subtitle'>Analyze player props, splits, trends, and hit rates</div>", unsafe_allow_html=True)

# ----------------------------
# Helpers
# ----------------------------
def add_derived_columns(df):
    df = df.copy()

    numeric_cols = [
        "MIN", "PTS", "REB", "AST", "STL", "BLK",
        "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "TOV"
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
            "FG%": 0.0,
            "3P%": 0.0,
            "FT%": 0.0,
            "TOV": 0.0,
        }

    fgm = df["FGM"].sum()
    fga = df["FGA"].sum()
    fg3m = df["FG3M"].sum()
    fg3a = df["FG3A"].sum() if "FG3A" in df.columns else 0
    ftm = df["FTM"].sum()
    fta = df["FTA"].sum()

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
        "FG%": (fgm / fga * 100) if fga > 0 else 0,
        "3P%": (fg3m / fg3a * 100) if fg3a > 0 else 0,
        "FT%": (ftm / fta * 100) if fta > 0 else 0,
        "TOV": df["TOV"].mean(),
    }


def show_stat_row(title, stats_dict):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("GP", stats_dict["GP"])
    c1.metric("MIN", f"{stats_dict['MIN']:.1f}")

    c2.metric("PTS", f"{stats_dict['PTS']:.1f}")
    c2.metric("REB", f"{stats_dict['REB']:.1f}")

    c3.metric("AST", f"{stats_dict['AST']:.1f}")
    c3.metric("TOV", f"{stats_dict['TOV']:.1f}")

    c4.metric("STL", f"{stats_dict['STL']:.1f}")
    c4.metric("BLK", f"{stats_dict['BLK']:.1f}")

    c5.metric("3PM", f"{stats_dict['3PM']:.1f}")
    c5.metric("FGM/FGA", f"{stats_dict['FGM']:.1f}/{stats_dict['FGA']:.1f}")

    st.markdown("<div class='muted-text' style='margin-top: 8px;'>Shooting Percentages</div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.metric("FG%", f"{stats_dict['FG%']:.1f}%")
    s2.metric("3P%", f"{stats_dict['3P%']:.1f}%")
    s3.metric("FT%", f"{stats_dict['FT%']:.1f}%")


def color_hit_cell(val):
    if val is True:
        return "background-color: rgba(34, 197, 94, 0.20); color: #4ade80; font-weight: 700;"
    if val is False:
        return "background-color: rgba(239, 68, 68, 0.20); color: #f87171; font-weight: 700;"
    return ""


def color_statvalue(row):
    if row["Hit"] is True:
        return ["background-color: rgba(34, 197, 94, 0.12)" if col == "StatValue" else "" for col in row.index]
    if row["Hit"] is False:
        return ["background-color: rgba(239, 68, 68, 0.12)" if col == "StatValue" else "" for col in row.index]
    return [""] * len(row)


# ----------------------------
# Sidebar Filters
# ----------------------------
with st.sidebar:
    st.markdown("## 🎛 Filters")
    st.markdown("---")

    active_players = sorted([p["full_name"] for p in players.get_active_players()])
    player_name = st.selectbox("Player", options=active_players)

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
    line = st.number_input("Line", value=19.5, step=0.5)

    split = st.selectbox("Split", ["Overall", "Home", "Away"])

    nba_teams = teams.get_teams()
    team_abbrevs = sorted([t["abbreviation"] for t in nba_teams])
    opponent = st.selectbox("Opponent", ["All"] + team_abbrevs)

    game_range = st.selectbox(
        "Game Sample",
        ["All Games", "Last 5", "Last 10", "Last 15", "Last 20"]
    )

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

            log["GAME_DATE"] = pd.to_datetime(log["GAME_DATE"])
            log = log.sort_values("GAME_DATE", ascending=False).copy()

            log["Location"] = log["MATCHUP"].apply(
                lambda x: "Away" if "@" in x else "Home"
            )

            log["OPP"] = log["MATCHUP"].str.split().str[-1]
            log = add_derived_columns(log)

            season_log = log.copy()
            filtered_log = log.copy()

            if split != "Overall":
                filtered_log = filtered_log[filtered_log["Location"] == split].copy()

            if opponent != "All":
                filtered_log = filtered_log[filtered_log["OPP"] == opponent].copy()

            if game_range != "All Games":
                n_games = int(game_range.split()[1])
                filtered_log = filtered_log.head(n_games).copy()

            filtered_log = calc_hit_column(filtered_log, stat_type, line, pick)

            label_parts = [split]
            if opponent != "All":
                label_parts.append(f"vs {opponent}")
            label_parts.append(game_range)
            label = " • ".join(label_parts)

            season_stats = build_per_game_stats(season_log)
            filtered_stats = build_per_game_stats(filtered_log)

            # Top card container
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)

            left, right = st.columns([1, 2])

            with left:
                headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"
                st.image(headshot_url, caption=player_name, use_container_width=True)

            with right:
                st.subheader(player_name)
                st.markdown(f"<div class='muted-text'><b>Filter:</b> {label}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='muted-text' style='margin-bottom: 12px;'><b>Prop:</b> {pick} {line} {stat_type}</div>", unsafe_allow_html=True)

                if len(filtered_log) == 0:
                    st.warning("No games found for these filters.")
                else:
                    hit_rate = filtered_log["Hit"].mean() * 100
                    avg_selected_stat = filtered_log["StatValue"].mean()

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Hit Rate", f"{hit_rate:.1f}%")
                    m2.metric("Games Found", len(filtered_log))
                    m3.metric(f"Avg {stat_type}", f"{avg_selected_stat:.1f}")

                    st.markdown("")
                    badge_class = "green-badge" if hit_rate >= 50 else "red-badge"
                    badge_text = "Trending Over / Strong Hit Rate" if hit_rate >= 50 else "Trending Under / Low Hit Rate"
                    st.markdown(f"<span class='{badge_class}'>{badge_text}</span>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Season stats card
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            show_stat_row("Season Per-Game Stats", season_stats)
            st.markdown("</div>", unsafe_allow_html=True)

            # Filtered stats card
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            show_stat_row(f"Filtered Per-Game Stats ({label})", filtered_stats)
            st.markdown("</div>", unsafe_allow_html=True)

            # Filtered game log
            if len(filtered_log) > 0:
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Filtered Game Log</div>", unsafe_allow_html=True)

                display_log = filtered_log[
                    [
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
                        "FGM",
                        "FGA",
                        "FG3M",
                        "FG3A",
                        "FTM",
                        "FTA",
                        "TOV",
                        "StatValue",
                        "Hit",
                    ]
                ].copy()

                display_log["GAME_DATE"] = display_log["GAME_DATE"].dt.strftime("%Y-%m-%d")

                styled_df = (
                    display_log.style
                    .apply(color_statvalue, axis=1)
                    .map(color_hit_cell, subset=["Hit"])
                )

                st.dataframe(styled_df, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"NBA servers are busy or an error occurred: {e}")
