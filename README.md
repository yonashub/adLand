# adLand
This program detects ads and finds the landing page of each ad in a given site without actually clicking on the ad
- accepts a single url or list of urls as input.
- appends the output to a log file on each run

usage:


option 1:
``` {r, engine='bash', count_lines}
python  adLand.py urllist.txt useragentlist.txt proxylist.txt
```
option 2:
``` {r, engine='bash', count_lines}
python  adLand.py http://www.example.com
```
