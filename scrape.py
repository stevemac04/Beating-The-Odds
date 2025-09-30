# importing libraries
import pandas as pd
from bs4 import BeautifulSoup
import requests
# Import functions from alternative.py
from alternative import calculate_weighted_metric, calculate_weighted_average, calculate_team_expected_scores
from datetime import date
import csv
import os
import json

# Get html of rotowire (where daily lineups come from)
rotowire = requests.get("https://rotogrinders.com/lineups/nhl#")
html_rotowire = BeautifulSoup(rotowire.content, "html.parser")

def scrape(tag, class_val, attr_name, html, positions=None):
    """
    Scrapes for a repeated tag and class that represents something desired, returning a list
    with all cases that match the desired case. If 'positions' is specified, it filters by the
    'data-position' attribute.

    Args:
    tag (string): Tag that is being searched for.
    class_val (string): Value of the class attribute to match.
    attr_name (string): The name of the attribute to extract. If "text", extracts text content.
    html (BeautifulSoup object): The HTML content to be scraped.
    positions (list, optional): List of allowed values for the 'data-position' attribute. Defaults to None.

    Returns:
    list: List of all values found in the specified attribute or text content, filtered if 'positions' is provided.
    """
    matched_elements = html.find_all(tag, class_=class_val)
    result_list = []

    for element in matched_elements:
        if positions:
            parent = element.find_parent("span", class_="player-nameplate")
            if parent and parent.get("data-position") not in positions:
                continue

        if attr_name == "text":
            result_list.append(element.get_text(strip=True))
        elif element.get(attr_name):
            result_list.append(element.get(attr_name))

    return result_list

# Get matchups, goalies, and skaters
matchups_list = scrape("span", "team-nameplate-title", "data-abbr", html_rotowire)
goalies_list = scrape("a", "player-nameplate-name", "text", html_rotowire, ['G'])
skaters_list = scrape("a", "player-nameplate-name", "text", html_rotowire, ['W', 'C', 'D'])

def handle_missing_players(matchups, skaters, goalies):
    """
    Prompts user to add any missing players to the lineup lists.
    Format: "[team] [position] [line] [player name]" or "False" if no additions needed
    Example: "BOS F 2 David Pastrnak" or "TOR G 1 Joseph Woll"
    
    Args:
    matchups (list): List of team abbreviations
    skaters (list): List of skater names
    goalies (list): List of goalie names
    
    Returns:
    tuple: Updated lists of (skaters, goalies)
    """
    while True:
        print("\nToday's Games:")
        for i in range(0, len(matchups), 2):
            print(f"{matchups[i]} vs {matchups[i+1]}")
        
        # Count total players needed
        total_skaters_needed = len(matchups) * 18 - len(skaters)
        total_goalies_needed = len(matchups) - len(goalies)
        
        print(f"\nTotal players needed:")
        print(f"Skaters: {total_skaters_needed} (18 per team)")
        print(f"Goalies: {total_goalies_needed} (1 per team)")
        
        print("\nAdd missing player in format: [team] [position] [line] [player name]")
        print("Example: 'BOS F 2 David Pastrnak' or 'TOR G 1 Joseph Woll'")
        print("Enter 'False' when finished")
        
        user_input = input("\nEnter player info or 'False': ").strip()
        
        if user_input.lower() == 'false':
            break
            
        try:
            team, position, line, *name = user_input.split()
            player_name = ' '.join(name)
            
            if team not in matchups:
                print(f"Error: Team {team} is not playing today")
                continue
                
            if position.upper() == 'G':
                goalies.append(player_name)
                print(f"Added goalie {player_name} to {team}")
            elif position.upper() == 'F' or position.upper() == 'D':
                skaters.append(player_name)
                print(f"Added {position} {player_name} to {team}")
            else:
                print("Error: Position must be 'F', 'D', or 'G'")
                continue
                
        except ValueError:
            print("Error: Invalid input format. Please use: [team] [position] [line] [player name]")
            continue
            
    return skaters, goalies

# Allow user to add any missing players
skaters_list, goalies_list = handle_missing_players(matchups_list, skaters_list, goalies_list)

# Read CSV files
goalies_df_2022_23 = pd.read_csv('goalies_2022_23.csv')
goalies_df_2024 = pd.read_csv('goalies_2024.csv')
skaters_df_2022_23 = pd.read_csv('skaters_2022_23.csv')
skaters_df_2024 = pd.read_csv('skaters_2024.csv')

# Add Season columns
skaters_df_2022_23['Season'] = '2022_23'
skaters_df_2024['Season'] = '2024'
goalies_df_2022_23['Season'] = '2022_23'
goalies_df_2024['Season'] = '2024'

# Concatenate dataframes
skaters_df = pd.concat([skaters_df_2022_23, skaters_df_2024])
goalies_df = pd.concat([goalies_df_2022_23, goalies_df_2024])

# Calculate weighted metrics
weight = 2/3
skaters_df = calculate_weighted_metric(skaters_df, 'ixG', weight)
xG_df = calculate_weighted_average(skaters_df, metric='ixG')
goalies_df = calculate_weighted_metric(goalies_df, 'GSAA', weight)
gsaa_df = calculate_weighted_average(goalies_df, metric='GSAA')

# Convert DataFrames to dictionaries for lookup
xG_dict = xG_df.set_index('Player')['Weighted_ixG'].to_dict()
gsax_dict = gsaa_df.set_index('Player')['Weighted_GSAA'].to_dict()

# Define time on ice list for each position
toi_list = [
    19.33, 19.33, 19.33,  # Line 1 (LW, C, RW)
    16.37, 16.37, 16.37,  # Line 2 (LW, C, RW)
    13.47, 13.47, 13.47,  # Line 3 (LW, C, RW)
    12.58, 12.58, 12.58,  # Line 4 (LW, C, RW)
    23.22, 23.22,         # Pair 1 (LD, RD)
    20.0, 20.0,           # Pair 2 (LD, RD)
    17.53, 17.53          # Pair 3 (LD, RD)
]

# Calculate expected scores
scores, matchups = calculate_team_expected_scores(
    matchups_list, 
    skaters_list, 
    goalies_list, 
    xG_dict, 
    gsax_dict, 
    toi_list
)

print(scores)
print(matchups)

def get_game_odds(matchups):
    """
    Prompts user to input 60-minute odds for each game.
    Format: [team1_odds] [team2_odds] [draw_odds]
    Example: +130 -110 +280
    
    Args:
    matchups (list): List of team abbreviations
    
    Returns:
    dict: Dictionary containing odds for each team and draws
    """
    odds_dict = {}
    
    print("\nEnter 60-minute odds for each game.")
    print("Format: [team1_odds] [team2_odds] [draw_odds]")
    print("Example: +130 -110 +280")
    print("Press Enter to skip odds for a game\n")
    
    for i in range(0, len(matchups), 2):
        team1, team2 = matchups[i], matchups[i+1]
        print(f"\n{team1} vs {team2}")
        odds_input = input("Enter odds: ").strip()
        
        if odds_input:
            try:
                team1_odds, team2_odds, draw_odds = odds_input.split()
                odds_dict[team1] = team1_odds
                odds_dict[team2] = team2_odds
                odds_dict[f"{team1}_{team2}_draw"] = draw_odds
            except ValueError:
                print(f"Invalid format for {team1} vs {team2}, skipping odds")
                odds_dict[team1] = ''
                odds_dict[team2] = ''
                odds_dict[f"{team1}_{team2}_draw"] = ''
        else:
            odds_dict[team1] = ''
            odds_dict[team2] = ''
            odds_dict[f"{team1}_{team2}_draw"] = ''
    
    return odds_dict

def save_predictions(scores, matchups, odds_dict=None):
    """
    Saves the predictions, matchups, and odds to a CSV file with the current date.
    Creates the file if it doesn't exist, appends if it does.
    """
    today = date.today().strftime('%Y-%m-%d')
    filename = 'predictions_log.csv'
    file_exists = os.path.isfile(filename)
    
    # Pair teams with their scores and odds
    games = []
    for i in range(0, len(matchups), 2):
        team1, team2 = matchups[i], matchups[i+1]
        game = {
            'Date': today,
            'Team1': team1,
            'Team1_xG': scores[i],
            'Team2': team2,
            'Team2_xG': scores[i+1],
            'Team1_Odds': odds_dict[team1] if odds_dict else '',
            'Team2_Odds': odds_dict[team2] if odds_dict else '',
            'Draw_Odds': odds_dict.get(f"{team1}_{team2}_draw", '') if odds_dict else '',
            'Team1_Score': '',
            'Team2_Score': ''
        }
        games.append(game)
    
    # Write to CSV
    with open(filename, mode='a', newline='') as file:
        fieldnames = ['Date', 'Team1', 'Team1_xG', 'Team2', 'Team2_xG', 
                     'Team1_Odds', 'Team2_Odds', 'Draw_Odds',
                     'Team1_Score', 'Team2_Score']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(games)

# Get odds for each game
odds_dict = get_game_odds(matchups)

# After calculating scores, save them with odds
save_predictions(scores, matchups, odds_dict)

# Create a dictionary mapping teams to their scores for the score matrix
team_score_dict = dict(zip(matchups, scores))

# Export the team_score_dict for use in score_matrix.py
with open('team_scores.json', 'w') as f:
    json.dump(team_score_dict, f)