import os
import sys
import getopt
import subprocess
import random

import PyXMCDA

from optparse import OptionParser


###

# Il faut donner la possibilite de lancer avec une graine predefinie
random.seed()

parser = OptionParser()

parser.add_option("-i", "--in", dest="in_dir")
parser.add_option("-o", "--out", dest="out_dir")

(options, args) = parser.parse_args()

in_dir = options.in_dir
out_dir = options.out_dir

critAverage = {}
critNormalSD = {}
critTriangSD = {}

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

	if not errorList :
	
		alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
		criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
		
		if not alternativesId :
			errorList.append("No alternatives found. Is your alternatives file correct ?")
		if not criteriaId :
			errorList.append("No criteria found. Is your criteria file correct ?")

if not errorList :

	# We check if parameters for criteria distribution profile have been provided
	if os.path.isfile (in_dir+"/criteriaProfiles.xml") :
		xmltree_CritProfile = PyXMCDA.parseValidate(in_dir+"/criteriaProfiles.xml")
		if xmltree_CritProfile == None :
			errorList.append ("criteriaProfiles file can't be validated.")
		else :
			critAverage = PyXMCDA.getNamedParametersByName (xmltree_CritProfile, "distributionAverage")
			critNormalSD = PyXMCDA.getNamedParametersByName (xmltree_CritProfile, "normalDistributionStandardDeviation")
			critTriangSD = PyXMCDA.getNamedParametersByName (xmltree_CritProfile, "triangularDistributionStandardDeviation")
			# ...
			

if not errorList :

	# We recover criteria scale information
	criteriaTypes = PyXMCDA.getCriteriaScalesTypes (xmltree_criteria, criteriaId)
	criteriaDir = PyXMCDA.getCriteriaPreferenceDirections (xmltree_criteria, criteriaId)
	criteriaUB = PyXMCDA.getCriteriaUpperBounds (xmltree_criteria, criteriaId)
	criteriaLB = PyXMCDA.getCriteriaLowerBounds (xmltree_criteria, criteriaId)
	criteriaRL = PyXMCDA.getCriteriaRankedLabel (xmltree_criteria, criteriaId)
	
	# We add some default lower and upper bounds
	for crit in criteriaId :
		if not criteriaLB.has_key (crit) or criteriaLB[crit] == None :
			if criteriaTypes[crit] == "quantitative" :
				criteriaLB[crit] = 0.0
			else :
				criteriaLB[crit] = 1
		if not criteriaUB.has_key (crit) or criteriaUB[crit] == None :
			if criteriaTypes[crit] == "quantitative" :
				criteriaUB[crit] = 100.0
			else :
				if criteriaRL.has_key(crit) and criteriaRL[crit] != None :
					criteriaUB[crit] = len(criteriaRL[crit])
				else :
					criteriaUB[crit] = 10
			
	# We construct the performance Tableau
	Tab = {}
	for crit in criteriaId :
		Tab[crit] = {}
		
		if critNormalSD.has_key(crit) :
			sd = critNormalSD[crit]
			if critAverage.has_key(crit) :
				average = critAverage[crit]
			else :
				average = (criteriaLB[crit] + criteriaUB[crit])/2.0
			for alt in alternativesId :			
				temp = criteriaLB[crit] -1
				while temp < criteriaLB[crit] or temp > criteriaUB[crit] :
					temp = random.gauss (average,sd)
					print "temp : " + str (temp)
				if criteriaDir[crit] == "min" :
					Tab[crit][alt] = criteriaUB[crit] - temp
				else :
					Tab[crit][alt] = temp
				if criteriaTypes[crit] == "qualitative" :
					Tab[crit][alt] = PyXMCDA.closestInt(Tab[crit][alt])
				
		elif critTriangSD.has_key (crit) :
			for alt in alternativesId :
				# MODIFIER !!!
				Tab[crit][alt] = random.randint (criteriaLB[crit], criteriaUB[crit])
		
		else :
			for alt in alternativesId :
				if criteriaTypes[crit] == "quantitative" :
					Tab[crit][alt] = float(random.randint (criteriaLB[crit]*100, criteriaUB[crit]*100))/100.0
				else :
					Tab[crit][alt] = random.randint (criteriaLB[crit], criteriaUB[crit])
	
	# We construct the performanceTable.xml file
	filePerfTable = open(out_dir+"/performanceTable.xml", 'w')
	PyXMCDA.writeHeader (filePerfTable)
	
	filePerfTable.write ("<performanceTable>\n")
	
	for alt in alternativesId :
		filePerfTable.write ("\t<alternativePerformances>\n\t\t<alternativeID>" + alt + "</alternativeID>\n")
		
		for crit in criteriaId :
			if criteriaTypes[crit] == "quantitative" :
				filePerfTable.write ("\t\t<performance>\n\t\t\t<criterionID>" + crit + "</criterionID>\n\t\t\t<value><real>"+ str(Tab[crit][alt]) + "</real></value>\n\t\t</performance>\n")
			else :
				filePerfTable.write ("\t\t<performance>\n\t\t\t<criterionID>" + crit + "</criterionID>\n\t\t\t<value><integer>"+ str(Tab[crit][alt]) + "</integer></value>\n\t\t</performance>\n")
		
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
