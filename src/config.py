import os
import sys
from dotenv import load_dotenv

# --- Configuration Variables ---
# The project_id and secret_id are hardcoded here for simplicity.
# In a larger application, these might also come from environment variables.
GCP_PROJECT_ID = "fantasy-snipe-ai"
DB_PASSWORD_SECRET_ID = "db-password"
DB_USER_SECRET_ID = "db-user"
DB_NAME_SECRET_ID = "db-name"

# --- Environment Detection ---
# Check if we're in a Cloud Run environment (either service or job)
# Google Cloud Run services set K_SERVICE, Cloud Run Jobs set K_REVISION
IS_CLOUD_RUN = 'K_SERVICE' in os.environ or 'K_REVISION' in os.environ
print(f"Environment detection: IS_CLOUD_RUN={IS_CLOUD_RUN}, K_SERVICE={os.environ.get('K_SERVICE', 'NOT_SET')}, K_REVISION={os.environ.get('K_REVISION', 'NOT_SET')}", file=sys.stderr)

def get_secret(secret_id):
    """
    Fetches a secret from Google Secret Manager if in Cloud Run environment,
    otherwise falls back to environment variables for local development.
    """
    if IS_CLOUD_RUN:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            
            # Construct the secret version name
            name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"
            
            # Access the secret version
            response = client.access_secret_version(name=name)
            
            # Return the decoded secret payload
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error fetching secret {secret_id} from Google Secret Manager: {e}", file=sys.stderr)
            # If we are in Cloud Run and fail to get the secret, we should fail hard.
            sys.exit(f"Could not retrieve secret {secret_id} from Secret Manager. Exiting.")
    else:
        # --- Local Development Fallback ---
        # For local development, load variables from a .env file.
        load_dotenv()
        
        # Map secret IDs to environment variable names
        env_var_map = {
            "db-password": "DB_PASS",
            "db-user": "DB_USER", 
            "db-name": "DB_NAME"
        }
        
        env_var = env_var_map.get(secret_id)
        if not env_var:
            print(f"Unknown secret ID: {secret_id}", file=sys.stderr)
            sys.exit(1)
            
        value = os.environ.get(env_var)
        if not value:
            print(f"{env_var} environment variable not found.", file=sys.stderr)
            print("Please ensure you have a .env file with the correct credentials for local development.", file=sys.stderr)
            sys.exit(1)
        return value

def get_db_password():
    """Fetches the database password."""
    return get_secret(DB_PASSWORD_SECRET_ID)

def get_db_user():
    """Fetches the database user."""
    return get_secret(DB_USER_SECRET_ID)

def get_db_name():
    """Fetches the database name."""
    return get_secret(DB_NAME_SECRET_ID)

# --- Load Credentials ---
# Load credentials from the appropriate source when the module is imported.
# Note: For local development, INSTANCE_CONNECTION_NAME still comes from .env
load_dotenv()
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME")
DB_USER = get_db_user()
DB_NAME = get_db_name()
DB_PASS = get_db_password()
