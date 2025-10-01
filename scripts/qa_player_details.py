from google.cloud import bigquery
import pandas as pd

def qa_player_details():
    client = bigquery.Client()

    print("=== PLAYER DETAILS QA ===")
    print()

    # 1. Check total count
    count_query = "SELECT COUNT(*) as total FROM `fantasy-snipe-ai.nhl_raw.players`"
    result = list(client.query(count_query).result())
    total_players = result[0]["total"]
    print(f"1. Total players ingested: {total_players}")

    # 2. Check data completeness
    completeness_query = """
    SELECT 
      COUNT(*) as total,
      COUNT(birth_date) as has_birth_date,
      COUNT(position) as has_position,
      COUNT(full_name) as has_full_name,
      COUNT(height_inches) as has_height,
      COUNT(weight_pounds) as has_weight,
      COUNT(draft_year) as has_draft_info,
      COUNT(shoots_catches) as has_shoots_catches
    FROM `fantasy-snipe-ai.nhl_raw.players`
    """
    result = list(client.query(completeness_query).result())[0]
    print(f"2. Data completeness:")
    print(f"   - Has birth_date: {result['has_birth_date']}/{result['total']} ({result['has_birth_date']/result['total']*100:.1f}%)")
    print(f"   - Has position: {result['has_position']}/{result['total']} ({result['has_position']/result['total']*100:.1f}%)")
    print(f"   - Has full_name: {result['has_full_name']}/{result['total']} ({result['has_full_name']/result['total']*100:.1f}%)")
    print(f"   - Has height: {result['has_height']}/{result['total']} ({result['has_height']/result['total']*100:.1f}%)")
    print(f"   - Has weight: {result['has_weight']}/{result['total']} ({result['has_weight']/result['total']*100:.1f}%)")
    print(f"   - Has draft info: {result['has_draft_info']}/{result['total']} ({result['has_draft_info']/result['total']*100:.1f}%)")
    print(f"   - Has shoots_catches: {result['has_shoots_catches']}/{result['total']} ({result['has_shoots_catches']/result['total']*100:.1f}%)")

    # 3. Check position distribution
    position_query = """
    SELECT position, COUNT(*) as count
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE position IS NOT NULL
    GROUP BY position
    ORDER BY count DESC
    """
    print(f"3. Position distribution:")
    for row in client.query(position_query).result():
        print(f"   - {row['position']}: {row['count']}")

    # 4. Check age range
    age_query = """
    SELECT 
      MIN(EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM birth_date)) as min_age,
      MAX(EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM birth_date)) as max_age,
      AVG(EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM birth_date)) as avg_age
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE birth_date IS NOT NULL
    """
    result = list(client.query(age_query).result())[0]
    print(f"4. Age range:")
    print(f"   - Min age: {result['min_age']}")
    print(f"   - Max age: {result['max_age']}")
    print(f"   - Avg age: {result['avg_age']:.1f}")

    # 5. Sample some high-profile players
    sample_query = """
    SELECT player_id, full_name, position, birth_date, current_team_abbrev, draft_year, draft_overall_pick
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE full_name IN ('Connor McDavid', 'Leon Draisaitl', 'Sidney Crosby', 'Alexander Ovechkin', 'Nathan MacKinnon')
    ORDER BY full_name
    """
    print(f"5. Sample high-profile players:")
    for row in client.query(sample_query).result():
        print(f"   - {row['full_name']} ({row['position']}) - {row['birth_date']} - {row['current_team_abbrev']} - Draft: {row['draft_year']} #{row['draft_overall_pick']}")

    # 6. Check for any data quality issues
    quality_query = """
    SELECT 
      COUNT(CASE WHEN player_id IS NULL THEN 1 END) as null_player_ids,
      COUNT(CASE WHEN full_name = '' THEN 1 END) as empty_names,
      COUNT(CASE WHEN birth_date < '1900-01-01' THEN 1 END) as old_birth_dates,
      COUNT(CASE WHEN birth_date > CURRENT_DATE() THEN 1 END) as future_birth_dates
    FROM `fantasy-snipe-ai.nhl_raw.players`
    """
    result = list(client.query(quality_query).result())[0]
    print(f"6. Data quality issues:")
    print(f"   - NULL player_ids: {result['null_player_ids']}")
    print(f"   - Empty names: {result['empty_names']}")
    print(f"   - Birth dates before 1900: {result['old_birth_dates']}")
    print(f"   - Future birth dates: {result['future_birth_dates']}")

    # 7. Check draft year distribution
    draft_query = """
    SELECT 
      draft_year,
      COUNT(*) as count
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE draft_year IS NOT NULL
    GROUP BY draft_year
    ORDER BY draft_year DESC
    LIMIT 10
    """
    print(f"7. Recent draft years (top 10):")
    for row in client.query(draft_query).result():
        print(f"   - {row['draft_year']}: {row['count']} players")

    # 8. Check team distribution
    team_query = """
    SELECT 
      current_team_abbrev,
      COUNT(*) as count
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE current_team_abbrev IS NOT NULL
    GROUP BY current_team_abbrev
    ORDER BY count DESC
    LIMIT 10
    """
    print(f"8. Current team distribution (top 10):")
    for row in client.query(team_query).result():
        print(f"   - {row['current_team_abbrev']}: {row['count']} players")

    print()
    print("=== QA COMPLETE ===")

if __name__ == "__main__":
    qa_player_details()
