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

if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/criteria.xml") or not os.path.isfile (in_dir+"/criteriaWeights.xml") or not os.path.isfile (in_dir+"/performanceTable.xml") :
	status = 1
	errorList.append("Some input files are missing")

else :
	
	xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
	xmltree_criteria = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
	xmltree_weights = PyXMCDA.parseValidate(in_dir+"/criteriaWeights.xml")
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
	if xmltree_weights == None :
		status = 1
		errorList.append("The criteria weights file can't be validated.")
	minValDomain = 0
	maxValDomain = 1
	if os.path.isfile (in_dir+"/valuationDomain.xml") :
		xmltree_valuation = PyXMCDA.parseValidate(in_dir+"/valuationDomain.xml")
		if xmltree_valuation == None :
			status = 1
			errorList.append ("valuationDomain file can't be validated.")
		else :
			mini = PyXMCDA.getParameterByName (xmltree_valuation, "min", "valuationDomain")
			maxi = PyXMCDA.getParameterByName (xmltree_valuation, "max", "valuationDomain")
			
			if not isinstance(mini,float) and not isinstance(mini,int) :
				errorList.append ("min value should be an integer or a real")
				status = 1
			if not isinstance(mini,float) and not isinstance(mini,int) :
				errorList.append ("max value should be an integer or a real")
				status = 1
			if status !=1 :
				if mini >= maxi :
					errorList.append ("The max value should be strictly greater than the min value")
					status = 1
			if status != 1 :
				minValDomain = mini
				maxValDomain = maxi

	if status != 1 :
	
		alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
		criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
		perfTable = PyXMCDA.getPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
		thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
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

	#On calcule la somme des poids
	sumWeights = 0.0
	
	for wei in weights.keys() :
		sumWeights = sumWeights + weights[wei]

	#On genere le fichier resultat
	fileAltValues = open(out_dir+"/alternativesComparisons.xml", 'w')
	PyXMCDA.writeHeader (fileAltValues)
	
	fileAltValues.write ("<alternativesComparisons><pairs>\n")
		
	for alt1 in alternativesId :
		for alt2 in alternativesId :
			fileAltValues.write("<pair><initial><alternativeID>"+alt1+"</alternativeID></initial><terminal><alternativeID>"+alt2+"</alternativeID></terminal>")
			posCrit = -1
			sum = 0.0
			for crit in criteriaId :
				
				if perfTable[alt1][crit] >= perfTable[alt2][crit] :
					sum = sum + maxValDomain*weights[crit]
				else :
					if not thresholds[crit].has_key('indifference') and not thresholds[crit].has_key('preference') :
						# aucun seuil, indif ou pref, defini
						sum = sum + minValDomain*weights[crit]
					else :
						if (thresholds[crit].has_key('indifference') != thresholds[crit].has_key('preference')) :
							#un seuil, indif ou pref, est defini
							if thresholds[crit].has_key('indifference') :
								if perfTable[alt1][crit] + thresholds[crit]["indifference"] >= perfTable[alt2][crit] :
									sum = sum + maxValDomain*weights[crit]
								else :
									sum = sum + minValDomain*weights[crit]
							else :
								if perfTable[alt1][crit] + thresholds[crit]["preference"] >= perfTable[alt2][crit] :
									sum = sum + maxValDomain*weights[crit]
								else :
									sum = sum + minValDomain*weights[crit]
						else :
							# il y a deux seuils
							if perfTable[alt1][crit] + thresholds[crit]["indifference"] >= perfTable[alt2][crit] :
								sum = sum + maxValDomain*weights[crit]
							elif perfTable[alt1][crit] + thresholds[crit]["preference"] >= perfTable[alt2][crit] :
								sum = sum + (float(maxValDomain+minValDomain))*weights[crit]/2.0
							else :
								sum = sum + minValDomain*weights[crit]
			sum = sum/sumWeights				
			fileAltValues.write ("<value><real>"+str(sum)+"</real></value></pair>\n")
		
	fileAltValues.write ("</pairs></alternativesComparisons>")
		
	PyXMCDA.writeFooter(fileAltValues)
	fileAltValues.close()



	PyXMCDA.writeLogMessages (fileMessages, ["Execution ok"])
	PyXMCDA.writeFooter(fileMessages)

