# Agent Smith

GitHub webhook server to catch "merge to master" actions

1. Clone repository.
2. Go to agent-smith directory: `cd agent-smith`
2. Init python virtual environment: `python3 -m venv .venv`
3. Ativate venv and install dependencies:

```
source .venv/bin/activate
pip install -r requirements.txt
```

4. Create service unit: `/etc/systemd/system/agent-smith-1.service`.

```
[Unit]
Description=Agent Smith 1
After=network.target
Wants=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/var/www/apps/agent-smith/
ExecStart=/var/www/apps/agent-smith/.venv/bin/fastapi run main.py --host=127.0.0.1 --port=20001
Restart=always
RestartSec=10
KillMode=process
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

5. Add nginx config:

```
    location /agent-smith/ {
        proxy_pass http://127.0.0.1:20001/;
    }
```

6. Reload daemon and activate systemd unit:

```
sudo systemctl daemon-reload
sudo systemctl enable agent-smith-1.service
sudo systemctl start agent-smith-1.service
```

7. Prepare your `script.sh`. For example:

```
cd /var/www/apps/my-app

git fetch --all
git reset --hard origin/master

sudo /var/www/apps/my-app/.venv/bin/pip install -r requirements.txt

sudo systemctl restart my-app.service
```

8. Create GitHub webhook with event "Pull requests" and secret for it.
