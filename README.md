# Beating-The-Odds
NHL Betting Algorithm that uses historical data for specific players and daily lineups to find value betting opportunities
The process:

Get historical data ƒor NHL players [https://www.naturalstattrick.com/]
Use xG and TOI to find an efficiency statistic that can quantify goals created / time on ice

bs4 scrape (I copy and paste manually the html as to not violate TOS) daily lineups for each team [https://rotogrinders.com/lineups/nhl#]
Clean lineups to a normalized and homogenous format (both with xG data and for easier parsing)
Use projected lineups and xG value to create a predicted scoreline
Alter scoreline prediction with goalie's GSAx

Use poisson distribution with predicted scoreline to find proabability of different score outcomes in the game
Visualization of probabilities

bs4 scrape (I copy and paste manually the html to not violate TOS) live odds from draftkings [draftkings]
Compare model's probabilities of outcomes to betting odds and identify value bets
