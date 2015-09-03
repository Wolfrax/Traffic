#!/bin/sh
# Configure nginx
cp wolfrax.conf /etc/nginx/sites-available/ # assumes symbolic link from /etc/nginx/sites-enabled to wolfrax.conf
cp nginx.conf /etc/nginx/
service nginx restart
# Configure gunicorn
cp gunicorn.conf /etc/supervisor/conf.d
supervisorctl restart gunicorn
