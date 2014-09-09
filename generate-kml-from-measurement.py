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

__version__ = "0.1"



DATA_DIR = ''.join([os.environ['HOME'], "/traceroute_cache"])
KML_FILE = ''.join([os.environ['HOME'], "/output.kml"])

GEOIP_FILE = "/opt/geoip2/GeoLite2-City.mmdb"
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

Rows			= []
ASPaths			= []	# [ [ { "ASN": xxx, "Holder": "xxx" }, ... ] ]
InvalidProbes		= []
ProbesWithErrors	= []
IncompleteProbes	= []
ValidProbesCount	= 0	# only results with one or more IP addresses different from both the source and the target in the middle of the path are considered valid
kml					= simplekml.Kml()
reader				= geoip2.database.Reader(GEOIP_FILE)


for result in data:

	IPAddress = result["from"]
	if IPAddress == "":
		IPAddress = result["src_addr"]

	if IPAddress == "":
		continue

	ASPath = []
	TracerouteCompleted = False
	Valid = False

	response = reader.city(IPAddress)

	#l = []
	#l.append(IPAddress)
	#l.append(response.location.latitude)
	#l.append(response.location.longitude)
	#

	#m = IPAddress + response.location.latitude + response.location.longitude

	#PrintLine(m)
	PrintLine(result["prb_id"])
	IPAddressDetails = IPCache.GetIPInformation( IPAddress )

	#PrintLine(IPAddressDetails)

	doc = kml.newdocument(name=str(result["prb_id"]))

	pnt = doc.newpoint(name=str(result["prb_id"]), 
			 description=''.join(["IP Address: ", IPAddress ,"\nPrefix: ",IPAddressDetails["Prefix"], "\nASN: ", IPAddressDetails["ASN"], "\nHostname: ", IPAddressDetails["HostName"], "\nHolder: ",IPAddressDetails["Holder"]]), 
			 coords=[(response.location.longitude,response.location.latitude)]
			 )

	pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/sunny.png'
	pnt.style.iconstyle.scale = 3

	ASPath.append( { "ASN": IPAddressDetails["ASN"], "Holder": IPAddressDetails["Holder"] } )

	Cols = []

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
	Rows.append( Cols )

	for hop in result["result"]:
		if hop.get("error","") == "":
			LastIPAddress = ""
			for response in hop["result"]:
				if response.get("from","") != "":
					IPAddress = response["from"]

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
						Rows.append( Cols )

						LastIPAddress = IPAddress
						
						geo_available = True

						try:
							response = reader.city(IPAddress)
						except:
							geo_available = False

						if (geo_available == False):
							PrintLine("Geo Not Available")
							continue
					
						if(last_latitude == 0 and last_longitude == 0):
							last_latitude = response.location.latitude
							last_longitude = response.location.longitude
							last_IPAddress = IPAddress
						else:
							doc.newlinestring(name=''.join(["Path: ", last_IPAddress, "-", IPAddress]),
											   coords=[(response.location.longitude,response.location.latitude), (last_longitude,last_latitude)],
											   altitudemode = simplekml.GxAltitudeMode.clampToSeaFloor,
											   extrude = 1,
											   tessellate = 1,
											   visibility = 1
											   )
							
							last_latitude = response.location.latitude
							last_longitude = response.location.longitude

						doc.newpoint(name=''.join([str(result["prb_id"]),"_",str(hop["hop"])]), 
									 description=''.join(["IP Address: ", IPAddress ,"\nPrefix: ",IPAddressDetails["Prefix"], "\nASN: ", IPAddressDetails["ASN"], "\nHostname: ", IPAddressDetails["HostName"], "\nHolder: ",IPAddressDetails["Holder"]]), 
									 coords=[(response.location.longitude,response.location.latitude)]
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

LastProbeID = 0
LastASN = ""

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

		PrintLine( "Probe %s" % LastProbeID )
		PrintLine( "" )

	if R[3] != "unknown":
		if R[3] != LastASN:
			if LastASN != "":
				PrintLine("")

			if R[4] != "":
				PrintLine( "  ASN %s - %s" % ( R[3], R[4] ) )
			else:
				PrintLine( "  ASN %s" % R[3] )

		LastASN = R[3]

	PrintNoNewLine( "    %s" % R[1] )					# hop n.
	PrintNoNewLine( ("{: >%d}" % ColsMaxLen[2]).format( R[2] ) )		# IP
	if R[5] != "":
		PrintNoNewLine( (" - {: >%d}" % ColsMaxLen[5]).format( R[5] ) )	# Prefix
	if R[6] != "unknown" and R[6] != "":
		PrintLine( ", %s" % R[6] )					# Hostname
	else:
		PrintLine("")

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



kml.save(KML_FILE)

PrintLine(''.join(["KML File writen to: ", KML_FILE]))
