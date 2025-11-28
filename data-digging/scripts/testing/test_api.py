import requests
import json

def get_all_teams():
    """
    Fetches all teams from the NHL API.
    """
    url = "https://api.nhle.com/stats/rest/en/team"
    try:
        response = requests.get(url)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        
        teams_data = response.json()
        print("Successfully fetched data from the NHL API.")
        print("Endpoint: ", url)
        print("\n--- Team Data Sample ---")
        # Print the first team's data for review
        if teams_data.get('data'):
            print(json.dumps(teams_data['data'][0], indent=2))
        else:
            print("No team data found in the response.")
        
        return teams_data

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    
    return None

if __name__ == "__main__":
    get_all_teams()
