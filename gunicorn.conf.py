import os
import subprocess
import sys


bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 1
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"


def on_starting(server):
    subprocess.run([sys.executable, "migrate_schema.py"], check=False)
