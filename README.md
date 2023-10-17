# musicgen

1. Install docker and docker-compose and/or docker desktop 
2. Install docker dependencies

```bash
sudo apt install nvidia-docker2
```
3. Reboot
4. Build and start. Navigate to the directory where your docker-compose.yaml file is located and run the following command:
```bash
docker-compose build
docker-compose up -d
```

### Maintenance
1. To shut down your Docker Compose service, you can use the docker-compose down command. Navigate to the directory where your docker-compose.yaml file is located and run the following command:

```bash
docker-compose down
```
