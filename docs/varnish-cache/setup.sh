#!/bin/bash

yum -y install varnish
sed -i ’s/Listen 80/Listen 8095/‘ /etc/httpd/conf/httpd.conf
httpd -k restart
varnishd -a localhost:80 -b localhost:8095 
