# Yandex backend school test assignment project

### Deploy instruction

```bash
apt install python3 python3-venv nginx-full git
mkdir /srv/uwsgi-flask
useradd -d /srv/uwsgi-flask -G www-data -s /bin/bash uwsgi-flask
sudo su uwsgi-flask
cd ~
git clone https://github.com/rabarbra/yandex_backendschool_delivery_api appdata
python -m venv env
source env/bin/activate
pip install -r appdata/requirements.txt
python appdata/init_db.py
exit
sudo cp /srv/uwsgi-flask/appdata/sys_configs/uwsgi-flask.conf /etc/nginx/sites-available/
sudo cp /srv/uwsgi-flask/appdata/sys_configs/uwsgi-flask.service /etc/systemd/system/
sudo systemctl reload nginx
sudo systemctl start uwsgi-flask
sudo systemctl enable uwsgi-flask
```
