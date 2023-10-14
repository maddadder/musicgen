# musicgen

1. Deploy as a service

```bash
chmod +x app.sh
sudo cp musicgen.service /etc/systemd/system/musicgen.service
sudo systemctl daemon-reload
sudo systemctl start musicgen
sudo systemctl restart musicgen
sudo systemctl enable musicgen
sudo systemctl status musicgen
```