#!/usr/bin/env python3
import json
import sys

def inspect_json(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        print(f"--- JSON Structure Inspection ---")
        print(f"Root type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            # Print first key's value type if exists
            if data:
                first_key = next(iter(data))
                print(f"Sample Key '{first_key}' type: {type(data[first_key])}")
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
            if len(data) > 0:
                print(f"First element type: {type(data[0])}")
        
        print(f"\n--- Raw Head (First 500 chars) ---")
        with open(filepath, 'r') as f:
            print(f.read(500))
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    target = "data/output/news_digest.json"
    inspect_json(target)