import time

# Data Timestamp
ts_data = 17641232360

# Current Unix Timestamp (Seconds)
ts_now_sec = 1764207669

# Test 1: Is data in Milliseconds?
# 17641232360 / 1000 = 17,641,232 seconds
# That would be year 1970. Too small.

# Test 2: Is data in Centiseconds (100 ticks/sec)?
# 17641232360 / 100 = 176,412,323 seconds
# Year 1975. Too small.

# Test 3: Is data in Deciseconds (10 ticks/sec)?
# 17641232360 / 10 = 1,764,123,236 seconds
# Let's format that date.
print(f"Data Raw: {ts_data}")
print(f"Assumed Deciseconds -> Seconds: {ts_data / 10}")
print(f"Current Seconds: {ts_now_sec}")

diff = ts_now_sec - (ts_data / 10)
print(f"Difference in seconds: {diff}")
print(f"Difference in hours: {diff / 3600}")

