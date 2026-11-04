#!/usr/bin/env python3
import os
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join("data", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_dummy_summary(index: int) -> str:
    # Simple placeholder summary; in a real scenario this would be fetched from a news source.
    return f"News Summary #{index + 1}: This is a placeholder summary for demonstration purposes."

def main():
    base_time = datetime.now()
    for i in range(3):
        # Slightly offset timestamps to ensure distinct filenames
        timestamp = (base_time + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        filename = f"news_{timestamp}_{i+1}.txt"
        file_path = os.path.join(OUTPUT_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(generate_dummy_summary(i) + "\n")
        print(f"Created: {file_path}")

if __name__ == "__main__":
    main()