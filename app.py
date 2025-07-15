# Streamlit App for Stat-Based Football Match Predictions
import streamlit as st
import pandas as pd

# Function to calculate team stats

def calculate_team_stats(df, team, venue='all', last_n=5):
    if venue == 'home':
        mask = df['Home Team'] == team
        gf = df.loc[mask, 'Home Goals'].tail(last_n)
        ga = df.loc[mask, 'Away Goals'].tail(last_n)
        cf = df.loc[mask, 'Home Corners'].tail(last_n)
        ca = df.loc[mask, 'Away Corners'].tail(last_n)
        opponents = df.loc[mask, 'Away Goals'].reset_index(drop=True)
        team_goals = gf.reset_index(drop=True)
    elif venue == 'away':
        mask = df['Away Team'] == team
        gf = df.loc[mask, 'Away Goals'].tail(last_n)
        ga = df.loc[mask, 'Home Goals'].tail(last_n)
        cf = df.loc[mask, 'Away Corners'].tail(last_n)
        ca = df.loc[mask, 'Home Corners'].tail(last_n)
        opponents = df.loc[mask, 'Home Goals'].reset_index(drop=True)
        team_goals = gf.reset_index(drop=True)
    else:
        mask_home = df['Home Team'] == team
        mask_away = df['Away Team'] == team
        gf = pd.concat([df.loc[mask_home, 'Home Goals'], df.loc[mask_away, 'Away Goals']]).tail(last_n)
        ga = pd.concat([df.loc[mask_home, 'Away Goals'], df.loc[mask_away, 'Home Goals']]).tail(last_n)
        cf = pd.concat([df.loc[mask_home, 'Home Corners'], df.loc[mask_away, 'Away Corners']]).tail(last_n)
        ca = pd.concat([df.loc[mask_home, 'Away Corners'], df.loc[mask_away, 'Home Corners']]).tail(last_n)
        team_goals = gf.reset_index(drop=True)
        opponents = ga.reset_index(drop=True)

    # Estimate strength: 3 for win, 1 for draw, 0 for loss based on goals
    points = [(3 if tg > og else 1 if tg == og else 0) for tg, og in zip(team_goals, opponents)]
    strength_score = sum(points) / len(points) if points else 0

    return {
        'Goals For': gf.mean(),
        'Goals Against': ga.mean(),
        'Corners For': cf.mean(),
        'Corners Against': ca.mean(),
        'Strength Score': strength_score
    }

# Prediction function with thresholds and commentary

def confidence_judgement(val, threshold=0.8, weak_threshold=0.6):
    if val >= threshold:
        return 'Yes'
    elif val <= weak_threshold:
        return 'No'
    else:
        return None

def predict_match(df, home_team, away_team):
    home = calculate_team_stats(df, home_team, venue='home')
    away = calculate_team_stats(df, away_team, venue='away')

    predictions = {
        'Home Team': home_team,
        'Away Team': away_team
    }
    confidences = {}

    # BTTS logic
    btts_score = min(home['Goals For'], away['Goals For'])
    btts = confidence_judgement(btts_score)
    if btts:
        predictions['BTTS'] = btts
        confidences['BTTS'] = abs(btts_score - 0.7)

    # Over 2.5 logic
    total_goals = (home['Goals For'] + home['Goals Against'] + away['Goals For'] + away['Goals Against']) / 2
    over_2_5 = confidence_judgement(total_goals, threshold=2.8, weak_threshold=2.2)
    if over_2_5:
        predictions['Over 2.5'] = over_2_5
        confidences['Over 2.5'] = abs(total_goals - 2.5)

    # Over 9.5 corners logic
    total_corners = (home['Corners For'] + home['Corners Against'] + away['Corners For'] + away['Corners Against']) / 2
    over_9_corners = confidence_judgement(total_corners, threshold=9.5, weak_threshold=8.0)
    if over_9_corners:
        predictions['Over 9.5 Corners'] = over_9_corners
        confidences['Over 9.5 Corners'] = abs(total_corners - 9.5)

    # More corners
    if home['Corners For'] > away['Corners For']:
        predictions['More Corners'] = home_team
    elif away['Corners For'] > home['Corners For']:
        predictions['More Corners'] = away_team

    # Insights
    top_confidences = sorted(confidences.items(), key=lambda x: x[1], reverse=True)[:2]
    commentary = []
    for stat, score in top_confidences:
        if stat == 'BTTS':
            line = "Expect both teams to get on the scoresheet." if predictions[stat] == 'Yes' else "One side might keep a clean sheet."
        elif stat == 'Over 2.5':
            line = "Chances of 3+ goals look solid." if predictions[stat] == 'Yes' else "Could be a tight, low-scoring game."
        elif stat == 'Over 9.5 Corners':
            line = "Expect a flurry of corners in this one." if predictions[stat] == 'Yes' else "Corner count may stay under the radar."
        else:
            line = "Key stat edge detected."
        commentary.append(f"• {line}")

    predictions['Insights'] = " ".join(commentary)
    return predictions

# Streamlit UI
st.title("⚽ Stat-Based Football Match Predictor")

uploaded_file = st.file_uploader("Upload your match stats Excel file (past results)", type=["xlsx"])
fixture_file = st.file_uploader("Upload your fixture list (HomeTeam, AwayTeam)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Results data uploaded successfully!")

    if fixture_file:
        fixtures = pd.read_excel(fixture_file)
        st.success("Fixture list uploaded successfully!")

        if st.button("Run Batch Predictions"):
            batch_results = []
            for _, row in fixtures.iterrows():
                home_team = row['HomeTeam']
                away_team = row['AwayTeam']
                prediction = predict_match(df, home_team, away_team)
                batch_results.append(prediction)

            st.subheader("📋 Predictions Summary")
            st.dataframe(pd.DataFrame(batch_results))

    else:
        home_team = st.selectbox("Select Home Team", sorted(pd.unique(df['Home Team'].tolist() + df['Away Team'].tolist())))
        away_team = st.selectbox("Select Away Team", sorted(pd.unique(df['Home Team'].tolist() + df['Away Team'].tolist())))

        if st.button("Predict Match"):
            if home_team != away_team:
                result = predict_match(df, home_team, away_team)
                st.subheader(f"Prediction: {home_team} vs {away_team}")
                for key, val in result.items():
                    if key not in ["Home Team", "Away Team"]:
                        st.markdown(f"**{key}:** {val}")
            else:
                st.warning("Please choose two different teams.")
