# GeoTiny EDU — Project-Based Seismology

Service: Flask app serving live vendor spectrum and global seismic activity,
plus education pages. This repo tracks the running deployment at:
`/srv/learnlab/geotiny-edu`.

How to run (systemd):
- service: geotiny-edu.service
- status: `systemctl status geotiny-edu.service --no-pager -l`
- restart: `sudo systemctl restart geotiny-edu.service`
- URL: http://127.0.0.1:8050/

Workflow:
- Create a feature branch per change.
- Commit small, revert quickly if needed.
- After each deploy, verify the site and `journalctl -u geotiny-edu.service -n 100`.

