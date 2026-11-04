#!/usr/bin/env python3
import os
import json

def get_cpu():
    return os.cpu_count()

def get_mem():
    try:
        import psutil
        return psutil.virtual_memory().total
    except Exception:
        # fallback using os.sysconf
        pages = os.sysconf('SC_PHYS_PAGES')
        page_size = os.sysconf('SC_PAGE_SIZE')
        return pages * page_size

def main():
    data = {
        'cpu': get_cpu(),
        'mem': get_mem()
    }
    print(json.dumps(data))

if __name__ == '__main__':
    main()