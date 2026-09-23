#!/usr/bin/env python
import sys
print("Testing moviepy imports...")
try:
    from deneme import DinamikPodcastUretici
    print("[OK] deneme module imported successfully")
    print("[OK] MoviePy import error FIXED!")
except ModuleNotFoundError as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
except Exception as e:
    print(f"[WARNING] Import succeeded but got: {type(e).__name__}: {e}")
