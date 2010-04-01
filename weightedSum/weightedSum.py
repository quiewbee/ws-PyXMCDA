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

XMCDA_NS = "http://www.decision-deck.org/2009/XMCDA-2.0.0"

# on cree le fichier pour les logs
fileMessages = open(out_dir+"/messages.xml", 'w')
PyXMCDA.writeHeader (fileMessages)

errorList = []

status = 0

if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/performanceTable.xml") or not os.path.isfile (in_dir+"/criteriaWeights.xml") :
	status = 1
	errorList.append("Some input files are missing")

else :

	xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
	xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
	xmltree_perfTable = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
	xmltree_weights = PyXMCDA.parseValidate(in_dir+"/criteriaWeights.xml")
	
	if xmltree_alternatives == None :
		status = 1
		errorList.append("The alternatives file can't be validated.")
	if xmltree_criteria == None :
		status = 1
		errorList.append("The criteria file can't be validated.")
	if xmltree_perfTable == None :
		status = 1
		errorList.append("The performance table file can't be validated.")
	if xmltree_weights == None :
		status = 1
		errorList.append("The criteriaWeights file can't be validated.")

	if status != 1 :
	
		alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
		criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
		perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
		weights = PyXMCDA.getCriterionValue (xmltree_weights, criteriaId)
	
		if alternativesId == [] :
			status = 1
			errorList.append("No alternatives found. Is your alternatives file correct ?")
		if criteriaId == [] :
			status = 1
			errorList.append("No criteria found. Is your criteria file correct ?")
		if perfTable == [] :
			status = 1
			errorList.append("No performance table found. Is your performance table file correct ?")
		if weights == [] :
			status = 1
			errorList.append("No weights found. Is your weights file correct ?")

if status == 1 :
	# Il y a eu des erreurs, on arrete
	PyXMCDA.write_error_messages (fileMessages, errorList)
	
else :

	#On genere le fichier resultat
	fileAltValues = open(out_dir+"/alternativesValues.xml", 'w')
	PyXMCDA.writeHeader (fileAltValues)
	
	fileAltValues.write ("<alternativesValues>\n")
	
	for alt in alternativesId :
		fileAltValues.write("<alternativeValue><alternativeID>"+alt+"</alternativeID><value><real>")
		sum = 0
		
		for crit in criteriaId :
			sum = sum + weights[crit] * perfTable[alt][crit]
		fileAltValues.write (str(sum))
		fileAltValues.write("</real></value></alternativeValue>\n")
		
	fileAltValues.write ("</alternativesValues>")
	
	PyXMCDA.writeFooter(fileAltValues)
	fileAltValues.close()



	PyXMCDA.writeLogMessages (fileMessages, ["Execution ok"])
	PyXMCDA.writeFooter(fileMessages)

fileMessages.close()
