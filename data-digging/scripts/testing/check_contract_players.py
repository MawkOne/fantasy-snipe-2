#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def check_contract_players():
    """Check which players from contract signings are in our projected rosters"""
    
    client = bigquery.Client()
    
    # List of players from the contract signings
    contract_players = [
        'Mikko Rantanen', 'Mitchell Marner', 'Jakob Chychrun', 'Sam Bennett', 'Ivan Provorov',
        'Nikolaj Ehlers', 'Brock Boeser', 'Vladislav Gavrikov', 'Aaron Ekblad', 'Neal Pionk',
        'Adin Hill', 'Conor Garland', 'Brad Marchand', 'Trent Frederic', 'Thatcher Demko',
        'Karel Vejmelka', 'Brock Nelson', 'Mikael Granlund', 'Johnathan Kovacevic', 'Mathieu Olivier',
        'Matt Duchene', 'Ryan Lindgren', 'Cody Ceci', 'John Tavares', 'Tanner Jeannot',
        'Dante Fabbro', 'Ryan Donato', 'Yanni Gourde', 'Kaedan Korczak', 'Dmitry Orlov',
        'Connor Brown', 'Brian Dumoulin', 'Jake Evans', 'Alex Iafallo', 'Olli Maatta',
        'Nate Schmidt', 'Taylor Hall', 'Jason Zucker', 'Kyle Palmieri', 'Charlie Lindgren',
        'Henri Jokiharju', 'Jake Allen', 'Pius Suter', 'Jordan Greenway', 'Jonathan Drouin',
        'Josh Manson', 'Brandon Tanev', 'Andrew Mangiapane', 'Eric Robinson', 'Parker Kelly',
        'Dan Vladar', 'Mikael Backlund', 'Nic Dowd', 'Radek Faksa', 'Mason Appleton',
        'Nicklaus Perbix', 'Anthony Beauvillier', 'Christian Dvorak', 'Joel Armia', 'Anton Forsberg',
        'Ville Husso', 'Andrei Kuzmenko', 'Steven Lorentz', 'Nico Sturm', 'John Klingberg',
        'Adam Gaudette', 'Sean Kuraly', 'Justin Danforth', 'Joel Hanley', 'Nick Bjugstad',
        'Gustav Nyquist', 'Pontus Holmberg', 'Alexander Kerfoot', 'Patrick Kane', 'Alex Lyon',
        'Justin Brazeau', 'Taylor Raddysh', 'Jeff Skinner', 'Michael Eyssimont', 'Ian Cole',
        'Frederik Andersen', 'Isac Lundestrom', 'Jonas Johansson', 'Anthony Mantha', 'Gage Goncalves',
        'Jakob Pelletier', 'Derek Forbort', 'Jonathan Toews', 'Reilly Smith', 'Brandon Saad',
        'Claude Giroux', 'Parker Wotherspoon', 'Corey Perry', 'Haydn Fleury', 'Josh Mahura',
        'Caleb Jones', 'Nathan Walker', 'Tony DeAngelo', 'Philip Tomasino', 'Dominic Toninato',
        'Dryden Hunt', 'Michael Dipietro', 'Michael Pezzetta', 'Dakota Mermis', 'Bo Groulx',
        'Cole Reinhardt', 'Cameron Hebig', 'Cameron Crotty', 'Dylan McIlrath', 'Jack Rathbone',
        'Jaycob Megna', 'Victor Olofsson', 'Wyatt Aamodt', 'Jonathan Quick', 'Lucas Condotta',
        'Joe Hicketts', 'Spencer Smallman', 'Anton Blidh', 'Matthew Murray', 'Jaxson Stauber',
        'John Hayden', 'Steven Santini', 'Cameron Hughes', 'Juha Jaaska', 'William Lagesson'
    ]
    
    # Create a string list for the IN clause
    player_list = "', '".join(contract_players)
    player_list = f"'{player_list}'"
    
    # Check which players are in our current projected rosters
    query = f"""
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    WHERE player_name IN ({player_list})
    ORDER BY team_abbr, player_name
    """
    
    results = client.query(query).to_dataframe()
    
    print('Players from contract signings found in our projected rosters:')
    print('=' * 60)
    for _, row in results.iterrows():
        print(f'{row.player_name:25} | {row.team_abbr:4} | {row.position_type:8} | {row.toi_tier}')
    
    print(f'\nTotal players found: {len(results)}')
    print(f'Total players in contract list: {len(contract_players)}')
    print(f'Missing from rosters: {len(contract_players) - len(results)}')
    
    # Show which players are missing
    found_players = set(results['player_name'].tolist())
    missing_players = set(contract_players) - found_players
    
    if missing_players:
        print(f'\nMissing players from rosters:')
        for player in sorted(missing_players):
            print(f'  - {player}')
    
    return results

if __name__ == "__main__":
    check_contract_players()
