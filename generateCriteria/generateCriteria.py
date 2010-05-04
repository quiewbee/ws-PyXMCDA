import os
import sys
import getopt
import subprocess

import random

import PyXMCDA

from optparse import OptionParser


###


parser = OptionParser()

parser.add_option("-i", "--in", dest="in_dir")
parser.add_option("-o", "--out", dest="out_dir")

(options, args) = parser.parse_args()

in_dir = options.in_dir
out_dir = options.out_dir

# Initialising a list of dictionaries for the preferences
prefDir = {}
critType = {}
lowerBound = {}
upperBound = {}

# Creating a list for error messages
errorList = []

# If some mandatory input files are missing
if not os.path.isfile (in_dir+"/nbCriteria.xml") and not os.path.isfile (in_dir+"/criteriaNames.xml") :
	errorList.append("No parameter has been provided. You should provide a number of criteria (using nbCriteria.xml file) or a list of criteria names (using criteriaNames.xml file).")

else :
	
	# User provide a list of criteria names
	if os.path.isfile (in_dir+"/criteriaNames.xml") :
	
		# We parse the input file
		xmltree_CritNames = PyXMCDA.parseValidate(in_dir+"/criteriaNames.xml")
		if xmltree_CritNames == None :
			errorList.append ("criteriaNames file can't be validated.")
		
		else :
			# We record the criteria names in critNames
			critNames = PyXMCDA.getParametersByName (xmltree_CritNames, "criteriaNames")
			
			if not critNames :
				errorList.append ("No criterion name has been found in criteriaNames file. Is your file correct ?")
		
	# user provide a number of criteria
	else :
	
		# We parse the input file
		xmltree_nbCrit = PyXMCDA.parseValidate(in_dir+"/nbCriteria.xml")
		if xmltree_nbCrit == None :
			errorList.append ("nbCriteria file can't be validated.")
				
		else :
			
			nbCrit = PyXMCDA.getParameterByName (xmltree_nbCrit, "nbCriteria")
				
			# We check the validity of the parameter
			if not nbCrit :
				errorList.append ("nbCriteria parameter not provided. It should be a strict positive integer.")
			if not errorList and not isinstance(nbCrit,int) :
				errorList.append ("nbCriteria value should be a strict positive integer.")
			if not errorList and nbCrit <= 0 :
				errorList.append ("nbCriteria value should be a scrict positive integer.")
				
			# We check if a prefix parameter has been provided
			if not errorList :
				if os.path.isfile (in_dir+"/criteriaPrefix.xml") :
					xmltree_CritPrefix = PyXMCDA.parseValidate(in_dir+"/criteriaPrefix.xml")
					if xmltree_CritPrefix == None :
						errorList.append ("criteriaPrefix file can't be validated.")
					else :
						critPrefix = PyXMCDA.getParameterByName (xmltree_CritPrefix, "criteriaPrefix")
						
						# We check the validity of the parameter
						if not isinstance(critPrefix,str) :
							errorList.append ("criteriaPrefix parameter should be a label")
				
				else :
					# If no prefix has been provided, the criteria will be called g1, g2, ...
					critPrefix = "g"
					
			if not errorList :
			
				# We create the critNames list
				critNames = []
				for nb in range(nbCrit) :
					critNames.append(critPrefix+str(nb+1))
				
			
if not errorList :
	
	# We check if a preferenceDirection file has been provided
	if os.path.isfile (in_dir+"/preferenceDirection.xml") :
		xmltree_PrefDir = PyXMCDA.parseValidate(in_dir+"/preferenceDirection.xml")
		if xmltree_PrefDir == None :
			errorList.append ("preferenceDirection file can't be validated.")
		else :
			prefDir = PyXMCDA.getNamedParametersByName (xmltree_PrefDir, "preferenceDirection")
			
			if not prefDir :
				errorList.append("No preference direction found. Is your preferenceDirection file correct ?")

if not errorList :
	
	# We check if a criteriaType file has been provided
	if os.path.isfile (in_dir+"/criteriaType.xml") :
		xmltree_CritType = PyXMCDA.parseValidate(in_dir+"/criteriaType.xml")
		if xmltree_CritType == None :
			errorList.append ("criteriaType file can't be validated.")
		else :
			critType = PyXMCDA.getNamedParametersByName (xmltree_CritType, "criteriaType")
			
			if not critType :
				errorList.append("No criterion type found. Is your criteriaType file correct ?")

if not errorList :
	
	# We check if a lowerBound file has been provided
	if os.path.isfile (in_dir+"/lowerBounds.xml") :
		xmltree_LowerBound = PyXMCDA.parseValidate(in_dir+"/lowerBounds.xml")
		if xmltree_LowerBound == None :
			errorList.append ("lowerBounds file can't be validated.")
		else :
			lowerBound = PyXMCDA.getNamedParametersByName (xmltree_LowerBound, "lowerBounds")
			
			if not lowerBound :
				errorList.append("No lower bound found. Is your lowerBounds file correct ?")
				
if not errorList :
	
	# We check if an upperBound file has been provided
	if os.path.isfile (in_dir+"/upperBounds.xml") :
		xmltree_UpperBound = PyXMCDA.parseValidate(in_dir+"/upperBounds.xml")
		if xmltree_UpperBound == None :
			errorList.append ("upperBounds file can't be validated.")
		else :
			upperBound = PyXMCDA.getNamedParametersByName (xmltree_UpperBound, "upperBounds")
			
			if not upperBound :
				errorList.append("No upper bound found. Is your upperBounds file correct ?")

if not errorList :
	
	# We check if a thresholdsNames file has been provided
	if os.path.isfile (in_dir+"/thresholdsNames.xml") :
		xmltree_Thresholds = PyXMCDA.parseValidate(in_dir+"/thresholdsNames.xml")
		if xmltree_Thresholds == None :
			errorList.append ("thresholdsNames file can't be validated.")
		else :
			thresholds = PyXMCDA.getParametersByName (xmltree_Thresholds, "thresholdsNames")
			
			if not thresholds :
				errorList.append("No threshold name found. Is your thresholdsNames file correct ?")


if not errorList :

	# We create the criteria.xml file
	fileCrit = open(out_dir+"/criteria.xml", 'w')
	PyXMCDA.writeHeader (fileCrit)
	fileCrit.write ("<criteria>\n")
	
	for crit in critNames :
		fileCrit.write ("\t<criterion id='" + crit + "'>\n\t\t<active>true</active>\n\t\t<scale>\n")
		
		# Opening qualitative (ordinal) or quantitative (cardinal) tag
		if critType.has_key (crit) and critType[crit] == "ordinal" :
			fileCrit.write ("\t\t\t<qualitative>\n")
			varBoundType = "integer"
			valLB = 0
			valUB = 10
		else :
			# By default, a criterion is quantitative
			fileCrit.write ("\t\t\t<quantitative>\n")
			varBoundType = "real"
			valLB = 0.0
			valUB = 100.0
		
		# Preference direction information	
		if prefDir.has_key (crit) and prefDir[crit] == "min" :
			fileCrit.write ("\t\t\t\t<preferenceDirection>min</preferenceDirection>\n")
		else :
			# By default, the preference direction is "max"
			fileCrit.write ("\t\t\t\t<preferenceDirection>max</preferenceDirection>\n")
		
		# Writing minimum tag for the lower bound
		fileCrit.write ("\t\t\t\t<minimum><"+varBoundType+">")
		
		if lowerBound.has_key (crit) :
			valLB = lowerBound[crit]
			
		fileCrit.write (str(valLB)+"<"+varBoundType+"></minimum>\n")
		
		# Writing maximum tag for the upper bound
		fileCrit.write ("\t\t\t\t<maximum><"+varBoundType+">")
		
		if upperBound.has_key (crit) :
			valUB = upperBound[crit]
			
		fileCrit.write (str(valUB)+"<"+varBoundType+"></maximum>\n")
		
		# Closing quantitative or qualitative tag		
		if critType.has_key (crit) and critType[crit] == "ordinal" :
			fileCrit.write("\t\t\t</qualitative>\n")
		else :		
			fileCrit.write("\t\t\t</quantitative>\n")
		
		# Closing scale tag
		fileCrit.write("\t\t</scale>\n")
		
				
		# Writing thresholds tag
		if thresholds :
			fileCrit.write ("\t\t<thresholds>\n")
		
		pos = 0
		for thre in thresholds :
			
			if critType.has_key (crit) and critType[crit] == "ordinal" :
				# Writing a random integer
				valThre = random.randint(valLB+pos*(valUB-valLB)/len(thresholds),valLB+(pos+1)*(valUB-valLB)/len(thresholds))
			else :
				# Writing a random real
				valThre = float(random.randint(int((valLB+pos*(valUB-valLB)/len(thresholds)))*100,int((valLB+(pos+1)*(valUB-valLB)/len(thresholds)))*100))/100
				
			fileCrit.write ("\t\t\t<threshold id='"+thre+"'>\n\t\t\t\t<constant><"+varBoundType+">"+str(valThre)+"</"+varBoundType+"></constant>\n")
			
			fileCrit.write ("\t\t\t</threshold>\n")
			
			pos += 1
				
		fileCrit.write ("\t\t</thresholds>\n")
		
		# Closing criterion tag
		fileCrit.write("\t</criterion>\n")

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
	

