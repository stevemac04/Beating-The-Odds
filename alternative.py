# importing libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
from datetime import date
import math

# reading files (taken from https://www.naturalstattrick.com/)
goalies_df_2022_23 = pd.read_csv('goalies_2022_23.csv')
goalies_df_2024 = pd.read_csv('goalies_2024.csv')
skaters_df_2022_23 = pd.read_csv('skaters_2022_23.csv')
skaters_df_2024 = pd.read_csv('skaters_2024.csv')

# establish a weight so that the most recent season has more effect on the xG and gsaa value we assign to players
weight = 2/3

def calculate_weighted_metric(df, metric, weight, season_col='Season', toi_col='TOI'):
    """
    Calculate the weighted metric for a given DataFrame, applying a specified weight to the metric
    and time on ice (TOI) columns based on the season.

    Args:
    df (DataFrame): The DataFrame containing player data.
    metric (string): The metric to be weighted (e.g., 'ixG', 'GSAA').
    weight (float): The weight to apply to the most recent season.
    season_col (string): The column name for the season. Defaults to 'Season'.
    toi_col (string): The column name for time on ice. Defaults to 'TOI'.

    Returns:
    DataFrame: The DataFrame with new columns for the weighted metric and weighted TOI.
    """
    df[f'Weighted_{metric}'] = df.apply(
        lambda row: row[metric] * (weight if row[season_col] == '2024' else (1 - weight)), axis=1)
    df['Weighted_TOI'] = df.apply(
        lambda row: row[toi_col] * (weight if row[season_col] == '2024' else (1 - weight)), axis=1)
    return df

def calculate_weighted_average(df, player_col='Player', metric='ixG'):
    """
    Calculate the weighted average of a specified metric, grouped by player.

    Args:
    df (DataFrame): The DataFrame containing player data.
    player_col (string): The column name for player identification. Defaults to 'Player'.
    metric (string): The metric to calculate the weighted average for. Defaults to 'ixG'.

    Returns:
    DataFrame: A DataFrame with players and their corresponding weighted average of the metric.
    """
    return df.groupby(player_col).apply(
        lambda df: df[f'Weighted_{metric}'].sum() / df['Weighted_TOI'].sum()).reset_index(name=f'Weighted_{metric}')

# Add 'Season' column
skaters_df_2022_23['Season'] = '2022_23'
skaters_df_2024['Season'] = '2024'

# Concatenate skater dataframes
skaters_df = pd.concat([skaters_df_2022_23, skaters_df_2024])

# Calculate weighted xG for skaters
skaters_df = calculate_weighted_metric(skaters_df, 'ixG', weight)
xG_df = calculate_weighted_average(skaters_df, metric='ixG')

# Add 'Season' column for goalies
goalies_df_2022_23['Season'] = '2022_23'
goalies_df_2024['Season'] = '2024'

# Concatenate goalie dataframes
goalies_df = pd.concat([goalies_df_2022_23, goalies_df_2024])

# Calculate weighted GSAA for goalies
goalies_df = calculate_weighted_metric(goalies_df, 'GSAA', weight)
gsaa_df = calculate_weighted_average(goalies_df, metric='GSAA')

def forward_line_calc(team, line, skaters_list, xG_dict, toi_list):
    """
    Calculates the xG for a single forward line of a team using the average minutes 
    for that line of players and their respective historical xG values.
    """
    line_xG = 0
    player_index = team*18 + line*3
    toi_start = line*3  # Each line starts at 0, 3, 6, or 9 in toi_list
    for i in range(3):
        index = player_index + i
        player_xG = xG_dict.get(skaters_list[index], 0)
        player_xG = player_xG * toi_list[toi_start + i]
        line_xG += player_xG
    return line_xG

def defense_line_calc(team, line, skaters_list, xG_dict, toi_list):
    """
    Calculates the xG for a single defensive line of a team using the average minutes 
    for that line of players and their respective historical xG values.
    """
    line_xG = 0
    player_index = team*18 + 12 + (line-5)*2
    toi_start = 12 + (line-5)*2  # Defense pairs start at 12, 14, or 16 in toi_list
    for i in range(2):
        index = player_index + i
        player_xG = xG_dict.get(skaters_list[index], 0)
        player_xG = player_xG * toi_list[toi_start + i]
        line_xG += player_xG
    return line_xG

def calculate_team_expected_scores(matchups_list, skaters_list, goalies_list, xG_dict, gsax_dict, toi_list):
    """
    Calculates expected scores for each team based on their lineup's xG values 
    and opposing goalie's GSAA.
    """
    expected_score = []
    
    # Read teams.csv for historical data - fixing the header issue
    teams_df = pd.read_csv('teams.csv', header=0)  # explicitly set first row as header
    teams_df = teams_df[teams_df['situation'] == 'all']  # lowercase 'situation'
    
    for team in range(len(matchups_list)):
        current_x_score = 0
        # Calculate forward lines
        for f_line in range(4):
            current_x_score += forward_line_calc(team, f_line, skaters_list, xG_dict, toi_list)
        # Calculate defense lines
        for d_line in range(4, 7):
            current_x_score += defense_line_calc(team, d_line, skaters_list, xG_dict, toi_list)
        
        # Get team data for GSAX adjustment
        team_name = matchups_list[team]
        team_data = teams_df[teams_df['team'] == team_name]
        if not team_data.empty:
            goals_for = float(team_data['goalsFor'].iloc[0])
            xgoals_for = float(team_data['xGoalsFor'].iloc[0])
            ice_time = float(team_data['iceTime'].iloc[0])
            
            # Calculate half of goals scored above/below expected per 60
            gsax_adjustment = 30 * (goals_for - xgoals_for) / ice_time
            current_x_score += gsax_adjustment
        
        # Adjust for opposing goalie AFTER team adjustment
        opposing_goalie = goalies_list[team+1] if team%2 == 0 else goalies_list[team-1]
        current_x_score -= gsax_dict.get(opposing_goalie, 0)
        
        expected_score.append(current_x_score)
    
    # Format scores to 2 decimal places
    formatted_scores = ['%.2f' % elem for elem in expected_score]
    return formatted_scores, matchups_list
