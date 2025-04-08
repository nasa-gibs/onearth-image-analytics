docker run --rm --mount type=bind,source=$(pwd)/app,target=/app -p 86:80 --net docker_oe2 -e WORKERS_PER_CORE="2" --name onearth-analytics --hostname onearth onearth-analytics
