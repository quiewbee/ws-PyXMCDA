import os
import sys
import getopt
import subprocess

import PyXMCDA
import lib_ampl_WAT_reverse

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
	if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/alternativesComparisons.xml") or not os.path.isfile (in_dir+"/performanceTable.xml") :
		errorList.append("Some input files are missing")
	
	else :
		
		maxWeight = 0
		
		if os.path.isfile (in_dir+"/maxWeight.xml") :
			xmltree_maxWeight = PyXMCDA.parseValidate(in_dir+"/maxWeight.xml")
			if xmltree_maxWeight == None :
				errorList.append ("maxWeight file can't be validated.")
			else :
				maxWeight = PyXMCDA.getParameterByName (xmltree_maxWeight, "maxWeight")
				if not isinstance(maxWeight,int) :
					errorList.append ("maxWeight value should be a strictly positive integer")
				else :
					if maxWeight <= 0 :
						errorList.append ("maxWeightvalue should be a strictly positive integer")
			
		xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
		xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
		xmltree_altComparisons = PyXMCDA.parseValidate(in_dir+"/alternativesComparisons.xml")
		xmltree_perfTable = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
		
		if xmltree_alternatives == None :
			errorList.append("The alternatives file can't be validated.")
		if xmltree_criteria == None :
			errorList.append("The criteria file can't be validated.")
		if xmltree_perfTable == None :
			errorList.append("The performance table file can't be validated.")
#		if xmltree_altComparisons == None :
#			errorList.append("The alternatives comparisons file can't be validated.")
	
		if not errorList :
		
			alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
			criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
			perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
			thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
			altComparisons = PyXMCDA.getAlternativesComparisons (xmltree_altComparisons, alternativesId)
			
			criComparisons = {}
			if os.path.isfile (in_dir+"/criteriaComparisons.xml") :
				xmltree_criComparisons = PyXMCDA.parseValidate(in_dir+"/criteriaComparisons.xml")
				if xmltree_criComparisons == None :
					errorList.append ("criteriaComparisons file can't be validated")
				else :
					criComparisons = PyXMCDA.getCriteriaComparisons (xmltree_criComparisons, criteriaId)
			
			criLB = {}
			if os.path.isfile (in_dir+"/criteriaLowerBounds.xml") :
				xmltree_criLB = PyXMCDA.parseValidate(in_dir+"/criteriaLowerBounds.xml")
				if xmltree_criLB == None :
					errorList.append ("criteriaLowerBounds file can't be validated")
				else :
					criLB = PyXMCDA.getCriterionValue (xmltree_criLB, criteriaId)
					
			criUB = {}
			if os.path.isfile (in_dir+"/criteriaUpperBounds.xml") :
				xmltree_criUB = PyXMCDA.parseValidate(in_dir+"/criteriaUpperBounds.xml")
				if xmltree_criUB == None :
					errorList.append ("criteriaUpperBounds file can't be validated")
				else :
					criUB = PyXMCDA.getCriterionValue (xmltree_criUB, criteriaId)
			
			criIndLB = {}
			criIndUB = {}
			criPreLB = {}
			criPreUB = {}
			if os.path.isfile (in_dir+"/criteriaThresholdsBounds.xml") :
				xmltree_criThreBounds = PyXMCDA.parseValidate(in_dir+"/criteriaThresholdsBounds.xml")
				if xmltree_criThreBounds == None :
					errorList.append ("criteriaThresholdsBounds file can't be validated")
				else :
					criIndLB = PyXMCDA.getCriterionValue (xmltree_criThreBounds, criteriaId, "indLowerBounds")
					criIndUB = PyXMCDA.getCriterionValue (xmltree_criThreBounds, criteriaId, "indUpperBounds")
					criPreLB = PyXMCDA.getCriterionValue (xmltree_criThreBounds, criteriaId, "prefLowerBounds")
					criPreUB = PyXMCDA.getCriterionValue (xmltree_criThreBounds, criteriaId, "prefUpperBounds")

			if not alternativesId :
				errorList.append("No alternatives found. Is your alternatives file correct ?")
			if not criteriaId :
				errorList.append("No criteria found. Is your criteria file correct ?")
			if not perfTable :
				errorList.append("No performance table found. Is your performance table file correct ?")
			if not thresholds :
				errorList.append("Problem when retrieving the thresholds. The thresholds need to be constant.")
		
	if not errorList :
	
		p = subprocess.Popen(['ampl'], shell=False, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		
		# We write in the pipe the first part of the ampl file
		file = open ("ampl_WAT_model.txt", 'r')
		p.stdin.write(file.read()) 
		p.stdin.write("\n")
		
		lib_ampl_WAT_reverse.create_ampl_reverse_data (p.stdin, alternativesId, criteriaId, perfTable, altComparisons, thresholds, maxWeight, criComparisons, criLB, criUB, criIndLB, criIndUB, criPreLB, criPreUB)
		
		file = open ("ampl_WAT_solve.txt", 'r')
		p.stdin.write(file.read())
		p.stdin.write("\n")
		p.stdin.flush()
		
		# Calling CPlex for solving MILP
		output,stderr = p.communicate()
		status = p.returncode
		
		#print output
		
		# We check the correct resolution
		if status == 0  and not stderr :
			
			if PyXMCDA.getStringPart(output, "nolicense") == "" :
			
				if PyXMCDA.getStringPart(output, "infeasible") != "infeasible" :
							
					# We create the criteriaWeights file
					fileWeights = open(out_dir+"/criteriaWeights.xml", 'w')
					PyXMCDA.writeHeader (fileWeights)
					
					# We write some information about the generated file
					fileWeights.write ("\t<projectReference>\n\t\t<title>Condorcet robust weights and thresholds elicitation</title>\n\t\t<version>"+VERSION+"</version>\n\t\t<author>ws_PyXMCDA suite (TV)</author>\n\t</projectReference>\n\n")
	
					fileWeights.write (PyXMCDA.getStringPart(output, "criteriaValues"))	
					PyXMCDA.writeFooter(fileWeights)
					fileWeights.close()
					
					# We create the criteriaThresholds file
					fileThresholds = open(out_dir+"/criteriaThresholds.xml",'w')
					PyXMCDA.writeHeader (fileThresholds)
					fileThresholds.write ("\t<projectReference>\n\t\t<title>Condorcet robust weights and thresholds elicitation</title>\n\t\t<version>"+VERSION+"</version>\n\t\t<author>ws_PyXMCDA suite (TV)</author>\n\t</projectReference>\n\n")
					fileThresholds.write (PyXMCDA.getStringPart(output, "criteriaThresholds"))	
					PyXMCDA.writeFooter(fileThresholds)
					fileThresholds.close()
					
					logList.append("Execution ok")
					logList.append(PyXMCDA.getStringPart(output, "slackSum")) 
					logList.append(PyXMCDA.getCleanedStringPart(output, "CPLexInfos"))
					
				else :
					errorList.append ("Infeasible problem.")
					errorList.append (PyXMCDA.getStringPart(output, "CPLexInfos"))
								
			else :
				errorList.append ("No license available.")
				errorList.append (PyXMCDA.getStringPart(output, "CPLexInfos"))
			
		else :
			errorList.append ("CPlex is unable to solve the problem.")
			errorList.append ("CPlex returned status : " + str(status))
			errorList.append (stderr)
		
	
	
	# Creating log and error file, messages.xml
	fileMessages = open(out_dir+"/messages.xml", 'w')
	PyXMCDA.writeHeader (fileMessages)
	
	if not errorList :
		PyXMCDA.writeLogMessages (fileMessages, logList)
	else :
		PyXMCDA.writeErrorMessages (fileMessages, errorList)
		
	PyXMCDA.writeFooter(fileMessages)
	fileMessages.close()

if __name__ == "__main__":
    sys.exit(main())
