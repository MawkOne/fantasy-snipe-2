import time
from google.cloud import bigquery
import google.generativeai as genai

genai.configure(api_key="AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk")
model = genai.GenerativeModel('gemini-2.5-flash')  # FLASH model
bq_client = bigquery.Client(project="fantasy-snipe-ai")

start = time.time()

print("🤖 Asking Gemini FLASH to generate SQL...")
t1 = time.time()
prompt = "Generate SQL: Top 5 players by shot attempts. Table: fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat, season=20242025"
sql_response = model.generate_content(prompt)
print(f"   ⏱️  AI SQL generation: {time.time() - t1:.2f}s")

print("📊 Executing BigQuery...")
t2 = time.time()
query = "SELECT player_id, SUM(CF) as total FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` WHERE season = 20242025 AND game_type = 2 GROUP BY player_id ORDER BY SUM(CF) DESC LIMIT 5"
result = bq_client.query(query).result()
data = list(result)
print(f"   ⏱️  BigQuery: {time.time() - t2:.2f}s")

print("🤖 Gemini FLASH explaining...")
t3 = time.time()
explain = model.generate_content("Explain in 1 sentence: " + str(data[:2]))
print(f"   ⏱️  AI explanation: {time.time() - t3:.2f}s")

print(f"\n⏱️  TOTAL TIME: {time.time() - start:.2f}s")
