import os
import sys
import getopt
import subprocess
import random

import PyXMCDA

from optparse import OptionParser


###

random.seed()

parser = OptionParser()

parser.add_option("-i", "--in", dest="in_dir")
parser.add_option("-o", "--out", dest="out_dir")

(options, args) = parser.parse_args()

in_dir = options.in_dir
out_dir = options.out_dir

# Creating a list for error messages
errorList = []

# If some mandatory input files are missing
if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") :
	errorList.append("Some input files are missing")

else :
	
	# We parse all the mandatory input files
	xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
	xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
	
	# We check if all madatory input files are valid
	if xmltree_alternatives == None :
		errorList.append("The alternatives file can't be validated.")
	if xmltree_criteria == None :
		errorList.append("The criteria file can't be validated.")
	
#### PAR LA SUITE, AJOUTER ICI UN TEST POUR UN PARAMETRE PERMETTANT DE PRECISER UN PEU LES VALEURS DE CHAQUE EVALUATION, DU GENRE LES BORNES, LE TYPE (ENTIER OU REAL,...)

	if not errorList :
	
		alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
		criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
		#thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)	
		
		if not alternativesId :
			errorList.append("No alternatives found. Is your alternatives file correct ?")
		if not criteriaId :
			errorList.append("No criteria found. Is your criteria file correct ?")


if not errorList :

	# We construct the performanceTable.xml file
	filePerfTable = open(out_dir+"/performanceTable.xml", 'w')
	PyXMCDA.writeHeader (filePerfTable)
	
	filePerfTable.write ("<performanceTable>\n")
	
	
	for alt in alternativesId :
		filePerfTable.write ("\t<alternativePerformances>\n\t\t<alternativeID>" + alt + "</alternativeID>\n")
		
		for crit in criteriaId :
			filePerfTable.write ("\t\t<performance>\n\t\t\t<criterionID>" + crit + "</criterionID>\n\t\t\t<value><integer>"+ str(random.randint(1,100)) + "</integer></value>\n\t\t</performance>\n")
			
		filePerfTable.write ("\t</alternativePerformances>\n")
	
	filePerfTable.write ("</performanceTable>\n")
	
	PyXMCDA.writeFooter(filePerfTable)
	filePerfTable.close()

# Creating log and error file, messages.xml
fileMessages = open(out_dir+"/messages.xml", 'w')
PyXMCDA.writeHeader (fileMessages)

if not errorList :

	PyXMCDA.writeLogMessages (fileMessages, ["Execution ok"])
else :
	PyXMCDA.writeErrorMessages (fileMessages, errorList)
	
PyXMCDA.writeFooter(fileMessages)
fileMessages.close()
