#!/bin/bash
cd /opt/
mitmdump -s smartrent-bridge.py --set http2 false & sleep 5 & python3 smartrent-login.py
