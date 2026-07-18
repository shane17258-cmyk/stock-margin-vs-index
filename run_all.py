import json
import os
from datetime import datetime, timezone, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 50)
print("Step 1: Fetching data...")
print("=" * 50)
exec(open(os.path.join(DATA_DIR, "fetch_data.py")).read())

print("\n" + "=" * 50)
print("Step 2: Plotting charts...")
print("=" * 50)
exec(open(os.path.join(DATA_DIR, "plot_charts.py")).read())

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)
update_info = {
    "update_time": now.strftime("%Y-%m-%d %H:%M") + " (UTC+8)"
}
with open(os.path.join(DATA_DIR, "update_info.json"), "w", encoding="utf-8") as f:
    json.dump(update_info, f, ensure_ascii=False)
print(f"\nUpdate info saved: {update_info['update_time']}")
print("\nAll done!")
