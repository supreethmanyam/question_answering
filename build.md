docker ps
docker exec -it <CONTAINER_ID> /bin/bash

docker build . -t qa
docker run -p 8080:8080 qa