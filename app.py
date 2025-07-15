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

    points = [(3 if tg > og else 1 if tg == og else 0) for tg, og in zip(team_goals, opponents)]
    strength_score = sum(points) / len(points) if points else 0

    return {
        'GF': list(gf),
        'GA': list(ga),
        'CF': list(cf),
        'CA': list(ca),
        'Strength Score': strength_score
    }

# Contextual prediction using adjusted recent performance

def predict_match(df, home_team, away_team):
    home = calculate_team_stats(df, home_team, venue='home')
    away = calculate_team_stats(df, away_team, venue='away')

    predictions = {
        'Home Team': home_team,
        'Away Team': away_team
    }

    insights = []

    # BTTS logic
    btts_yes = 0
    for hgf, agf in zip(home['GF'], away['GA']):
        if hgf > 0 and agf > 0:
            btts_yes += 1
    for agf, hga in zip(away['GF'], home['GA']):
        if agf > 0 and hga > 0:
            btts_yes += 1
    btts_ratio = btts_yes / max(len(home['GF']), 1)
    if btts_ratio >= 0.7:
        predictions['BTTS'] = 'Yes'
        insights.append("• Both teams tend to score and concede regularly.")
    elif btts_ratio <= 0.3:
        predictions['BTTS'] = 'No'
        insights.append("• One team often shuts out the other.")

    # Over 2.5 logic
    goal_totals = [h + a for h, a in zip(home['GF'], home['GA'])] + [h + a for h, a in zip(away['GF'], away['GA'])]
    over_count = sum([1 for total in goal_totals if total > 2.5])
    over_ratio = over_count / max(len(goal_totals), 1)
    if over_ratio >= 0.7:
        predictions['Over 2.5'] = 'Yes'
        insights.append("• Matches often exceed 2.5 goals.")
    elif over_ratio <= 0.3:
        predictions['Over 2.5'] = 'No'
        insights.append("• Matches tend to be low-scoring.")

    # Over 9.5 corners logic
    corner_totals = [h + a for h, a in zip(home['CF'], home['CA'])] + [h + a for h, a in zip(away['CF'], away['CA'])]
    over_corner_count = sum([1 for total in corner_totals if total > 9])
    corner_ratio = over_corner_count / max(len(corner_totals), 1)
    if corner_ratio >= 0.7:
        predictions['Over 9.5 Corners'] = 'Yes'
        insights.append("• Games are typically corner-heavy.")
    elif corner_ratio <= 0.3:
        predictions['Over 9.5 Corners'] = 'No'
        insights.append("• Corners may be limited.")

    # More corners
    avg_home_cf = sum(home['CF']) / len(home['CF']) if home['CF'] else 0
    avg_away_cf = sum(away['CF']) / len(away['CF']) if away['CF'] else 0
    if abs(avg_home_cf - avg_away_cf) >= 1:
        predictions['More Corners'] = home_team if avg_home_cf > avg_away_cf else away_team

    predictions['Insights'] = " ".join(insights) if insights else "Too close to call."
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
