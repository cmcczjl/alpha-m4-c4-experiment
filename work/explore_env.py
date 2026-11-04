#!/usr/bin/env python3
import subprocess, sys
print("Python version:", sys.version)
try:
    import requests
    print("requests available")
except ImportError:
    print("requests not installed")
try:
    from bs4 import BeautifulSoup
    print("BeautifulSoup available")
except ImportError:
    print("BeautifulSoup not installed")