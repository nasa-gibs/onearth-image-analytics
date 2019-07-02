# Varnish-Cache Overview

The varnish cache service is an in-memory HTTP cache which caches responses to HTTP requests. This can save a fair bit of time over S3 requests and save money for the most commonly made requests.

## Setup

The setup.sh script should setup varnish from scratch. Sometimes, you need to replace the line `varnishd -a localhost:80 -b localhost:8095` with `varnishd -a [IP ADDRESS]:80 -b localhost:8095`. 8095 is an arbitrary choice for a backend port. Varnish acts as an HTTP frontend which checks its cache and routes the request to the Apache backend if not found.

## Statistics and Logs:

varnishlog -g session
varnishstat

varnishd -a is the listening port -b is the backend port.

## Restarting Apache:

/usr/sbin/apache2ctl restart
httpd -k restart

## Assorted Utilities:

ss -nutlp to view port usage
httpd -k restart to restart
varnishlog -q 'RespStatus == 503' -g request to log 503

## Profiling:

These benchmarks are all local, so they don't reflect time savings from S3 requests.

With Varnish:

siege -c 5 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg

Transactions:		         250 hits
Availability:		      100.00 %
Elapsed time:		        1.00 secs
Data transferred:	        8.64 MB
Response time:		        0.02 secs
Transaction rate:	      250.00 trans/sec
Throughput:		        8.64 MB/sec
Concurrency:		        4.11
Successful transactions:         250
Failed transactions:	           0
Longest transaction:	        0.06
Shortest transaction:	        0.00

siege -c 25 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg

Transactions:		        1250 hits
Availability:		      100.00 %
Elapsed time:		        3.88 secs
Data transferred:	       43.22 MB
Response time:		        0.06 secs
Transaction rate:	      322.16 trans/sec
Throughput:		       11.14 MB/sec
Concurrency:		       20.88
Successful transactions:        1250
Failed transactions:	           0
Longest transaction:	        0.23
Shortest transaction:	        0.00

siege -c 50 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg 

Transactions:		        2490 hits
Availability:		       99.60 %
Elapsed time:		        7.96 secs
Data transferred:	       86.10 MB
Response time:		        0.14 secs
Transaction rate:	      312.81 trans/sec
Throughput:		       10.82 MB/sec
Concurrency:		       43.36
Successful transactions:        2490
Failed transactions:	          10
Longest transaction:	        0.58
Shortest transaction:	        0.01

siege -c 50 -r 50 -i -f links.txt (for 5 links, including 404)

Transactions:		        2500 hits
Availability:		      100.00 %
Elapsed time:		       11.60 secs
Data transferred:	       35.13 MB
Response time:		        0.21 secs
Transaction rate:	      215.52 trans/sec
Throughput:		        3.03 MB/sec
Concurrency:		       44.41
Successful transactions:        1466
Failed transactions:	           0
Longest transaction:	        0.87
Shortest transaction:	        0.00

siege -c 100 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg (some connection reset by peer errors)

Transactions:		        4924 hits
Availability:		       98.48 %
Elapsed time:		       22.03 secs
Data transferred:	      170.26 MB
Response time:		        0.39 secs
Transaction rate:	      223.51 trans/sec
Throughput:		        7.73 MB/sec
Concurrency:		       87.18
Successful transactions:        4924
Failed transactions:	          76
Longest transaction:	        3.21
Shortest transaction:	        0.01

siege -c 50 -r 50 -i -f links.txt

Transactions:		        4911 hits
Availability:		       98.22 %
Elapsed time:		       23.86 secs
Data transferred:	       69.73 MB
Response time:		        0.43 secs
Transaction rate:	      205.83 trans/sec
Throughput:		        2.92 MB/sec
Concurrency:		       89.43
Successful transactions:        2950
Failed transactions:	          89
Longest transaction:	        2.23
Shortest transaction:	        0.01

Without varnish:

siege -c 5 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg

Transactions:		         250 hits
Availability:		      100.00 %
Elapsed time:		        1.12 secs
Data transferred:	        8.64 MB
Response time:		        0.02 secs
Transaction rate:	      223.21 trans/sec
Throughput:		        7.72 MB/sec
Concurrency:		        3.85
Successful transactions:         250
Failed transactions:	           0
Longest transaction:	        0.08
Shortest transaction:	        0.00

siege -c 25 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg

Transactions:		        1250 hits
Availability:		      100.00 %
Elapsed time:		        5.36 secs
Data transferred:	       43.22 MB
Response time:		        0.09 secs
Transaction rate:	      233.21 trans/sec
Throughput:		        8.06 MB/sec
Concurrency:		       20.80
Successful transactions:        1250
Failed transactions:	           0
Longest transaction:	        0.62
Shortest transaction:	        0.00

siege -c 50 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg

Transactions:		        2478 hits
Availability:		       99.12 %
Elapsed time:		       10.53 secs
Data transferred:	       85.69 MB
Response time:		        0.19 secs
Transaction rate:	      235.33 trans/sec
Throughput:		        8.14 MB/sec
Concurrency:		       44.32
Successful transactions:        2478
Failed transactions:	          22
Longest transaction:	        0.86
Shortest transaction:	        0.01

siege -c 50 -r 50 -i -f links.txt (for 5 links, including 404)

Transactions:		        2485 hits
Availability:		       99.40 %
Elapsed time:		       13.21 secs
Data transferred:	       35.47 MB
Response time:		        0.25 secs
Transaction rate:	      188.12 trans/sec
Throughput:		        2.69 MB/sec
Concurrency:		       46.28
Successful transactions:        1496
Failed transactions:	          15
Longest transaction:	        1.74
Shortest transaction:	        0.01

siege -c 100 -r 50 http://localhost/oe-status/BlueMarble16km/default/2004-08-01/16km/1/0/0.jpeg (some connection reset by peer errors)

Transactions:		        4977 hits
Availability:		       99.54 %
Elapsed time:		       31.23 secs
Data transferred:	      172.10 MB
Response time:		        0.56 secs
Transaction rate:	      159.37 trans/sec
Throughput:		        5.51 MB/sec
Concurrency:		       88.71
Successful transactions:        4977
Failed transactions:	          23
Longest transaction:	        7.75
Shortest transaction:	        0.01

siege -c 100 -r 50 -i -f links.txt

Transactions:		        4975 hits
Availability:		       99.50 %
Elapsed time:		       28.69 secs
Data transferred:	       69.97 MB
Response time:		        0.52 secs
Transaction rate:	      173.41 trans/sec
Throughput:		        2.44 MB/sec
Concurrency:		       90.72
Successful transactions:        2965
Failed transactions:	          25
Longest transaction:	        3.00
Shortest transaction:	        0.01
