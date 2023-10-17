# musicgen

1. Install [docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)
2. Follow [post install instructions](https://docs.docker.com/engine/install/linux-postinstall/)
3. Install [docker dependencies](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/1.14.2/install-guide.html#installing-with-apt)
4. Reboot
5. Build and start. Navigate to the directory where your docker-compose.yaml file is located and run the following command:
```bash
docker compose build
docker compose up -d
```

### Maintenance
1. To shut down your Docker Compose service, you can use the docker-compose down command. Navigate to the directory where your docker-compose.yaml file is located and run the following command:

```bash
docker compose down
```
2. If you are debugging you can use
```bash
docker-compose up --remove-orphans
```