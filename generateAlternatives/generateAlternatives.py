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
if not os.path.isfile (in_dir+"/nbAlternatives.xml") and not os.path.isfile (in_dir+"/alternativesNames.xml") :
	errorList.append("No parameter has been provided. You should provide a number of alternatives (using nbAlternatives.xml file) or a list of alternatives names (using alternativesNames.xml file).")

else :
	
	# User provide a list of alternatives names
	if os.path.isfile (in_dir+"/alternativesNames.xml") :
	
		# We parse the input file
		xmltree_AltNames = PyXMCDA.parseValidate(in_dir+"/alternativesNames.xml")
		if xmltree_AltNames == None :
			errorList.append ("alternativesNames file can't be validated.")
		
		else :
			# We record the alternatives names in altNames
			altNames = PyXMCDA.getParametersByName (xmltree_AltNames, "alternativesNames")
			
			if not altNames :
				errorList.append ("No alternative name has been found in alternativesNames file. Is your file correct ?")
		
	# user provide a number of alternatives
	else :
	
		# We parse the input file
		xmltree_nbAlt = PyXMCDA.parseValidate(in_dir+"/nbAlternatives.xml")
		if xmltree_nbAlt == None :
			errorList.append ("nbAlternatives file can't be validated.")
				
		else :
			
			nbAlt = PyXMCDA.getParameterByName (xmltree_nbAlt, "nbAlternatives")
				
			# We check the validity of the parameter
			if not nbAlt :
				errorList.append ("nbAlternatives parameter not provided. It should be a strict positive integer.")
			if not errorList and not isinstance(nbAlt,int) :
				errorList.append ("nbAlternatives value should be a strict positive integer.")
			if not errorList and nbAlt <= 0 :
				errorList.append ("nbAlternatives value should be a scrict positive integer.")
				
			# We check if a prefix parameter has been provided
			if not errorList :
				if os.path.isfile (in_dir+"/alternativesPrefix.xml") :
					xmltree_AltPrefix = PyXMCDA.parseValidate(in_dir+"/alternativesPrefix.xml")
					if xmltree_AltPrefix == None :
						errorList.append ("alternativesPrefix file can't be validated.")
					else :
						altPrefix = PyXMCDA.getParameterByName (xmltree_AltPrefix, "alternativesPrefix")
						
						# We check the validity of the parameter
						if not isinstance(altPrefix,str) :
							errorList.append ("alternativesPrefix parameter should be a label")
				
				else :
					# If no prefix has been provided, the alternatives will be called a1, a2, ...
					altPrefix = "a"
					
			if not errorList :
			
				# We create the altNames list
				altNames = []
				for nb in range(nbAlt) :
					altNames.append(altPrefix+str(nb+1))
				
			
if not errorList :

	# We create the alternatives.xml file
	fileAlt = open(out_dir+"/alternatives.xml", 'w')
	PyXMCDA.writeHeader (fileAlt)
	fileAlt.write ("<alternatives>\n")
	
	for alt in altNames :
		fileAlt.write ("\t<alternative id='" + alt + "'>\n\t\t<active>true</active>\n\t</alternative>\n")

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
	

