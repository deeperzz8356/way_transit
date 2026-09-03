"""Find where PostgreSQL is actually listening."""
import socket, os

# Check common ports
for port in [5432, 5433, 5434, 5435]:
    try:
        s = socket.create_connection(("localhost", port), timeout=1)
        s.close()
        print(f"PostgreSQL reachable at localhost:{port}")
    except:
        print(f"localhost:{port} - not reachable")

# Also check the remote IP from .env
try:
    s = socket.create_connection(("100.66.96.15", 5432), timeout=2)
    s.close()
    print("Remote 100.66.96.15:5432 - reachable")
except:
    print("Remote 100.66.96.15:5432 - NOT reachable (this is your problem)")

# Check pg_config for data directory
try:
    import subprocess
    r = subprocess.run(["pg_config", "--bindir"], capture_output=True, text=True, timeout=5)
    print(f"pg_config bindir: {r.stdout.strip()}")
except:
    pass

# Check Windows registry for PostgreSQL port
try:
    import winreg
    for ver in ["9.6","10","11","12","13","14","15","16","17"]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                f"SOFTWARE\\PostgreSQL\\Installations\\postgresql-x64-{ver}")
            port = winreg.QueryValueEx(key, "Port")[0]
            datadir = winreg.QueryValueEx(key, "Data Directory")[0]
            print(f"PostgreSQL {ver}: port={port}, data={datadir}")
        except:
            pass
except:
    pass
