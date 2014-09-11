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

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import getopt
import json
import urllib
import ipdetailscache
import simplekml
import geoip2.database
import config
import time
from datetime import date
from html import HTML
import pprint
import math

__version__ = "0.1"

DATA_DIR = config.DATA_DIR
KML_FILE = config.KML_FILE
GEOIP_FILE = config.GEOIP_FILE

#DATA_DIR = ''.join([os.environ['HOME'], "/traceroute_cache"])
#KML_FILE = ''.join([os.environ['HOME'], "/output.kml"])
#GEOIP_FILE = ''.join([os.path.dirname(os.path.abspath(__file__)),"/GeoLite2-City.mmdb"])

#GEOIP_FILE = "/opt/geoip2/GeoLite2-City.mmdb"
try:
	os.stat(DATA_DIR)
except:
	os.mkdir(DATA_DIR)

APIKey				= ""
MeasurementID			= 0
ASPathRadiusFromTarget		= 20
AlsoIncludeIncompletePaths	= False
ForceDownload			= False

def PrintLine(s):
	print(s)

def PrintNoNewLine(s):
	sys.stdout.write( s )
def PrintLine(s):
	print(s)
def Usage():
	PrintLine("")
	PrintLine("ripe-kml-generator %s, Copyright (c) 2014 Mathias Handsche" % __version__)
	PrintLine("")
	PrintLine("Usage: %s [-k api_key ] [-f] measurement_id" % ( sys.argv[0] ) )
	PrintLine("")
	PrintLine("Options:")
	PrintLine("	-k	RIPEAtlas API key to access the measurement")
	PrintLine("	-f	Skip local measurement cache and force its download")
	PrintLine("")
# ------------------------------------------------------------------

def print_descr(tbl_el):
	table= "<table>"
	table += "<tr><td><b>Probe ID</b></td><td>" + str(tbl_el["Probe ID"]) + "</td>"
	table += "<tr><td><b>IPv4 ASN</b></td><td>" + tbl_el["IPv4 ASN"] + "</td>"
	table += "<tr><td><b>IPv4 Prefix</b></td><td>" + tbl_el["IPv4 Prefix"] + "</td>"
	if tbl_el["IPv6 ASN"] != "NA":
		table += "<tr><td><b>IPv6 ASN</b></td><td>" + tbl_el["IPv6 ASN"] + "</td>"
	if tbl_el["IPv6 Prefix"] != "NA":
		table += "<tr><td><b>IPv6 Prefix</b></td><td>" + tbl_el["IPv6 Prefix"] + "</td>"
	if tbl_el["Country Code"] != "NA":
		table += "<tr><td><b>Country Code</b></td><td>" + tbl_el["Country Code"] + "</td>"
	if tbl_el["Up since"] != "NA":
		table += "<tr><td><b>Up since</b></td><td>" + tbl_el["Up since"] + "</td>"
	if tbl_el["Down since"] != "NA":
        	table += "<tr><td><b>Down since</b></td><td>" + tbl_el["Down since"] + "</td>"
	table += "</table>"
	return str(table)

def getProbeInfo(): 
	url= "https://atlas.ripe.net/contrib/active_probes.json"
	js = "%s/probes.json" % ( DATA_DIR)

	if os.path.isfile(js) and os.path.getctime(js) > (time.time() - 86400):
		PrintLine("Active Probes Json up to date")
	else:
		try:
			urllib.urlretrieve(url, js)
		except: 
			PrintLine("Can't download Active Probes")
			quit()

	json_data = open(js)
	j = json.load( json_data )
	json_data.close()
	
	hashr = {} 
	for e in j:
		d={}
		up= e[0]
		d["lat"]= e[1]
		d["lon"]= e[2]
		a= e[3]
		for i in range(0,len(a),2):
			d[a[i]]= a[i+1]
		if "IPv6 Prefix" not in d.keys():
			d["IPv6 Prefix"] = "NA"
		else:
			up= "UP6"
                if "IPv6 ASN" not in d.keys():
                        d["IPv6 ASN"] = "NA"
		else:
                        up= "UP6"
		if "IPv4 Prefix" not in d.keys():
                        d["IPv4 Prefix"] = "NA"
		if "IPv4 ASN" not in d.keys():
                        d["IPv4 ASN"] = "NA"
		if "Country Code" not in d.keys():
                        d["Country Code"] = "NA"
		if "Up since" not in d.keys():
                        d["Up since"] = "NA"
		if "Down since" not in d.keys():
                        d["Down since"] = "NA"
		descr = print_descr(d)
		d["desc"] = descr

		hashr[d["Probe ID"]] = d

	return(hashr)

def distance_on_unit_sphere(lat1, long1, lat2, long2):

    if (lat1 == lat2 and long1 == long2):
    	return(0)

    PrintLine("Latitude: %.4f Longitude: %.4f \nLatitude: %.4f Longitude: %.4f" % (lat1, long1, lat2, long2))
    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
        
    # Compute spherical distance from spherical coordinates.
        
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return (arc * 6373)

def median(mylist):
    if (len(mylist) == 0):
        return(0)
    sorts = sorted(mylist)
    length = len(sorts)
    if not length % 2:
        return (sorts[length / 2] + sorts[length / 2 - 1]) / 2.0
    return sorts[length / 2]

def color_selctor(latency,distance):
	expected_latency = distance / 200

	if latency <= expected_latency * 1:  # wahrscheinlich fehler da zu schnell
		colorhex = "FF0000"
	elif latency <= expected_latency * 1.5:
		colorhex = "00FF00"
	elif latency <= expected_latency * 2:
		colorhex = "FFFF00"
	else:
		colorhex = "FF0000"

	return(simplekml.Color.hex(colorhex))
# ------------------------------------------------------------------

try:
	opts, args = getopt.getopt(sys.argv[1:],"hifr:k:")
	for opt, arg in opts:
		if opt == "-k":
			APIKey = arg

		elif opt == "-f":
			ForceDownload = True

		elif opt == "-h":
			Usage()
			quit()

		else:
			PrintLine( "Unexpected option: %s" % opt )
			Usage()
			quit()

	if len(args) < 1:
		PrintLine( "Measurement ID not specified" )
		Usage()
		quit()
	else:
		if args[0].isdigit():
			MeasurementID = int(args[0])
			if MeasurementID <= 0:
				PrintLine("Measurement ID must be > 0")
				Usage()
				quit()
		else:
			PrintLine( "Number expected for measurement ID" )
			Usage()
			quit()

except getopt.GetoptError:
	Usage()

try:
	IPCache = ipdetailscache.IPDetailsCache( Debug = False, IP_ADDRESSES_CACHE_FILE = "%s/ip_addr.cache" % DATA_DIR, IP_PREFIXES_CACHE_FILE = "%s/ip_pref.cache" % DATA_DIR );
except:
	PrintLine("Error opening the IP details cache. Verify write permissions on %s for the running user." % DATA_DIR)
	quit()

DataOK = False

if not ( ForceDownload ):
	try:
		json_data = open( "%s/m%s.json" % ( DATA_DIR, MeasurementID ) )
		data = json.load( json_data )
		json_data.close()
		DataOK = True
	except:
		pass

if( not DataOK ):
	try:
		urllib.urlretrieve( "https://atlas.ripe.net/api/v1/measurement/%s/result/?key=%s" % ( MeasurementID, APIKey ), "%s/m%s.json" % ( DATA_DIR, MeasurementID ) )
	except:
		PrintLine("Can't download measurement results.")
		PrintLine("Verify that measurement ID (%d) is correct and that measurement is public, otherwise set the correct API key with -k option." % ( MeasurementID ) );
		PrintLine("Check also that local directory (%s) has write permissions for the current user." % DATA_DIR)
		quit()

	try:
		json_data = open( "%s/m%s.json" % ( DATA_DIR, MeasurementID ) )
		data = json.load( json_data )
		json_data.close()

		DataOK = True
	except:
		pass

if( not DataOK ):
	PrintLine("Can't get JSON data.")
	quit()	


# ------------------------------------------------------------------

h = getProbeInfo()
Rows			= []
ASPaths			= []	# [ [ { "ASN": xxx, "Holder": "xxx" }, ... ] ]
InvalidProbes		= []
ProbesWithErrors	= []
IncompleteProbes	= []
ValidProbesCount	= 0	# only results with one or more IP addresses different from both the source and the target in the middle of the path are considered valid
kml					= simplekml.Kml()
reader				= geoip2.database.Reader(GEOIP_FILE)

probe_details = getProbeInfo()

doc = kml.newdocument(name = "UDM: " + str(MeasurementID))
kml.document = doc

h = HTML('html')
t = h.table(border='1')
r = t.tr
r.td('Measurement ID')
r.td(str(MeasurementID))
r = t.tr
r.td('Destination IP')
r.td(str(data[0]["dst_addr"]))
r = t.tr
r.td('Destination Name')
r.td(str(data[0]["dst_name"]))
r = t.tr
r.td('Starttime:')
r.td(date.fromtimestamp(int(data[0]["timestamp"])).strftime('%Y-%m-%d %H:%M:%S'))
r = t.tr
r.td('Endtime')
r.td(date.fromtimestamp(int(data[0]["endtime"])).strftime('%Y-%m-%d %H:%M:%S'))
r = t.tr
r.td('IP Version')
r.td(str(data[0]["af"]))
r = t.tr
r.td('Paris ID')
r.td(str(data[0]["paris_id"]))
r = t.tr
r.td('Protocol')
r.td(str(data[0]["proto"]))
r = t.tr
r.td('Size of Packets')
r.td(str(data[0]["size"]))

PrintLine(type(str(h)))

PrintLine(str(h))


doc.description = str(h)

# Probe Result

for result in data:

	IPAddress = result["from"]
	if IPAddress == "":
		IPAddress = result["src_addr"]

	if IPAddress == "":
		continue

	ProbeID = str(result["prb_id"])

	if not int(ProbeID) in probe_details:
		PrintLine("ProbeID to skip: " + ProbeID)
		continue

	ASPath = []
	TracerouteCompleted = False
	Valid = False

	geo = reader.city(IPAddress)

	#l = []
	#l.append(IPAddress)
	#l.append(geo.location.latitude)
	#l.append(geo.location.longitude)
	#

	#m = IPAddress + geo.location.latitude + geo.location.longitude

	#PrintLine(m)

	IPAddressDetails = IPCache.GetIPInformation( IPAddress )

	#PrintLine(IPAddressDetails)

	fol = doc.newfolder(name=ProbeID)
	#fol.description()

	pnt = fol.newpoint(name=ProbeID, 
			 description=''.join(["IP Address: ", IPAddress ,"\nPrefix: ",IPAddressDetails["Prefix"], "\nASN: ", IPAddressDetails["ASN"], "\nHostname: ", IPAddressDetails["HostName"], "\nHolder: ",IPAddressDetails["Holder"]]), 
			 #coords=[(geo.location.longitude,geo.location.latitude)]
			 coords=[(probe_details[int(ProbeID)]["lon"],probe_details[int(ProbeID)]["lat"])]
			 )

	pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/sunny.png'
	pnt.style.iconstyle.scale = 3

	ASPath.append( { "ASN": IPAddressDetails["ASN"], "Holder": IPAddressDetails["Holder"] } )

	Cols = []

	last_rtt = 0
	last_longitude = 0
	last_latitude = 0
	last_IPAddress = ""

	Cols.append( result["prb_id"] )
	Cols.append( "{: <5}".format("From") )
	Cols.append( IPAddress )
	Cols.append( IPAddressDetails["ASN"] )
	Cols.append( IPAddressDetails["Holder"] )
	Cols.append( IPAddressDetails["Prefix"] )
	Cols.append( IPAddressDetails["HostName"] )
	Cols.append( 0 )
	Cols.append( 255 )
	Cols.append( 0 )
	Rows.append( Cols )

	# Hops from each probe 

	for hop in result["result"]:
		if hop.get("error","") == "":
			LastIPAddress = ""
			listrtt = []

			for rttcounter in hop["result"]:
				if rttcounter.get("rtt","") != "":
					listrtt.append(float(rttcounter["rtt"]))

			for response in hop["result"]:
				if response.get("from","") != "":
					IPAddress = response["from"]

					PrintLine("Respone ----------------- ")
					pp = pprint.PrettyPrinter(indent=4)

					pp.pprint(response)
					PrintLine("Respone ----------------- ")
					Valid = Valid or ( ( IPAddress != result["from"] ) and ( IPAddress != result["dst_addr"] ) )

					if IPAddress != LastIPAddress:
						
						IPAddressDetails = IPCache.GetIPInformation( IPAddress )

						if IPAddressDetails["ASN"].isdigit():
							if not ( IPAddressDetails["ASN"] in [ AS["ASN"] for AS in ASPath ] ):
								ASPath.append( { "ASN": IPAddressDetails["ASN"], "Holder": IPAddressDetails["Holder"] } )

						Cols = []

						Cols.append( result["prb_id"] )

						# traceroute complete?
						if result["dst_addr"] == IPAddress:
							TracerouteCompleted = True
							Cols.append( "{:<5}".format("To") )
						else:
							Cols.append( " {:2d}. ".format( hop["hop"] ) )

						Cols.append( IPAddress )
						Cols.append( IPAddressDetails["ASN"] )
						Cols.append( IPAddressDetails["Holder"] )
						Cols.append( IPAddressDetails["Prefix"] )
						Cols.append( IPAddressDetails["HostName"] )
						Cols.append( "%.2f" % median(listrtt))
						Cols.append( response["ttl"])
						#Rows.append( Cols )

						LastIPAddress = IPAddress
						
						geo_available = True
						

						try:
							geo = reader.city(IPAddress)
						except:
							geo_available = False


						if (geo_available == False):
							PrintLine("IP: " + IPAddress + " Geo Not Available")
							continue

						else:
							PrintLine("IP: " + IPAddress + " Long: " + str(geo.location.longitude) + " Lat: " + str(geo.location.latitude) )
					
						if(last_latitude == 0 and last_longitude == 0):
							last_latitude = geo.location.latitude
							last_longitude = geo.location.longitude
							last_rtt = median(listrtt)
							Cols.append( 0 )

							last_IPAddress = IPAddress
						else:
							distance = "%d" % distance_on_unit_sphere(last_latitude, last_longitude, geo.location.latitude, geo.location.longitude)
							line = fol.newlinestring(name=''.join(["Path: ", last_IPAddress, "-", IPAddress]),
											   coords=[(geo.location.longitude,geo.location.latitude), (last_longitude,last_latitude)],
											   altitudemode = simplekml.GxAltitudeMode.clampToSeaFloor,
											   extrude = 1,
											   tessellate = 1,
											   visibility = 1
											   )

							rtt = float(median(listrtt)) - float(last_rtt)

							line.description = "Distance: %s km \n" % (distance) + "RTT: " + str(rtt) +" ms"
							line.style.linestyle.color = color_selctor(rtt,int(distance))

							last_rtt = median(listrtt)
							last_latitude = geo.location.latitude
							last_longitude = geo.location.longitude

							Cols.append( distance )
						Rows.append( Cols )

						fol.newpoint(name=''.join([str(result["prb_id"]),"_",str(hop["hop"])]), 
									 description=''.join(["IP Address: ", IPAddress ,"\nPrefix: ",IPAddressDetails["Prefix"], "\nASN: ", IPAddressDetails["ASN"], "\nHostname: ", IPAddressDetails["HostName"], "\nHolder: ",IPAddressDetails["Holder"]]), 
									 coords=[(geo.location.longitude,geo.location.latitude)]
									 )
						
		else:
			ProbesWithErrors.append( result["prb_id"] )
			break

	if not result["prb_id"] in ProbesWithErrors:
		if Valid:
			if not TracerouteCompleted:
				IncompleteProbes.append( result["prb_id"] )

			if ASPath != []:
				if TracerouteCompleted or AlsoIncludeIncompletePaths:
					ValidProbesCount = ValidProbesCount + 1
					ASPaths.append( ASPath )
		else:
			InvalidProbes.append( result["prb_id"] )

	
	sys.stdout.write("\rProcessed probes: %d valid, %d with errors, %d incomplete paths" % ( ValidProbesCount, len(ProbesWithErrors), len(IncompleteProbes) ) )
	sys.stdout.flush()


sys.stdout.write("\r")
PrintLine("")




# ------------------------------------------------------------------

ColsMaxLen = []
for Col in zip(*Rows):
	ColsMaxLen.append( max( len( str(Val) ) for Val in Col ) )

pp = pprint.PrettyPrinter(indent=4)

pp.pprint(ColsMaxLen)

LastProbeID = 0
LastASN = ""
kl = {}

pp = pprint.PrettyPrinter(indent=4)

pp.pprint(Rows)

for R in Rows:
	if R[0] != LastProbeID:
		if LastProbeID != 0:
			if LastProbeID in ProbesWithErrors:
				PrintLine("")
				PrintLine("  With errors")
			else:
				if LastProbeID in InvalidProbes:
					PrintLine("")
					PrintLine("  Invalid")
				else:
					if LastProbeID in IncompleteProbes:
						PrintLine("")
						PrintLine("  Incomplete")
			PrintLine("")

		LastProbeID = R[0]

		LastASN = ""
		kl[LastProbeID] = ""
		PrintLine( "Probe %s" % LastProbeID )
		kl[LastProbeID] += "Probe %s" % LastProbeID + "\n"
		PrintLine( "" )
		kl[LastProbeID] += "\n"

	if R[3] != "unknown":
		if R[3] != LastASN:
			if LastASN != "":
				PrintLine("")
				kl[LastProbeID] += "\n"

			if R[4] != "":
				PrintLine( "  ASN %s - %s" % ( R[3], R[4] ) )
				kl[LastProbeID] += "  ASN %s - %s" % ( R[3], R[4] ) + "\n"
			else:
				PrintLine( "  ASN %s" % R[3] )
				kl[LastProbeID] += "  ASN %s" % R[3] + "\n"

		LastASN = R[3]

	PrintNoNewLine( "    %s" % R[1] )					# hop n.
	kl[LastProbeID] += "    %s" % R[1]
	PrintNoNewLine( ("{: >%d}" % ColsMaxLen[2]).format( R[2] ) )		# IP
	kl[LastProbeID] += ("{: >%d}" % ColsMaxLen[2]).format( R[2] )

	if R[5] != "":
		PrintNoNewLine( (" - {: >%d}" % ColsMaxLen[5]).format( R[5] ) )	# Prefix
		kl[LastProbeID] +=  (" - {: >%d}" % ColsMaxLen[5]).format( R[5] )
	if len(R) >=8 and R[7] != "":
		PrintNoNewLine( (" - {: >%d} ms" % ColsMaxLen[7]).format( float(R[7]) ) )	# RTT
		kl[LastProbeID] += (" - {: >%d} ms" % ColsMaxLen[7]).format( float(R[7]) )
	if len(R) >=10 and R[9] != "":
		PrintNoNewLine( (" - Distance {: >%d} km" % ColsMaxLen[9]).format( R[9] ) )	# Distance
		kl[LastProbeID] += (" - Distance {: >%d} km" % ColsMaxLen[9]).format( R[9] )
	if len(R) >=9 and R[8] != "":
		PrintNoNewLine( (" - TTL {: >%d}" % ColsMaxLen[8]).format( R[8] ) )	# TTL
		kl[LastProbeID] += (" - TTL {: >%d}" % ColsMaxLen[8]).format( R[8] )
	if R[6] != "unknown" and R[6] != "":
		PrintLine( ", %s" % R[6] )					# Hostname
		kl[LastProbeID] += ", %s" % R[6] + "\n"
	else:
		PrintLine("")
		kl[LastProbeID] += "\n"



PrintLine ("Meine Ausgabe\n ----------------")
pp.pprint(kl)
PrintLine ("Meine Ausgabe\n ----------------")

PrintLine("")


if len(IncompleteProbes) > 0:
	PrintLine("Valid probes: %s - %s incomplete (%s)" % ( ValidProbesCount, len(IncompleteProbes), ", ".join(map(str,IncompleteProbes)) ) )
else:
	PrintLine("Valid probes: %s" % ValidProbesCount)
PrintLine("")

if len(InvalidProbes) > 0:
	PrintLine("Invalid probes: %s (%s)" % ( len(InvalidProbes), ", ".join(map(str,InvalidProbes)) ) )
	PrintLine("")
if len(ProbesWithErrors) > 0:
	PrintLine("Probes with errors: %s (%s)" % ( len(ProbesWithErrors), ", ".join(map(str,ProbesWithErrors)) ) )
	PrintLine("")

# ------------------------------------------------------------------
PrintLine("Considering the last %d ASes for each path, this is the number of probes which reach the target through them:" %ASPathRadiusFromTarget )

SelectedASPaths = [ ASPath[-ASPathRadiusFromTarget:] for ASPath in ASPaths ]
DistinctASPaths = []
for ASPath in SelectedASPaths:
	if not ASPath in DistinctASPaths:
		DistinctASPaths.append( ASPath )

Rows = []
LastRowID = 0
for ASPath in DistinctASPaths:
	LastRowID = LastRowID + 1

	for AS in ASPath:
		Cols = []
		Cols.append( LastRowID )
		Cols.append( "%d probes" % SelectedASPaths.count(ASPath) )
		Cols.append( AS["ASN"] )
		Cols.append( AS["Holder"] )
		Rows.append( Cols )

ColsMaxLen = []
for Col in zip(*Rows):
        ColsMaxLen.append( max( len(str(Val)) for Val in Col ) )

LastRowID = 0
for R in Rows:
	if R[0] != LastRowID:
		PrintLine("")
		PrintNoNewLine( ("{: >%d}: " % ColsMaxLen[1]).format(R[1]) )
		LastRowID = R[0]
	else:
		PrintNoNewLine( ("{: >%d}  " % ColsMaxLen[1]).format(" ") )

	PrintNoNewLine( ("{: >%d}, " % ColsMaxLen[2]).format(R[2] ) )
	PrintLine( R[3] )

PrintLine("")

# ------------------------------------------------------------------

PrintLine(kml.allcontainers)
for b in kml.allcontainers:
	b.description = kl[int(b.name)]
	PrintLine(b.description)


kml.save(KML_FILE)

PrintLine(''.join(["KML File writen to: ", KML_FILE]))

