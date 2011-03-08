import os
import sys
import getopt
import subprocess

import PyXMCDA

from optparse import OptionParser

VERSION = "1.0.0"

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
	
	# Creating lists for error and log messages
	errorList = []
	logList = []
	
	# If some mandatory input files are missing
	if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/performanceTable.xml"):
		errorList.append("Some input files are missing")
	
	else:
			
		xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
		xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
		xmltree_perfTable = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
		
		if xmltree_alternatives == None:
			errorList.append("The alternatives file can't be validated.")
		if xmltree_criteria == None:
			errorList.append("The criteria file can't be validated.")
		if xmltree_perfTable == None:
			errorList.append("The performance table file can't be validated.")

		if not errorList:
		
			alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
			criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
			perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
			thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
		
			if not alternativesId:
				errorList.append("No alternatives found. Is your alternatives file correct ?")
			if not criteriaId:
				errorList.append("No criteria found. Is your criteria file correct ?")
			if not perfTable:
				errorList.append("No performance table found. Is your performance table file correct ?")
		
	if not errorList:
	
		ElemOut = PyXMCDA.getRubisElementaryOutranking (alternativesId, criteriaId, perfTable, thresholds)
		
		# Adding thresholds equals to 0 when they are not defined
		for crit in criteriaId:
			if not thresholds.has_key(crit):
				thresholds[crit] = {}
			if not thresholds[crit].has_key("indifference"):
				thresholds[crit]["indifference"] = 0
			if not thresholds[crit].has_key("preference"):
				thresholds[crit]["preference"] = 0
				
		# Creating the table for min and max thresholds
		thresholdsBounds = {}
		
		for crit in criteriaId:
			thresholdsBounds[crit] = {}
			thresholdsBounds[crit]["ind"] = {}
			thresholdsBounds[crit]["ind"]["min"] = 0.0
			thresholdsBounds[crit]["pre"] = {}
			thresholdsBounds[crit]["pre"]["min"] = 0.0
			
			for alt1 in alternativesId:
				for alt2 in alternativesId:
					if alt1 != alt2:
						if perfTable[alt1][crit] < perfTable[alt2][crit]:
							if ElemOut[alt1][alt2][crit] == 1:
								if perfTable[alt2][crit] - perfTable[alt1][crit] > thresholdsBounds[crit]["ind"]["min"]:
									thresholdsBounds[crit]["ind"]["min"] = perfTable[alt2][crit] - perfTable[alt1][crit]
								if perfTable[alt2][crit] - perfTable[alt1][crit] > thresholdsBounds[crit]["pre"]["min"]:
									thresholdsBounds[crit]["pre"]["min"] = perfTable[alt2][crit] - perfTable[alt1][crit]
							elif ElemOut[alt1][alt2][crit] == 0.5:
								if perfTable[alt2][crit] - perfTable[alt1][crit] > thresholdsBounds[crit]["pre"]["min"]:
									thresholdsBounds[crit]["pre"]["min"] = perfTable[alt2][crit] - perfTable[alt1][crit]
								if not thresholdsBounds[crit]["ind"].has_key("max") or perfTable[alt2][crit] - perfTable[alt1][crit] < thresholdsBounds[crit]["ind"]["max"]:
									thresholdsBounds[crit]["ind"]["max"] = perfTable[alt2][crit] - perfTable[alt1][crit]
							else:
								if not thresholdsBounds[crit]["ind"].has_key("max") or perfTable[alt2][crit] - perfTable[alt1][crit] < thresholdsBounds[crit]["ind"]["max"]:
									thresholdsBounds[crit]["ind"]["max"] = perfTable[alt2][crit] - perfTable[alt1][crit]
								if not thresholdsBounds[crit]["pre"].has_key("max") or perfTable[alt2][crit] - perfTable[alt1][crit] < thresholdsBounds[crit]["pre"]["max"]:
									thresholdsBounds[crit]["pre"]["max"] = perfTable[alt2][crit] - perfTable[alt1][crit]

		# Creating criteriaTresholdsBounds file
		fileThresholds = open(out_dir+"/criteriaTresholdsBounds.xml",'w')
		PyXMCDA.writeHeader(fileThresholds)
		
		# We write some information about the generated file
		fileThresholds.write ("\t<projectReference>\n\t\t<title>Thresholds Sensitivity Analysis (TSA)</title>\n\t\t<version>"+VERSION+"</version>\n\t\t<author>ws_PyXMCDA suite (TV)</author>\n\t</projectReference>\n\n")
	
		# Writing the indLowerBounds
		fileThresholds.write("<criteriaValues mcdaConcept='indLowerBounds'>\n")
		for crit in criteriaId:
			if thresholdsBounds[crit]["ind"].has_key("min"):
				fileThresholds.write("<criterionValue><criterionID>"+crit+"</criterionID><value><real>"+str(thresholdsBounds[crit]["ind"]["min"])+"</real></value></criterionValue>\n")
		fileThresholds.write("</criteriaValues>\n\n")
		
		# Writing the indUpperBounds
		fileThresholds.write("<criteriaValues mcdaConcept='indUpperBounds'>\n")
		for crit in criteriaId:
			if thresholdsBounds[crit]["ind"].has_key("max"):
				fileThresholds.write("<criterionValue><criterionID>"+crit+"</criterionID><value><real>"+str(thresholdsBounds[crit]["ind"]["max"])+"</real></value></criterionValue>\n")
		fileThresholds.write("</criteriaValues>\n\n")
		
		# Writing the indLowerBounds
		fileThresholds.write("<criteriaValues mcdaConcept='prefLowerBounds'>\n")
		for crit in criteriaId:
			if thresholdsBounds[crit]["pre"].has_key("min"):
				fileThresholds.write("<criterionValue><criterionID>"+crit+"</criterionID><value><real>"+str(thresholdsBounds[crit]["pre"]["min"])+"</real></value></criterionValue>\n")
		fileThresholds.write("</criteriaValues>\n\n")
		
		# Writing the preUpperBounds
		fileThresholds.write("<criteriaValues mcdaConcept='prefUpperBounds'>\n")
		for crit in criteriaId:
			if thresholdsBounds[crit]["pre"].has_key("max"):
				fileThresholds.write("<criterionValue><criterionID>"+crit+"</criterionID><value><real>"+str(thresholdsBounds[crit]["pre"]["max"])+"</real></value></criterionValue>\n")
		fileThresholds.write("</criteriaValues>\n\n")
		
		PyXMCDA.writeFooter(fileThresholds)
		fileThresholds.close()
			
	# Creating log and error file, messages.xml
	fileMessages = open(out_dir+"/messages.xml", 'w')
	PyXMCDA.writeHeader (fileMessages)
	
	if not errorList:
		logList.append("Execution ok")
		PyXMCDA.writeLogMessages (fileMessages, logList)
	else:
		PyXMCDA.writeErrorMessages (fileMessages, errorList)
		
	PyXMCDA.writeFooter(fileMessages)
	fileMessages.close()

if __name__ == "__main__":
    sys.exit(main())
