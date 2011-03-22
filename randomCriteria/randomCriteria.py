import os
import sys
import getopt
import subprocess
import random

import PyXMCDA

from optparse import OptionParser


###
def main(argv=None):
	if argv is None:
		argv = sys.argv
	
	parser = OptionParser()
	
	parser.add_option("-i", "--in", dest="in_dir")
	parser.add_option("-o", "--out", dest="out_dir")
	
	(options, args) = parser.parse_args(argv[1:])
	
	in_dir = options.in_dir
	out_dir = options.out_dir
	
	# Initialising a list of dictionaries for the preferences
	prefDir = {}
	critType = {}
	lowerBound = {}
	upperBound = {}
	levelNumber = {}
	thresholds = {}
	
	# Creating a list for error messages
	errorList = []
	
	# If some mandatory input files are missing
	if not os.path.isfile (in_dir+"/nbCriteria.xml") and not os.path.isfile (in_dir+"/criteriaNames.xml") :
		errorList.append("No parameter has been provided. You should provide a number of criteria (using nbCriteria.xml file) or a list of criteria names (using criteriaNames.xml file).")
	
	else :
		
		# User provides a list of criteria names
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
			
		# User provides a number of criteria
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
	
		# We check if a seed is provided for the random generation
		if os.path.isfile (in_dir+"/seed.xml") :
			xmltree_seed = PyXMCDA.parseValidate(in_dir+"/seed.xml")
			if xmltree_seed == None :
				errorList.append ("seed file can't be validated.")
			else :
				seed = PyXMCDA.getParameterByName (xmltree_seed, "seed")
				if not isinstance(seed,int) :
					errorList.append ("seed value should be a strictly positive integer")
				else :
					if seed <= 0 :
						errorList.append ("seed should be a strictly positive integer")
					else:
						# We initialize the random generator
						random.seed(seed)
		
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
		
		# We check if a numberOfLevels parameter has been provided
		if os.path.isfile (in_dir+"/numberOfLevels.xml") :
			xmltree_levelNumber = PyXMCDA.parseValidate(in_dir+"/numberOfLevels.xml")
			if xmltree_levelNumber == None :
				errorList.append ("numberOfLevels file can't be validated.")
			else :
				levelNumber = PyXMCDA.getNamedParametersByName (xmltree_levelNumber, "numberOfLevels")
				if not levelNumber :
					errorList.append("No number of levels found. Is your numberOfLevels file correct ?")
	
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
			
			# Opening qualitative or quantitative tag
			if critType.has_key (crit) and critType[crit] == "qualitative" :
				fileCrit.write ("\t\t\t<qualitative>\n")
				varBoundType = "integer"
				if levelNumber.has_key (crit) :
					numberOfLevels = levelNumber[crit]
					valLB = 1
					valUB = numberOfLevels
				else :
					numberOfLevels = 10
					valLB = 1
					valUB = 10
			else :
				# By default, a criterion is quantitative
				fileCrit.write ("\t\t\t<quantitative>\n")
				varBoundType = "real"
				if lowerBound.has_key (crit) :
					valLB = lowerBound[crit]
				else :
					valLB = 0.0
				if upperBound.has_key (crit) :
					valUB = upperBound[crit]
				else :
					valUB = 100.0
			
			# Preference direction information	
			if prefDir.has_key (crit) and prefDir[crit] == "min" :
				fileCrit.write ("\t\t\t\t<preferenceDirection>min</preferenceDirection>\n")
			else :
				# By default, the preference direction is "max"
				fileCrit.write ("\t\t\t\t<preferenceDirection>max</preferenceDirection>\n")
			
			if critType.has_key (crit) and critType[crit] == "qualitative" :
				for nb in range (numberOfLevels) :
					fileCrit.write ("\t\t\t\t<rankedLabel><label>"+str(nb+1)+"</label><rank>"+str(nb+1)+"</rank></rankedLabel>\n")
			
			else :
		
				# Writing minimum tag for the lower bound
				fileCrit.write ("\t\t\t\t<minimum><"+varBoundType+">")
			
				if lowerBound.has_key (crit) :
					valLB = lowerBound[crit]
				
				fileCrit.write (str(valLB)+"</"+varBoundType+"></minimum>\n")
				
				# Writing maximum tag for the upper bound
				fileCrit.write ("\t\t\t\t<maximum><"+varBoundType+">")
					
				fileCrit.write (str(valUB)+"</"+varBoundType+"></maximum>\n")
			
			# Closing quantitative or qualitative tag		
			if critType.has_key (crit) and critType[crit] == "qualitative" :
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
					
					if critType.has_key (crit) and critType[crit] == "qualitative" :
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

if __name__ == "__main__":
    sys.exit(main())
