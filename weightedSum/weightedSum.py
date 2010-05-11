import os
import sys
import getopt
import subprocess

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
	
	# Creating a list for error messages
	errorList = []
	
	# If some mandatory input files are missing
	if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/criteriaWeights.xml") or not os.path.isfile (in_dir+"/performanceTable.xml") :
		errorList.append("Some input files are missing")
	
	else :
		
		# We parse all the mandatory input files
		xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
		xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
		xmltree_weights = PyXMCDA.parseValidate(in_dir+"/criteriaWeights.xml")
		xmltree_perfTable = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
		
		# We check if all madatory input files are valid
		if xmltree_alternatives == None :
			errorList.append("The alternatives file can't be validated.")
		if xmltree_criteria == None :
			errorList.append("The criteria file can't be validated.")
		if xmltree_perfTable == None :
			errorList.append("The performance table file can't be validated.")
		if xmltree_weights == None :
			errorList.append("The criteria weights file can't be validated.")
		
		if not errorList :
		
			alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
			criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
			perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
			thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
			weights = PyXMCDA.getCriterionValue (xmltree_weights, criteriaId)
		
			if not alternativesId :
				errorList.append("No alternatives found. Is your alternatives file correct ?")
			if not criteriaId :
				errorList.append("No criteria found. Is your criteria file correct ?")
			if not perfTable :
				errorList.append("No performance table found. Is your performance table file correct ?")
			if not weights :
				errorList.append("No weights found. Is your weights file correct ?")
	
	
	if not errorList :
	
		# We check if a criterion weight is defined for all the active criteria
		for crit in criteriaId :
			if not weights.has_key(crit) :
				errorList.append("There is no defined weight for criterion "+crit+".")
		
		
	if not errorList :
		
		# We compute the weighted sum for all the active alternatives
		fileAltValues = open(out_dir+"/alternativesValues.xml", 'w')
		PyXMCDA.writeHeader (fileAltValues)
		
		fileAltValues.write ("<alternativesValues>\n")
		
		for alt in alternativesId :
		
			fileAltValues.write("<alternativeValue><alternativeID>"+alt+"</alternativeID><value>")
			sum = 0.0
			errorAlt = False
	
			for crit in criteriaId :
				
				try :
					sum = sum + weights[crit] * perfTable[alt][crit]
				except :
					errorList.append("No evaluation found for alternative "+alt+" on criterion "+crit+" in the performance table.")
					errorAlt = True
		
			if not errorAlt :	
				fileAltValues.write ("<real>"+str(sum)+"</real></value></alternativeValue>\n")
			else :
				fileAltValues.write ("<NA>not available</NA></value></alternativeValue>\n")
			
		fileAltValues.write ("</alternativesValues>")
		
		PyXMCDA.writeFooter(fileAltValues)
		fileAltValues.close()
	
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
