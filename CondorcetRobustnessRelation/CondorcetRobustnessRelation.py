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
	
		# We create the weight class (only considering the active criteria)
		
		uniqueWeights = []
		classWeights = {}
		
		for crit in criteriaId :
			try :
				if classWeights.has_key (str(weights[crit])) :
					classWeights[str(weights[crit])].append(crit)
				else :
					classWeights[str(weights[crit])] = [crit]
					uniqueWeights.append(str(weights[crit]))
			except :
				errorList.append("There is no defined weight for criterion "+crit+".")
	
		uniqueWeights = sorted(uniqueWeights, reverse=False)
	
	if not errorList :
	
		# We compute the weight sum (only the weights associated to active criteria)
		sumWeights = 0.0
		
		for crit in criteriaId :
			try :
				sumWeights = sumWeights + weights[crit]
			except :
				errorList.append("There is no defined weight for criterion "+crit+".")
				
	if not errorList :
		
		# We recover the criteria preference directions
		criteriaDir = PyXMCDA.getCriteriaPreferenceDirections (xmltree_criteria, criteriaId)
		
		# On retourne les valeurs pour les criteres a minimiser
		# ATTENTION ! NE MARCHE QUE SI VALEUR NUMERIQUES !!!
		for crit in criteriaId:
			if criteriaDir.has_key (crit) and criteriaDir[crit] == "min" :
				for alt in alternativesId:			
					perfTable[alt][crit] = -perfTable[alt][crit]
		
		# We compute the alternative comparisons values
		fileAltValues = open(out_dir+"/alternativesComparisons.xml", 'w')
		PyXMCDA.writeHeader (fileAltValues)
		
		fileAltValues.write ("\t<alternativesComparisons mcdaConcept='CondorcetRobustnessRelation'>\n\t\t<pairs>\n")
			
		for alt1 in alternativesId: #["Flat 7"]: #alternativesId :
			for alt2 in alternativesId: #["Flat 2"]: #alternativesId :
			
				fileAltValues.write("\t\t\t<pair>\n\t\t\t\t<initial><alternativeID>"+alt1+"</alternativeID></initial>\n\t\t\t\t<terminal><alternativeID>"+alt2+"</alternativeID></terminal>\n")
				
				ElementaryVector = {}
				sum = 0.0
				probComparisons = False
				
				for crit in criteriaId :
				
					# If the value of one criteria is NA
					if perfTable[alt1][crit] == "NA" or perfTable[alt2][crit] == "NA":
						print "NANANANANANANANAN"
						
					try :
						if perfTable[alt1][crit] >= perfTable[alt2][crit] :
							sum = sum + weights[crit]
							ElementaryVector[crit] = 1
						else :
							if not thresholds[crit].has_key('indifference') and not thresholds[crit].has_key('preference') :
								# No constant thresholds are defined for the seleccted criterion
								ElementaryVector[crit] = 0
							else :
								if (thresholds[crit].has_key('indifference') != thresholds[crit].has_key('preference')) :
									# An indifference Xor a preference threshold has been defined
									if thresholds[crit].has_key('indifference') :
										if perfTable[alt1][crit] + thresholds[crit]["indifference"] >= perfTable[alt2][crit] :
											sum = sum + weights[crit]
											ElementaryVector[crit] = 1
										else :
											ElementaryVector[crit] = 0
									else :
										if perfTable[alt1][crit] + thresholds[crit]["preference"] >= perfTable[alt2][crit] :
											sum = sum + weights[crit]
											ElementaryVector[crit] = 1
										else :
											ElementaryVector[crit] = 0
								else :
									# An indifference and a preference thresholds have been defined
									if perfTable[alt1][crit] + thresholds[crit]["indifference"] >= perfTable[alt2][crit] :
										sum = sum + weights[crit]
										ElementaryVector[crit] = 1
									elif perfTable[alt1][crit] + thresholds[crit]["preference"] >= perfTable[alt2][crit] :
										sum = sum + weights[crit]/2.0
										ElementaryVector[crit] = 0.5
									else :
										ElementaryVector[crit] = 0
					except :
						errorList.append("some alternatives evaluations are missing for criterion "+crit+", during the comparison between "+alt1+" and "+alt2+".")
						probComparisons = True
				
				if not probComparisons :
					sum = sum/sumWeights
					
					# We compute the corresponding Condorcet denotation
					if sum == 0 :
						# m3 denotation
						fileAltValues.write ("\t\t\t\t<value><integer>-3</integer></value>\n\t\t\t</pair>\n")
					elif sum == 1 :
						# p3 denotation
						fileAltValues.write ("\t\t\t\t<value><integer>3</integer></value>\n\t\t\t</pair>\n")
					elif sum == 0.5 :
						# 0 denotation
						fileAltValues.write ("\t\t\t\t<value><integer>0</integer></value>\n\t\t\t</pair>\n")
					elif sum < 0.5 :
						# m1 or m2 denotation
						conditionm2Ok = True
						strictInequality = False
						sumPro = 0.0
						sumAgainst = 0.0
						
						for we in uniqueWeights :
							for crit in classWeights[we] :
								sumPro += ElementaryVector[crit]
								sumAgainst += 1.0 - ElementaryVector[crit]
							if sumPro > sumAgainst :
								conditionm2Ok = False
								break
							if sumPro < sumAgainst :
								strictInequality = True
						
						if conditionm2Ok and strictInequality :
							fileAltValues.write ("\t\t\t\t<value><integer>-2</integer></value>\n\t\t\t</pair>\n")
						else :
							fileAltValues.write ("\t\t\t\t<value><integer>-1</integer></value>\n\t\t\t</pair>\n")
					else :
						# p1 or p2 denotation
						conditionp2Ok = True
						strictInequality = False
						sumPro = 0.0
						sumAgainst = 0.0
						
						for we in uniqueWeights :
							for crit in classWeights[we] :
								sumPro += ElementaryVector[crit]
								sumAgainst += 1.0 - ElementaryVector[crit]
							if sumPro < sumAgainst :
								conditionp2Ok = False
								break
							if sumPro > sumAgainst :
								strictInequality = True
						
						if conditionp2Ok and strictInequality :
							fileAltValues.write ("\t\t\t\t<value><integer>2</integer></value>\n\t\t\t</pair>\n")
						else :
							fileAltValues.write ("\t\t\t\t<value><integer>1</integer></value>\n\t\t\t</pair>\n")
				else :
					fileAltValues.write ("\t\t\t\t<value><NA>not available</NA></value>\n\t\t\t</pair>\n")
			
		fileAltValues.write ("\t\t</pairs>\n\t</alternativesComparisons>\n")
			
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
