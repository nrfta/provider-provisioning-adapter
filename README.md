## Setup (Debian/Ubuntu)
### Initialize Project
1. Install python3.10 
    ```sh
    sudo apt update && sudo apt upgrade -y
    sudo apt install software-properties-common -y 
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt install python3.10 python3.10-venv
    curl -O https://bootstrap.pypa.io/get-pip.py
    python3.10 get-pip.py
    ```
2. Verify installation
    ```sh
    python3.10 --version
    ```
3. Create virtual environment
   ```sh
   mkdir {{ project_dir }}
   cd {{ project_dir }}
   python3.10 -m venv .venv
   source ./venv/bin/activate
   ```
4. Install project dependencies
   ```sh
   pip install --upgrade pip setuptools
   pip install --find-links=https://github.com/nrfta/provider-provisioning-adapter/releases/latest provider-provisioning-adapter 
   ```
5. Define environment variables
   ```sh
   # Paths to scripts. Must be executable by user
   export PPA_SERVICE_CREATE=  
   export PPA_SERVICE_MODIFY=
   export PPA_SERVICE_REMOVE=
   export PPA_SERVICE_TIMEOUT=  # unit == seconds, defaults to 180 seconds if not set
   export PPA_PORT=  # defaults to port 8888
   export PPA_LOG_LEVEL=  # one of: debug | info | warning | error
   export PPA_LOG_DIR=
   ```
6. Run
   ```sh
   ppa-serve
   ```
### (Optional) systemd
1. Create systemd service config
   ```
   [Unit]
   Description=Underline provider provisioning adapter
   After=network.target
   
   [Service]
   Type=notify
   User={{ USER }}
   Group={{ GROUP }}
   EnvironmentFile={{ APPLICATION_DIR}}/.env
   WorkingDirectory={{ APPLICATION_DIR }}
   ExecStart={{ APPLICATION_DIR }}/.venv/bin/ppa-serve
   ExecReload=/bin/kill -s HUP $MAINPID
   KillMode=mixed
   TimeoutStopSec=5
   PrivateTmp=true
   
   [Install]
   WantedBy=multi-user.target
   ```
2. Reload daemon
   ```sh
   sudo systemctl daemon-reload
   ```
3. Enable and start custom service
   ```sh
   sudo systemctl enable ppa
   sudo systemctl start ppa
   ```
4. Verify the service is functional
   ```systemctl status ppa```
### (Optional) Reverse Proxy
1. Install Caddy via package manager
   1. Instructions can be found on Caddy's website; [here](https://caddyserver.com/docs/install#debian-ubuntu-raspbian)
2. edit /etc/caddy/Caddyfile
   ```sh
   sudo cat << EOF > /etc/caddy/Caddyfile
   {{ DOMAIN NAME }}
   
   reverse-proxy 127.0.0.1:{{ PPA_PORT }}
   EOF
   ```
3. Reload caddy service after saving the new config
   ```sh
   sudo systemctl reload caddy 
   ```
4. Verify caddy is up and running
   ```sh
   systemctl status caddy
   ```
## Scripts
Scripts can be written in any language. The only requirements are this: it must be executable, and accept a single string argument as a positional param.
The data being passed to the script is a minified JSON string. The shape of the object differs between the CREATE/REMOVE scripts and the MODIFY script - as seen below.

#### CREATE/REMOVE scripts data shape
```json
{
  "provider_handoff": {
    "circuitId": "TEST-SPC-1",
    "vlan": "20"
  },
  "service": {
    "type": "data",
    "detail": {
      "data": {
        "downloadSpeedKbps": 500000,
        "uploadSpeedKbps": 500000
      }
    }
  },
  "subscription_id": "d81446c0-5547-4cc3-8223-2f51f482b48b",
  "sonar_account_id": 3942936
}
```

#### MODIFY script data shape
```json
{
  "old_provider_handoff": {
    "vlan": "3",
    "circuitId": "CKT-R0-S2-A-MOCK-1"
  },
  "old_service": {
    "type": "data",
    "detail": {
      "data": {
        "downloadSpeedKbps": 500000,
        "uploadSpeedKbps": 500000
      }
    }
  },
  "new_provider_handoff": {
    "vlan": "13",
    "circuitId": "swp3"
  },
  "new_service": {
    "type": "data",
    "detail": {
      "data": {
        "downloadSpeedKbps": 10000000,
        "uploadSpeedKbps": 10000000
      }
    }
  },
  "new_subscription_id": "d81446c0-5547-4cc3-8223-2f51f482b48b",
  "old_subscription_id": "d2fd364f-d95a-4533-9a5d-84f23eb8881c",
  "sonar_account_id": "3942926"
}
```

### Bash Example
The example uses [jq](https://stedolan.github.io/jq/). Install the dependency before running the script: ```sudo apt install jq```
```sh
#!/usr/bin/env bash
# CREATE new service

set -e  # Exit script on any failure. 
        # Utilize flow control structures to check for errors. Use `exit 1` to signal there was an error
        ## Example: if <condition failure>; then exit 1; fi;

cid=$(jq -r '.provider_handoff.circuitId' <<< "$1")
vid=$(jq -r '.provider_handoff.vlan' <<< "$1")
customer_id=$(jq -r '.sonar_account_id' <<< "$1")
speed["download"]=$(jq -r '.service.detail.data.downloadSpeedKbps' <<< "$1")
speed["upload"]=$(jq -r '.service.detail.data.uploadSpeedKbps' <<< "$1")

echo "Processing customer ${customer_id} on vlan ${vid}"
echo "Requested download speed: ${speed["download"]}Kbps, " "Requested upload speed: ${speed["upload"]}Kbps"
echo

# pseudo config
cat << EOF
set vlans ${cid}
set vlans ${cid} vlan-id ${vid}
set interfaces ge-0/0/0 unit 0 description Customer:${customer_id},Service:${cid}
set interfaces ge-0/0/0 unit 0 family ethernet-switching vlan members ${cid}
EOF
```
