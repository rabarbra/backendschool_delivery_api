# Backend school test assignment project

### Deploy instruction

```bash
sudo apt install python3 python3-venv nginx-full git build-essential python-dev
mkdir /srv/uwsgi-flask
useradd -d /srv/uwsgi-flask -G www-data -s /bin/bash uwsgi-flask
sudo su uwsgi-flask
cd ~
git clone https://github.com/rabarbra/backendschool_delivery_api appdata
python3 -m venv env
source env/bin/activate
pip install wheel
pip install -r appdata/requirements.txt
python appdata/init_db.py
exit
sudo cp /srv/uwsgi-flask/appdata/sys_configs/uwsgi-flask.conf /etc/nginx/sites-available/
sudo cp /srv/uwsgi-flask/appdata/sys_configs/uwsgi-flask.service /etc/systemd/system/
sudo systemctl reload nginx
sudo systemctl start uwsgi-flask
sudo systemctl enable uwsgi-flask
```

### Requirements

#### Operating system

Ubuntu 20.04.2 LTS

#### System packages

1. Nginx 1.18.0
2. Python3.8.5
3. python3-venv-3.8.2
4. git-1:2.25.1-1ubuntu3
5. build-essential 12.8ubuntu1
6. python-dev 

#### Python packages

1. Flask 1.1.2
2. Flask-SQLAlchemy 2.5.1
3. marshmallow 3.10.0
4. python-dateutil 2.8.1
5. rfc3339 6.2
6. uWSGI 2.0.19.1
