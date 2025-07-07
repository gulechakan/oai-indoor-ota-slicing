
# Exit on error
set -e

cd /
sudo mkdir mydata
sudo /usr/local/etc/emulab/mkextrafs.pl -f /mydata

# change the ownership of this new space
username=$(whoami)
groupname=$(id -gn)

sudo chown $username:$groupname mydata
chmod 775 mydata
# verify the result
ls -ld mydata

# Define working directory for CN5G
# CN_DIR="/var/tmp/oai-cn5g"
# CN_DIR="/opt/oai-cn5g"
CN_DIR="/mydata/oai-cn5g"
# GIT_REPO="https://github.com/gulechakan/oai-5gc-modified.git"
# BRANCH="master"  # change to your custom branch name if needed

# Clean up any previous attempt
# sudo rm -rf "$CN_DIR"
# mkdir -p "$CN_DIR"
# cd "$CN_DIR"

# Clone the modified CN5G repo
# sudo git clone -b "$BRANCH" "$GIT_REPO" .

sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT

# Setup the CN node
function setup_cn_node {
    # Install docker, docker compose, wireshark/tshark
    echo setting up cn node
    sudo apt-get update && sudo apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      docker.io \
      docker-compose-v2 \
      gnupg \
      lsb-release

    sudo add-apt-repository -y ppa:wireshark-dev/stable
    echo "wireshark-common wireshark-common/install-setuid boolean false" | sudo debconf-set-selections

    sudo DEBIAN_FRONTEND=noninteractive apt-get update && sudo apt-get install -y \
        wireshark \
        tshark

    sudo systemctl enable docker
    sudo usermod -aG docker $USER

    printf "installing compose"
    until sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose; do
        printf '.'
        sleep 2
    done

    sudo chmod +x /usr/local/bin/docker-compose

    sudo sysctl net.ipv4.conf.all.forwarding=1
    sudo iptables -P FORWARD ACCEPT

    # ignoring the COMMIT_HASH for now
    # sudo cp -r /local/repository/etc/oai/cn5g /var/tmp/oai-cn5g
    echo setting up cn node... done.
}

setup_cn_node

# # Optional: build step if your Docker images are custom
# # echo "Building Docker images..."
# # sudo docker compose -f docker-compose-basic-nrf.yaml build

# # Pull latest images if needed
# echo "Pulling Docker images..."
# sudo docker compose -f docker-compose-basic-nrf.yaml pull

# # Deploy CN5G
# echo "Starting CN5G Docker Compose setup..."
# sudo docker compose -f docker-compose-basic-nrf.yaml up -d

# # Show container status
# sudo docker compose -f docker-compose-basic-nrf.yaml ps

# # Show logs for AMF (optional)
# echo "Following logs for oai-amf..."
# sudo docker compose -f docker-compose-basic-nrf.yaml logs -f oai-amf
