# TO DO : Faire verification lorsque le probleme est infaisable et mettre un message d'erreur


import os
import sys
import getopt
import subprocess



import PyXMCDA
import lib_ampl_reverse

from optparse import OptionParser

###

parser = OptionParser()

parser.add_option("-i", "--in", dest="in_dir")
parser.add_option("-o", "--out", dest="out_dir")

(options, args) = parser.parse_args()

in_dir = options.in_dir
out_dir = options.out_dir

# on cree le fichier pour les logs
fileMessages = open(out_dir+"/messages.xml", 'w')
PyXMCDA.writeHeader (fileMessages)

errorList = []

status = 0

if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/alternativesComparisons.xml") or not os.path.isfile (in_dir+"/performanceTable.xml") :
	status = 1
	errorList.append("Some input files are missing")

else :
	
	maxWeight = 0
	
	if os.path.isfile (in_dir+"/maxWeight.xml") :
		xmltree_maxWeight = PyXMCDA.parseValidate(in_dir+"/maxWeight.xml")
		if xmltree_maxWeight == None :
			status = 1
			errorList.append ("maxWeight file can't be validated.")
		else :
			maxWeight = PyXMCDA.getParameterByName (xmltree_maxWeight, "maxWeight")
			if not isinstance(maxWeight,int) :
				errorList.append ("maxWeight value should be a strictly positive integer")
				status = 1
			else :
				if maxWeight <= 0 :
					errorList.append ("maxWeightvalue should be a strictly positive integer")
					status = 1
		
		
	xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
	xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
	xmltree_altComparisons = PyXMCDA.parseValidate(in_dir+"/alternativesComparisons.xml")
	xmltree_perfTable = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
	
	if xmltree_alternatives == None :
		status = 1
		errorList.append("The alternatives file can't be validated.")
	if xmltree_criteria == None :
		status = 1
		errorList.append("The criteria file can't be validated.")
	if xmltree_perfTable == None :
		status = 1
		errorList.append("The performance table file can't be validated.")
	if xmltree_altComparisons == None :
		status = 1
		errorList.append("The alternatives comparisons file can't be validated.")

	if status != 1 :
	
		alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
		criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
		perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
		thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
		altComparisons = PyXMCDA.getAlternativesComparisons (xmltree_altComparisons, alternativesId)
		
		criComparisons = {}
		if os.path.isfile (in_dir+"/criteriaComparisons.xml") :
			xmltree_criComparisons = PyXMCDA.parseValidate(in_dir+"/criteriaComparisons.xml")
			if xmltree_criComparisons == None :
				status = 1
				errorList.append ("criteriaComparisons file can't be validated")
			else :
				criComparisons = PyXMCDA.getCriteriaComparisons (xmltree_criComparisons, criteriaId)
		
		criLB = {}
		if os.path.isfile (in_dir+"/criteriaLowerBounds.xml") :
			xmltree_criLB = PyXMCDA.parseValidate(in_dir+"/criteriaLowerBounds.xml")
			if xmltree_criLB == None :
				status = 1
				errorList.append ("criteriaLowerBounds file can't be validated")
			else :
				criLB = PyXMCDA.getCriterionValue (xmltree_criLB, criteriaId)
				
		criUB = {}
		if os.path.isfile (in_dir+"/criteriaUpperBounds.xml") :
			xmltree_criUB = PyXMCDA.parseValidate(in_dir+"/criteriaUpperBounds.xml")
			if xmltree_criUB == None :
				status = 1
				errorList.append ("criteriaUpperBounds file can't be validated")
			else :
				criUB = PyXMCDA.getCriterionValue (xmltree_criUB, criteriaId)
				
		
		if alternativesId == [] :
			status = 1
			errorList.append("No alternatives found. Is your alternatives file correct ?")
		if criteriaId == [] :
			status = 1
			errorList.append("No criteria found. Is your criteria file correct ?")
		if perfTable == {} :
			status = 1
			errorList.append("No performance table found. Is your performance table file correct ?")
		#if altComparisons == {} :
		#	status = 1
		#	errorList.append("No alternatives comparisons found. Is your file correct ?")
		if thresholds == None :
			status = 1
			errorList.append("Problem when retrieving the thresholds. The thresholds need to be constant.")
	
if status == 1 :
	# Il y a eu des erreurs, on arrete
	PyXMCDA.writeErrorMessages (fileMessages, errorList)
	
else :

	p = subprocess.Popen(['ampl'], shell=False, bufsize=0,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
	
	#On ecrit dans le pipe la premiere partie du fichier ampl
	file = open ("amplRoadef2010_model.txt", 'r')
	p.stdin.write(file.read()) 
	p.stdin.write("\n")
	
	lib_ampl_reverse.create_ampl_reverse_data (p.stdin, alternativesId, criteriaId, perfTable, altComparisons, thresholds, maxWeight, criComparisons, criLB, criUB)
	
	file = open ("amplRoadef2010_solve.txt", 'r')
	p.stdin.write(file.read())
	p.stdin.write("\n")
	p.stdin.flush()
	output,stderr = p.communicate()
	status = p.returncode
	
	#print output
	
	if status == 0 :
	
		# On verifie si la resolution s'est faite
		if not stderr :
		
			if PyXMCDA.getStringPart(output, "nolicense") == "" :
			
				if PyXMCDA.getStringPart(output, "infeasible") != "infeasible" :
							
					# On cree le fichier pour les poids
					fileWeights = open(out_dir+"/criteriaWeights.xml", 'w')
					PyXMCDA.writeHeader (fileWeights)
					fileWeights.write (PyXMCDA.getStringPart(output, "criteriaValues"))	
					PyXMCDA.writeLogMessages (fileMessages, ["Execution ok", PyXMCDA.getStringPart(output, "slackSum"), PyXMCDA.getCleanedStringPart(output, "CPLexInfos")])
					PyXMCDA.writeFooter(fileWeights)
					fileWeights.close()
				
				else :
					PyXMCDA.writeErrorMessages(fileMessages, [PyXMCDA.getStringPart(output, "CPLexInfos")])
			
			else :
				PyXMCDA.writeErrorMessages(fileMessages, ["No license available", PyXMCDA.getStringPart(output, "CPLexInfos")])
			
		else :
		
			PyXMCDA.writeErrorMessages (fileMessages, [stderr])
			
	else :
	
		PyXMCDA.writeErrorMessages (fileMessages, [stderr])
	
PyXMCDA.writeFooter(fileMessages)

fileMessages.close()
