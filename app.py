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
        cardf = df.loc[mask, 'Home Cards'].tail(last_n)
        carda = df.loc[mask, 'Away Cards'].tail(last_n)
    elif venue == 'away':
        mask = df['Away Team'] == team
        gf = df.loc[mask, 'Away Goals'].tail(last_n)
        ga = df.loc[mask, 'Home Goals'].tail(last_n)
        cf = df.loc[mask, 'Away Corners'].tail(last_n)
        ca = df.loc[mask, 'Home Corners'].tail(last_n)
        cardf = df.loc[mask, 'Away Cards'].tail(last_n)
        carda = df.loc[mask, 'Home Cards'].tail(last_n)
    else:
        gf = pd.concat([df[df['Home Team'] == team]['Home Goals'], df[df['Away Team'] == team]['Away Goals']]).tail(last_n)
        ga = pd.concat([df[df['Home Team'] == team]['Away Goals'], df[df['Away Team'] == team]['Home Goals']]).tail(last_n)
        cf = pd.concat([df[df['Home Team'] == team]['Home Corners'], df[df['Away Team'] == team]['Away Corners']]).tail(last_n)
        ca = pd.concat([df[df['Home Team'] == team]['Away Corners'], df[df['Away Team'] == team]['Home Corners']]).tail(last_n)
        cardf = pd.concat([df[df['Home Team'] == team]['Home Cards'], df[df['Away Team'] == team]['Away Cards']]).tail(last_n)
        carda = pd.concat([df[df['Home Team'] == team]['Away Cards'], df[df['Away Team'] == team]['Home Cards']]).tail(last_n)

    return {
        'Goals For': gf.mean(),
        'Goals Against': ga.mean(),
        'Corners For': cf.mean(),
        'Corners Against': ca.mean(),
        'Cards For': cardf.mean(),
        'Cards Against': carda.mean()
    }

# Prediction function
def predict_match(df, home_team, away_team):
    home = calculate_team_stats(df, home_team, venue='home')
    away = calculate_team_stats(df, away_team, venue='away')

    prediction = {
        'BTTS': 'Yes' if home['Goals For'] > 0.8 and away['Goals For'] > 0.8 else 'No',
        'Over 2.5 Goals': 'Yes' if (home['Goals For'] + home['Goals Against'] + away['Goals For'] + away['Goals Against']) / 2 > 2.5 else 'No',
        'More Corners': home_team if home['Corners For'] > away['Corners For'] else away_team,
        'Total Corners': round((home['Corners For'] + home['Corners Against'] + away['Corners For'] + away['Corners Against']) / 2, 1),
        'More Cards': home_team if home['Cards For'] > away['Cards For'] else away_team,
        'Total Cards': round((home['Cards For'] + home['Cards Against'] + away['Cards For'] + away['Cards Against']) / 2, 1)
    }
    return prediction

# Streamlit UI
st.title("⚽ Stat-Based Football Match Predictor")

uploaded_file = st.file_uploader("Upload your match stats Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Data uploaded successfully!")

    home_team = st.selectbox("Select Home Team", sorted(pd.unique(df['Home Team'].tolist() + df['Away Team'].tolist())))
    away_team = st.selectbox("Select Away Team", sorted(pd.unique(df['Home Team'].tolist() + df['Away Team'].tolist())))

    if st.button("Predict Match"):
        if home_team != away_team:
            result = predict_match(df, home_team, away_team)
            st.subheader(f"Prediction: {home_team} vs {away_team}")
            for key, val in result.items():
                st.markdown(f"**{key}:** {val}")
        else:
            st.warning("Please choose two different teams.")
