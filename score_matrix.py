import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date
import math
import csv
from pathlib import Path

# Team color dictionary
color_dict = {
    'ANA': '#F47A38',  # Anaheim Ducks
    'BOS': '#FCB514',  # Boston Bruins
    'BUF': '#041E42',  # Buffalo Sabres
    'CAR': '#CC0000',  # Carolina Hurricanes
    'CGY': '#C8102E',  # Calgary Flames
    'CHI': '#CF0A2C',  # Chicago Blackhawks
    'CBJ': '#002654',  # Columbus Blue Jackets
    'COL': '#6F263D',  # Colorado Avalanche
    'DAL': '#006847',  # Dallas Stars
    'DET': '#CE1126',  # Detroit Red Wings
    'EDM': '#FF4C00',  # Edmonton Oilers
    'FLA': '#041E42',  # Florida Panthers
    'LAK': '#111111',  # Los Angeles Kings
    'MIN': '#154734',  # Minnesota Wild
    'MON': '#AF1E2D',  # Montreal Canadiens
    'NJD': '#CE1126',  # New Jersey Devils
    'NSH': '#FFB81C',  # Nashville Predators
    'NYI': '#00539B',  # New York Islanders
    'NYR': '#0033A0',  # New York Rangers
    'OTT': '#E31837',  # Ottawa Senators
    'PHI': '#F74902',  # Philadelphia Flyers
    'PIT': '#FCB514',  # Pittsburgh Penguins
    'SEA': '#001628',  # Seattle Kraken
    'SJS': '#006D75',  # San Jose Sharks
    'STL': '#002F87',  # St. Louis Blues
    'TBL': '#002868',  # Tampa Bay Lightning
    'TOR': '#003E7E',  # Toronto Maple Leafs
    'UTA': '#71AFE5',  # Utah Hockey Club
    'VAN': '#00843D',  # Vancouver Canucks
    'VGK': '#B4975A',  # Vegas Golden Knights
    'WSH': '#041E42',  # Washington Capitals
    'WPG': '#041E42'   # Winnipeg Jets
}

# Team name dictionary
team_names = {
    'ANA': 'Anaheim',
    'BOS': 'Boston',
    'BUF': 'Buffalo',
    'CAR': 'Carolina',
    'CGY': 'Calgary',
    'CHI': 'Chicago',
    'CBJ': 'Columbus',
    'COL': 'Colorado',
    'DAL': 'Dallas',
    'DET': 'Detroit',
    'EDM': 'Edmonton',
    'FLA': 'Florida',
    'LAK': 'Los Angeles',
    'MIN': 'Minnesota',
    'MON': 'Montreal',
    'NJD': 'New Jersey',
    'NSH': 'Nashville',
    'NYI': 'N.Y. Islanders',
    'NYR': 'N.Y. Rangers',
    'OTT': 'Ottawa',
    'PHI': 'Philadelphia',
    'PIT': 'Pittsburgh',
    'SEA': 'Seattle',
    'SJS': 'San Jose',
    'STL': 'St. Louis',
    'TBL': 'Tampa Bay',
    'TOR': 'Toronto',
    'UTA': 'Utah',
    'VAN': 'Vancouver',
    'VGK': 'Vegas',
    'WSH': 'Washington',
    'WPG': 'Winnipeg'
}

def poisson_probability_matrix(team1_xG, team2_xG, max_goals=6):
    """Calculate the score probability matrix using Poisson distribution."""
    def calc_distribution(xG):
        probs = [math.exp(-xG) * (xG**k) / math.factorial(k) for k in range(max_goals + 1)]
        return np.array(probs) / sum(probs)
    
    return np.outer(calc_distribution(team1_xG), calc_distribution(team2_xG))

def american_to_probability(odds_str):
    """Convert American odds to implied probability
    +200 means bet 100 to win 200 (underdog, lower probability)
    -200 means bet 200 to win 100 (favorite, higher probability)
    """
    if pd.isna(odds_str):
        return None
    try:
        odds_str = str(odds_str).strip()
        is_plus = odds_str.startswith('+')
        odds = float(odds_str.replace('+', '').replace('-', ''))
        
        if is_plus:
            return 100 / (odds + 100)  # underdog
        else:
            return odds / (odds + 100)  # favorite
    except Exception as e:
        return None

def plot_game_probabilities(team1, team2, team1_xG, team2_xG, team1_odds=None, team2_odds=None, draw_odds=None, actual_scores=None):
    """Plot the probability matrix for a game with team colors."""
    score_matrix = poisson_probability_matrix(team1_xG, team2_xG)
    value_bets = []  # Store value bets for this game
    
    # Create condition matrices
    color_matrix = np.zeros_like(score_matrix, dtype='int')
    color_matrix[np.tril_indices(len(score_matrix), -1)] = 1  # Team 1 wins
    color_matrix[np.diag_indices(len(score_matrix))] = 2      # Draw
    color_matrix[np.triu_indices(len(score_matrix), 1)] = 3   # Team 2 wins
    
    # Get team colors and names
    team1_color = color_dict[team1]
    team2_color = color_dict[team2]
    team1_name = team_names[team1]
    team2_name = team_names[team2]
    
    plt.figure(figsize=(10, 8))
    ax = sns.heatmap(color_matrix, 
                     annot=score_matrix * 100, 
                     fmt=".2f", 
                     cmap=[team1_color, '#808080', team2_color], 
                     cbar=False)
    
    ax.invert_yaxis()
    plt.xlabel(f"{team2_name} Goals")
    plt.ylabel(f"{team1_name} Goals")
    plt.title(f"Probability of Scoreline (%) - {team1_name} vs {team2_name}")
    
    # Calculate win probabilities
    win_team1_prob = np.sum(np.tril(score_matrix, -1))
    win_team2_prob = np.sum(np.triu(score_matrix, 1))
    draw_prob = np.sum(np.diag(score_matrix))
    
    print(f"\n{team1_name} vs {team2_name}")
    print("=" * 40)
    print(f"Expected Goals:")
    print(f"{team1_name}: {team1_xG:.2f}")
    print(f"{team2_name}: {team2_xG:.2f}")
    print("\nModel Probabilities:")
    print(f"{team1_name} win: {win_team1_prob:.1%}")
    print(f"{team2_name} win: {win_team2_prob:.1%}")
    print(f"Draw: {draw_prob:.1%}")
    
    # Compare with sportsbook odds if available
    if team1_odds and team2_odds and draw_odds:
        today = date.today().strftime("%Y-%m-%d")
        book_prob_team1 = american_to_probability(team1_odds)
        book_prob_team2 = american_to_probability(team2_odds)
        book_prob_draw = american_to_probability(draw_odds)
        
        if all([book_prob_team1, book_prob_team2, book_prob_draw]):
            print("\nValue Analysis:")
            print("-" * 40)
            print(f"{'Outcome':<15} {'Model':>7} {'Book':>7} {'Edge':>7} {'Odds':>7}")
            print("-" * 40)
            
            def process_value_line(name, model_prob, book_prob, odds):
                edge = ((model_prob) / book_prob - 1) * 100
                print(f"{name:<15} {model_prob:>6.1%} {book_prob:>6.1%} {edge:>+6.1f}% {odds:>7}")
                
                # Store bets with >10% edge
                if edge > 10:
                    value_bets.append({
                        'Date': today,
                        'Team1': team1,
                        'Team2': team2,
                        'Bet_Type': name,
                        'Model_Prob': model_prob,
                        'Book_Prob': book_prob,
                        'Edge': edge,
                        'Odds': odds,
                        'Result': '',  # To be filled manually
                        'Units': ''    # To be filled manually
                    })
            
            process_value_line(team1_name, win_team1_prob, book_prob_team1, team1_odds)
            process_value_line(team2_name, win_team2_prob, book_prob_team2, team2_odds)
            process_value_line("Draw", draw_prob, book_prob_draw, draw_odds)
    
    print()  # Extra line for spacing
    plt.show()
    return value_bets

def save_value_bets(value_bets):
    """Save value bets to a CSV file."""
    filename = 'value_bets_log.csv'
    file_exists = Path(filename).exists()
    
    fieldnames = ['Date', 'Team1', 'Team2', 'Bet_Type', 'Model_Prob', 
                  'Book_Prob', 'Edge', 'Odds', 'Result', 'Units']
    
    with open(filename, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(value_bets)

def main():
    today = date.today().strftime("%Y-%m-%d")
    try:
        # Read CSV with odds columns as strings
        predictions_df = pd.read_csv('predictions_log.csv', 
                                   dtype={'Team1_Odds': str, 'Team2_Odds': str, 'Draw_Odds': str})
        
        predictions_df = predictions_df.drop_duplicates(
            subset=['Date', 'Team1', 'Team2'], 
            keep='last'
        )
        
        todays_games = predictions_df[predictions_df['Date'] == today]

        if len(todays_games) == 0:
            print(f"No games found for {today} in predictions_log.csv")
            return
        
        print(f"\nAnalyzing NHL Games for {today}")
        print("=" * 40)
        
        # Store all value bets
        all_value_bets = []
        
        # Plot each game and collect value bets
        for _, game in todays_games.iterrows():
            value_bets = plot_game_probabilities(
                game['Team1'],
                game['Team2'],
                float(game['Team1_xG']),
                float(game['Team2_xG']),
                game['Team1_Odds'],
                game['Team2_Odds'],
                game['Draw_Odds'],
                (game['Team1_Score'], game['Team2_Score'])
            )
            all_value_bets.extend(value_bets)
        
        # Save value bets if any found
        if all_value_bets:
            save_value_bets(all_value_bets)
            print(f"\nSaved {len(all_value_bets)} value bets to value_bets_log.csv")

    except Exception as e:
        print(f"Error reading predictions_log.csv: {e}")

if __name__ == "__main__":
    main()