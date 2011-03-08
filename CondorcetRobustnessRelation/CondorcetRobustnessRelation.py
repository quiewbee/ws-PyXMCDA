import os
import sys
import getopt
import subprocess

import PyXMCDA

from optparse import OptionParser

VERSION = "1.3.1"


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
	
	# If some mandatory folders haven't been provided
	if not in_dir or not out_dir:
		print "You have to provide an input and an output directory, using -i and -o command line options"
		return
	
	if not os.path.isdir(out_dir):
		print "The specified output directory doesn't exist"
		return
		
	if not os.path.isdir(in_dir):
		print "The specified input directory doesn't exist"
		return
		
	# If some mandatory input files are missing
	if not os.path.isfile (in_dir+"/alternatives.xml") \
	or not os.path.isfile (in_dir+"/criteria.xml") \
	or not os.path.isfile (in_dir+"/criteriaWeights.xml") \
	or not os.path.isfile (in_dir+"/performanceTable.xml") :
		
		errorList.append("Some input files are missing")
		PyXMCDA.createMessagesFile (out_dir+"/messages.xml", [], [], errorList)
		return
		
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
		
	if errorList:
		PyXMCDA.createMessagesFile (out_dir+"/messages.xml", [], [], errorList)
		return
	
	# We capture the data
	alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives)
	criteriaId = PyXMCDA.getCriteriaID(xmltree_criteria)
	perfTable = PyXMCDA.getNumericPerformanceTable(xmltree_perfTable, alternativesId, criteriaId)
	thresholds = PyXMCDA.getConstantThresholds (xmltree_criteria, criteriaId)
	weights = PyXMCDA.getCriterionValue (xmltree_weights, criteriaId)
	criteriaDir = PyXMCDA.getCriteriaPreferenceDirections (xmltree_criteria, criteriaId)
		
	if not alternativesId :
		errorList.append("No alternatives found. Is your alternatives file correct ?")
	if not criteriaId :
		errorList.append("No criteria found. Is your criteria file correct ?")
	if not perfTable :
		errorList.append("No performance table found. Is your performance table file correct ?")
	if not weights :
		errorList.append("No weights found. Is your weights file correct ?")
		
	if errorList:
		PyXMCDA.createMessagesFile (out_dir+"/messages.xml", [], [], errorList)
		return
	
	# We create the weight classes and the weight sum (only considering the active criteria)
	uniqueWeights = []
	classWeights = {}
	sumWeights = 0.0
	
	for crit in criteriaId :
		try :
			sumWeights = sumWeights + weights[crit]
			if classWeights.has_key (str(weights[crit])) :
				classWeights[str(weights[crit])].append(crit)
			else :
				classWeights[str(weights[crit])] = [crit]
				uniqueWeights.append(str(weights[crit]))
		except :
			errorList.append("There is no defined weight for criterion "+crit+".")
			PyXMCDA.createMessagesFile (out_dir+"/messages.xml", [], [], errorList)
			return
	
	uniqueWeights = sorted(uniqueWeights, reverse=True)
	
	# We compute the alternative comparisons values
	fileAltValues = open(out_dir+"/alternativesComparisons.xml", 'w')
	PyXMCDA.writeHeader (fileAltValues)
	
	# We write some information about the generated file
	fileAltValues.write ("\t<projectReference>\n\t\t<title>Condorcet robustness relation</title>\n\t\t<version>"+VERSION+"</version>\n\t\t<author>ws_PyXMCDA suite (TV)</author>\n\t</projectReference>\n\n")
	
	fileAltValues.write ("\t<alternativesComparisons mcdaConcept='CondorcetRobustnessRelation'>\n\t\t<pairs>\n")
	
	ElemOutranking = PyXMCDA.getRubisElementaryOutranking (alternativesId, criteriaId, perfTable, thresholds)
	tabVeto = PyXMCDA.getVetos (alternativesId, criteriaId, perfTable, thresholds)
	
	for alt1 in alternativesId:
		for alt2 in alternativesId:
		
			fileAltValues.write("\t\t\t<pair>\n\t\t\t\t<initial><alternativeID>"+alt1+"</alternativeID></initial>\n\t\t\t\t<terminal><alternativeID>"+alt2+"</alternativeID></terminal>\n")
			
			if tabVeto.has_key(alt1) and tabVeto[alt1].has_key(alt2) and not tabVeto[alt1][alt2] is None :
				# Veto situation
				fileAltValues.write ("\t\t\t\t<value><integer>-3</integer></value>\n\t\t\t</pair>\n")
				continue
			
			ElementaryVector = ElemOutranking[alt1][alt2]
			sum = 0.0
			probComparisons = False
			
			try :
				for crit in criteriaId:
					sum = sum + weights[crit]*ElemOutranking[alt1][alt2][crit]
			except:
				errorList.append("some alternatives evaluations are missing for criterion "+crit+", during the comparison between "+alt1+" and "+alt2+".")
				probComparisons = True
			
			if probComparisons :
				fileAltValues.write ("\t\t\t\t<value><NA>not available</NA></value>\n\t\t\t</pair>\n")
				continue
				
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
		
	fileAltValues.write ("\t\t</pairs>\n\t</alternativesComparisons>\n")
	
	PyXMCDA.writeFooter(fileAltValues)
	fileAltValues.close()
	
	# Creating log and error file, messages.xml
	if not errorList :
		PyXMCDA.createMessagesFile (out_dir+"/messages.xml", ["Execution ok"], [], [])
	else :
		PyXMCDA.createMessagesFile (out_dir+"/messages.xml", [], [], errorList)



if __name__ == "__main__":
    sys.exit(main())
