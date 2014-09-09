ripe-atlas-traceroute2kml
=========================

A Python script which reads results from RIPE Atlas traceroute measurements (both IPv4 and IPv6) and generates a *.kml file.

Overview
--------

*  the script analyzes the traceroute results and then shows a plain text summary of traversed ASes:

        [...]
    
        2 probes:  7922, COMCAST-7922 - Comcast Cable Communications, Inc.,US
                   3356, LEVEL3 - Level 3 Communications, Inc.,US
                   3333, RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL
        
        3 probes:  1273, CW Cable and Wireless Worldwide plc,GB
                   1200, AMS-IX1 Amsterdam Internet Exchange B.V.,NL
                   3333, RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL
        
        [...]
* additionally it generates a kml file for route visualisation in google maps


Installation
------------

### Prerequirements

    import ipaddr http://code.google.com/p/ipaddr-py/ - pip install ipaddr
    import simplekml https://code.google.com/p/simplekml/ - pip install simplekml
    import geoip2.database https://github.com/maxmind/GeoIP2-python - with easy_install or pip install geoip2

Download latest GeoLite2 Free Database: http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz

### Generate Config File in the same directory as the generate-kml-from-measurement.py resides
    config.py
    #!/usr/bin/python
    
    # Copyright (c) 2014 Pier Carlo Chiodi - http://www.pierky.com
    # Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT
    #
    # The MIT License (MIT)
    # =====================
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in all
    # copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.
    # 
    # Part of this work is based on Raphael JavaScript Library by Dmitry Baranovskiy 
    # (http://raphaeljs.com/) and Dracula Graph Library by Johann Philipp Strathausen
    # (http://www.graphdracula.net/).
    
    import os
    
    __version__ = "0.1"
    
    
    
    DATA_DIR = "/ripe-atlas-traceroute2kml/cache"
    KML_FILE = "output.kml"
    GEOIP_FILE = "/resources/GeoLite2-City.mmdb"


Usage
-----

For each run, the RIPE Atlas measurement ID is required; if the measurement is not public, the API key is also needed in order to access the results.

Results are then downloaded in a local file for later use; traceroute hops IP addresses are analyzed using the "ipdetailscache" library (https://github.com/pierky/ipdetailscache) and their details locally cached.


Command line mode syntax:

    ./ripeatlastracepath [-k api_key ] [-f] measurement_id
    
    Options:
        -k      RIPEAtlas API key to access the measurement
        -f      Skip local measurement cache and force its download

Third-party Libraries
---------------------
Part of this work is based of the project ripeatlastracepath. Thanks a lot to Pier Carlo Chiodi - http://www.pierky.com




