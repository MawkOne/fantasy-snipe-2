#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def update_roster_team_assignments():
    """Update roster team assignments based on contract signings"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("UPDATING ROSTER TEAM ASSIGNMENTS BASED ON CONTRACT SIGNINGS")
    print("="*80)
    
    # Key player team assignments based on contract signings
    player_team_updates = {
        'Mitchell Marner': 'TOR',  # Missing from rosters
        'Mikko Rantanen': 'COL',   # Currently on DAL, should be COL
        'Jakob Chychrun': 'WAS',   # Currently on WSH, should be WAS (Washington)
        'Sam Bennett': 'FLA',      # Currently on FLA, this is correct
        'Ivan Provorov': 'CBJ',    # Currently on CBJ, this is correct
        'Nikolaj Ehlers': 'WPG',   # Currently on CAR, should be WPG
        'Brock Boeser': 'VAN',     # Currently on VAN, this is correct
        'Vladislav Gavrikov': 'LAK', # Currently on LAK, this is correct
        'Aaron Ekblad': 'FLA',     # Currently on FLA, this is correct
        'Neal Pionk': 'WPG',       # Currently on WPG, this is correct
        'Adin Hill': 'VGK',        # Currently on VGK, this is correct
        'Conor Garland': 'VAN',    # Currently on VAN, this is correct
        'Brad Marchand': 'BOS',    # Currently on FLA, should be BOS
        'Trent Frederic': 'BOS',   # Currently on EDM, should be BOS
        'Thatcher Demko': 'VAN',   # Currently on VAN, this is correct
        'Brock Nelson': 'NYI',     # Currently on COL, should be NYI
        'Mikael Granlund': 'SJS',  # Currently on ANA and DAL, should be SJS
        'John Tavares': 'TOR',     # Currently on TOR, this is correct
        'Tanner Jeannot': 'TBL',   # Currently on LAK, should be TBL
        'Dante Fabbro': 'NSH',     # Currently on CBJ, should be NSH
        'Ryan Donato': 'CHI',      # Currently on CHI, this is correct
        'Yanni Gourde': 'TBL',     # Currently on TBL, this is correct
        'Kaedan Korczak': 'VGK',   # Currently on VGK, this is correct
        'Dmitry Orlov': 'DET',     # Currently on CAR and SJS, should be DET
        'Connor Brown': 'EDM',     # Currently on EDM, this is correct
        'Brian Dumoulin': 'PIT',   # Currently on NJD, should be PIT
        'Jake Evans': 'MTL',       # Currently on MTL, this is correct
        'Alex Iafallo': 'WPG',     # Currently on WPG, this is correct
        'Olli Maatta': 'DET',      # Currently on UTA, should be DET
        'Nate Schmidt': 'FLA',     # Currently on FLA, this is correct
        'Taylor Hall': 'CHI',      # Currently on CAR, should be CHI
        'Jason Zucker': 'BUF',     # Currently on BUF, this is correct
        'Kyle Palmieri': 'NYI',    # Currently on NYI, this is correct
        'Charlie Lindgren': 'WSH', # Currently on WSH, this is correct
        'Henri Jokiharju': 'BOS',  # Currently on BOS, this is correct
        'Jake Allen': 'NJD',       # Currently on NJD, this is correct
        'Pius Suter': 'STL',       # Currently on STL and VAN, should be STL
        'Jordan Greenway': 'BUF',  # Currently on BUF, this is correct
        'Jonathan Drouin': 'COL',  # Currently on COL and NYI, should be COL
        'Josh Manson': 'COL',      # Currently on COL, this is correct
        'Brandon Tanev': 'WPG',    # Currently on WPG, this is correct
        'Andrew Mangiapane': 'CGY', # Currently on EDM and WSH, should be CGY
        'Eric Robinson': 'CAR',    # Currently on CAR, this is correct
        'Parker Kelly': 'OTT',     # Currently on COL, should be OTT
        'Dan Vladar': 'CGY',       # Missing from rosters
        'Mikael Backlund': 'CGY',  # Currently on CGY, this is correct
        'Nic Dowd': 'WSH',         # Currently on WSH, this is correct
        'Radek Faksa': 'STL',      # Currently on STL, this is correct
        'Mason Appleton': 'WPG',   # Currently on WPG, this is correct
        'Nicklaus Perbix': 'TBL',  # Missing from rosters
        'Anthony Beauvillier': 'WSH', # Currently on WSH, this is correct
        'Christian Dvorak': 'MTL', # Currently on MTL, this is correct
        'Joel Armia': 'MTL',       # Currently on MTL, this is correct
        'Anton Forsberg': 'OTT',   # Currently on OTT, this is correct
        'Ville Husso': 'DET',      # Missing from rosters
        'Andrei Kuzmenko': 'CGY',  # Currently on LAK, should be CGY
        'Steven Lorentz': 'TOR',   # Currently on TOR, this is correct
        'Nico Sturm': 'FLA',       # Currently on FLA, this is correct
        'John Klingberg': 'TOR',   # Currently on EDM, should be TOR
        'Adam Gaudette': 'OTT',    # Currently on OTT, this is correct
        'Sean Kuraly': 'CBJ',      # Currently on CBJ, this is correct
        'Justin Danforth': 'CBJ',  # Currently on CBJ, this is correct
        'Joel Hanley': 'DAL',      # Currently on CGY, should be DAL
        'Nick Bjugstad': 'UTA',    # Currently on UTA, this is correct
        'Gustav Nyquist': 'NSH',   # Currently on MIN and WPG, should be NSH
        'Pontus Holmberg': 'TOR',  # Currently on TOR, this is correct
        'Alexander Kerfoot': 'UTA', # Currently on UTA, this is correct
        'Patrick Kane': 'DET',     # Currently on DET, this is correct
        'Alex Lyon': 'DET',        # Currently on DET, this is correct
        'Justin Brazeau': 'BOS',   # Currently on MIN, should be BOS
        'Taylor Raddysh': 'CHI',   # Currently on WSH, should be CHI
        'Jeff Skinner': 'EDM',     # Currently on EDM, this is correct
        'Michael Eyssimont': 'SEA', # Currently on SEA, this is correct
        'Ian Cole': 'UTA',         # Currently on UTA, this is correct
        'Frederik Andersen': 'CAR', # Currently on CAR, this is correct
        'Isac Lundestrom': 'ANA',  # Currently on ANA, this is correct
        'Jonas Johansson': 'TBL',  # Currently on TBL, this is correct
        'Anthony Mantha': 'CGY',   # Currently on CGY, this is correct
        'Gage Goncalves': 'TBL',   # Currently on TBL, this is correct
        'Jakob Pelletier': 'CGY',  # Currently on PHI and TBL, should be CGY
        'Derek Forbort': 'VAN',    # Currently on VAN, this is correct
        'Jonathan Toews': 'CHI',   # Currently on WPG, should be CHI
        'Reilly Smith': 'VGK',     # Currently on VGK, this is correct
        'Brandon Saad': 'STL',     # Currently on VGK, should be STL
        'Claude Giroux': 'OTT',    # Currently on OTT, this is correct
        'Parker Wotherspoon': 'BOS', # Currently on BOS, this is correct
        'Corey Perry': 'EDM',      # Currently on EDM, this is correct
        'Haydn Fleury': 'WPG',     # Currently on WPG, this is correct
        'Josh Mahura': 'SEA',      # Currently on SEA, this is correct
        'Caleb Jones': 'LAK',      # Currently on LAK, this is correct
        'Nathan Walker': 'STL',    # Currently on STL, this is correct
        'Tony DeAngelo': 'CAR',    # Missing from rosters
        'Philip Tomasino': 'NSH',  # Currently on PIT, should be NSH
        'Dominic Toninato': 'WPG', # Currently on WPG, this is correct
        'Dryden Hunt': 'CGY',      # Currently on CGY, this is correct
        'Michael Dipietro': 'VAN', # Missing from rosters
        'Michael Pezzetta': 'MTL', # Currently on MTL, this is correct
        'Dakota Mermis': 'TOR',    # Currently on TOR, this is correct
        'Bo Groulx': 'NYR',        # Currently on NYR, this is correct
        'Cole Reinhardt': 'NYI',   # Missing from rosters
        'Cameron Hebig': 'EDM',    # Missing from rosters
        'Cameron Crotty': 'BOS',   # Missing from rosters
        'Dylan McIlrath': 'WSH',   # Currently on WSH, this is correct
        'Jack Rathbone': 'VAN',    # Missing from rosters
        'Jaycob Megna': 'FLA',     # Currently on FLA, this is correct
        'Victor Olofsson': 'BUF',  # Currently on VGK, should be BUF
        'Wyatt Aamodt': 'MIN',     # Missing from rosters
        'Jonathan Quick': 'NYR',   # Currently on NYR, this is correct
        'Lucas Condotta': 'MTL',   # Missing from rosters
        'Joe Hicketts': 'DET',     # Missing from rosters
        'Spencer Smallman': 'CAR', # Missing from rosters
        'Anton Blidh': 'BOS',      # Missing from rosters
        'Matthew Murray': 'TOR',   # Missing from rosters
        'Jaxson Stauber': 'CHI',   # Missing from rosters
        'John Hayden': 'SEA',      # Currently on SEA, this is correct
        'Steven Santini': 'NSH',   # Missing from rosters
        'Cameron Hughes': 'BOS',   # Missing from rosters
        'Juha Jaaska': 'CAR',      # Currently on CAR, this is correct
        'William Lagesson': 'DET', # Currently on DET, this is correct
    }
    
    # First, let's check which players need to be added or moved
    print("Checking players that need team updates...")
    
    updates_needed = []
    for player, correct_team in player_team_updates.items():
        query = f"""
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE player_name = '{player}'
        """
        
        results = client.query(query).to_dataframe()
        
        if results.empty:
            updates_needed.append((player, correct_team, 'MISSING'))
        else:
            current_team = results.iloc[0]['team_abbr']
            if current_team != correct_team:
                updates_needed.append((player, correct_team, f'WRONG TEAM (currently {current_team})'))
    
    print(f"\nPlayers needing updates: {len(updates_needed)}")
    print("=" * 60)
    for player, correct_team, issue in updates_needed:
        print(f'{player:25} | {correct_team:4} | {issue}')
    
    # For now, let's just report the issues
    # In a real implementation, we would update the BigQuery table
    print(f"\n✅ Found {len(updates_needed)} players that need team assignment updates")
    print("These updates would need to be applied to the projected_rosters_2025_26 table")

if __name__ == "__main__":
    update_roster_team_assignments()
