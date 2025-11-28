import time
from google.cloud import bigquery
import google.generativeai as genai

# Setup
genai.configure(api_key="AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk")
model = genai.GenerativeModel('gemini-2.5-pro')
bq_client = bigquery.Client(project="fantasy-snipe-ai")

# Test query
start = time.time()

# Step 1: AI generates SQL
print("🤖 Asking AI to generate SQL...")
t1 = time.time()
prompt = "Generate SQL: Top 5 players by shot attempts. Table: fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat"
sql_response = model.generate_content(prompt)
print(f"   ⏱️  AI SQL generation: {time.time() - t1:.2f}s")

# Step 2: Execute BigQuery
print("📊 Executing BigQuery...")
t2 = time.time()
query = "SELECT player_id, SUM(CF) as total FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` WHERE season = 20242025 AND game_type = 2 GROUP BY player_id ORDER BY SUM(CF) DESC LIMIT 5"
result = bq_client.query(query).result()
data = list(result)
print(f"   ⏱️  BigQuery execution: {time.time() - t2:.2f}s")

# Step 3: AI explains
print("🤖 AI explaining results...")
t3 = time.time()
explain = model.generate_content("Explain these results: " + str(data))
print(f"   ⏱️  AI explanation: {time.time() - t3:.2f}s")

print(f"\n⏱️  TOTAL TIME: {time.time() - start:.2f}s")
