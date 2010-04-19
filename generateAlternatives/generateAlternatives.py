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
if not os.path.isfile (in_dir+"/nbAlternatives.xml") :
	errorList.append("nbAlternatives file missing.")

else :
	
	# We parse the input file
	xmltree_nbAlt = PyXMCDA.parseValidate(in_dir+"/nbAlternatives.xml")
	if xmltree_nbAlt == None :
		errorList.append ("nbAlternatives file can't be validated.")
			
	else :
		
		nbAlt = PyXMCDA.getParameterByName (xmltree_nbAlt, "nbAlternatives")
		altSuffix = PyXMCDA.getParameterByName (xmltree_nbAlt, "alternativesSuffix")
			
		# We check the validity of the parameter
		if not nbAlt :
			errorList.append ("nbAlternatives parameter not provided")
		if not errorList and not isinstance(nbAlt,int) :
			errorList.append ("nbAlternatives value should be an integer")
		if not errorList and nbAlt <= 0 :
			errorList.append ("nbAlternatives value should be a scrit positive integer")

		if altSuffix and not isinstance(altSuffix,str) :
			errorList.append ("alternativesSuffix parameter should be a label")
			
if not errorList :

	# We create an alternatives.xml file with nbAlt alternatives
	
	# If no suffix has been provided, the alternatives will be called a1, a2, ...
	# Else, it will be called altSuffix1, altSuffix2, ...
	
	if not altSuffix :
		altSuffix = "a"
	
	# We create the alternatives file
	fileAlt = open(out_dir+"/alternatives.xml", 'w')
	PyXMCDA.writeHeader (fileAlt)
	fileAlt.write ("<alternatives>\n")
	
	for nb in range(nbAlt) :
		fileAlt.write ("\t<alternative id='" + altSuffix + str(nb+1) + "'>\n\t\t<active>true</active>\n\t</alternative>\n")

	fileAlt.write ("</alternatives>\n")
			
	PyXMCDA.writeFooter(fileAlt)
	fileAlt.close()

# Creating log and error file, messages.xml
fileMessages = open(out_dir+"/messages.xml", 'w')
PyXMCDA.writeHeader (fileMessages)

if not errorList :

	PyXMCDA.writeLogMessages (fileMessages, ["Execution ok"])
else :
	PyXMCDA.writeErrorMessages (fileMessages, errorList)
	
PyXMCDA.writeFooter(fileMessages)
fileMessages.close()
	

