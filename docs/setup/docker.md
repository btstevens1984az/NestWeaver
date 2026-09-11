# Docker setup

## Prerequisites

- Docker Engine or Docker Desktop  
- Compose v2 (`docker compose`)

## Quick start

```bash
git clone https://github.com/btstevens1984az/NestWeaver.git
cd NestWeaver
docker compose up --build
```

This builds the NestWeaver image, starts **Ollama**, and runs `nestweaver sim-demo`.

## Interactive shell

```bash
docker compose run --rm nestweaver doctor
docker compose run --rm nestweaver sim-demo --scenario fetch
docker compose run --rm --entrypoint bash nestweaver
```

## Pull a model into the Ollama container

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.2:3b
```

## Notes

- ROS 2 desktop is not bundled in the default image (keeps it small). Use a ROS-ready image or the host/Pi for `nestweaver_ros2`.  
- Bind-mount `configs/` is read-only in Compose for safety.
