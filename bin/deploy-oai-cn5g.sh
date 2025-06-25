
# Exit on error
set -e

# Define working directory for CN5G
CN_DIR="/var/tmp/oai-cn5g"
GIT_REPO="https://github.com/gulechakan/oai-5gc-modified.git"
BRANCH="master"  # change to your custom branch name if needed

# Clean up any previous attempt
sudo rm -rf "$CN_DIR"
mkdir -p "$CN_DIR"
cd "$CN_DIR"

# Clone the modified CN5G repo
sudo git clone -b "$BRANCH" "$GIT_REPO" .

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
