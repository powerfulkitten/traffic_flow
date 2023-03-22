WORKDIR="/var/lib/touchcloud/volume"
DOCKER_COMPOSE_PATH="${WORKDIR}/compose.yml"

sudo mkdir -p $WORKDIR
sudo cp config.json $WORKDIR
sudo cp compose.yml $WORKDIR
docker compose -f $DOCKER_COMPOSE_PATH up -d
