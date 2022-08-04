## Setup (Debian/Ubuntu)
#### Install Python 3.10
1. 
    ```
    sudo apt update && sudo apt upgrade -y
    sudo apt install software-properties-common -y 
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt install python3.10 
    ```
2. Verify installation
    ```
    python3.10 --version
    ```
#### Initialize Project
1. 
    ```
    git clone https://github.com/nrfta/provider-provisioning-adapter.git
    cd provider-provisioning-adapter
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools
    pip install -r requirements.txt
    ```
2. Copy, then fill out the environment variables in the .env file
    ```
   cp .template.env .env
   ```