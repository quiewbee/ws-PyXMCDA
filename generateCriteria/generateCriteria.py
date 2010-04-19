import os
import sys
import getopt
import subprocess

import PyXMCDA

from optparse import OptionParser


###


parser = OptionParser()

parser.add_option("-i", "--in", dest="in_dir")
parser.add_option("-o", "--out", dest="out_dir")

(options, args) = parser.parse_args()

in_dir = options.in_dir
out_dir = options.out_dir

# Creating a list for error messages
errorList = []

# If some mandatory input files are missing
if not os.path.isfile (in_dir+"/nbCriteria.xml") :
	errorList.append("nbCriteria file missing.")

else :
	
	# We parse the input file
	xmltree_nbCrit = PyXMCDA.parseValidate(in_dir+"/nbCriteria.xml")
	if xmltree_nbCrit == None :
		errorList.append ("nbCriteria file can't be validated.")
			
	else :
		
		nbCrit = PyXMCDA.getParameterByName (xmltree_nbCrit, "nbCriteria")
		critSuffix = PyXMCDA.getParameterByName (xmltree_nbCrit, "criteriaSuffix")
			
		# We check the validity of the parameters
		if not nbCrit :
			errorList.append ("nbCriteria parameter not provided")
		if not errorList and not isinstance(nbCrit,int) :
			errorList.append ("nbCriteria value should be an integer")
		if not errorList and nbCrit <= 0 :
			errorList.append ("nbCriteria value should be a scrit positive integer")

		if critSuffix and not isinstance(critSuffix,str) :
			errorList.append ("criteriaSuffix parameter should be a label")
			
if not errorList :

	# We create an criteria.xml file with nbCrit criteria
	
	# If no suffix has been provided, the criteria will be called g1, g2, ...
	# Else, it will be called critSuffix1, critSuffix2, ...
	
	if not critSuffix :
		critSuffix = "g"
	
	# We create the criteria file
	fileCrit = open(out_dir+"/criteria.xml", 'w')
	PyXMCDA.writeHeader (fileCrit)
	fileCrit.write ("<criteria>\n")
	
	for nb in range(nbCrit) :
		fileCrit.write ("\t<criterion id='" + critSuffix + str(nb+1) + "'>\n\t\t<active>true</active>\n\t</criterion>\n")

	fileCrit.write ("</criteria>\n")
			
	PyXMCDA.writeFooter(fileCrit)
	fileCrit.close()

# Creating log and error file, messages.xml
fileMessages = open(out_dir+"/messages.xml", 'w')
PyXMCDA.writeHeader (fileMessages)

if not errorList :

	PyXMCDA.writeLogMessages (fileMessages, ["Execution ok"])
else :
	PyXMCDA.writeErrorMessages (fileMessages, errorList)
	
PyXMCDA.writeFooter(fileMessages)
fileMessages.close()
	

