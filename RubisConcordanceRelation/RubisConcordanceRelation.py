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
		
		# By default, the valuation domain is fixed to [0,1]	
		minValDomain = 0
		maxValDomain = 1
		
		# If a valuation domain input file has been provided
		if os.path.isfile (in_dir+"/valuationDomain.xml") :
		
			xmltree_valuation = PyXMCDA.parseValidate(in_dir+"/valuationDomain.xml")
			if xmltree_valuation == None :
				errorList.append ("valuationDomain file can't be validated.")
				
			else :
			
				minValDomain = PyXMCDA.getParameterByName (xmltree_valuation, "min", "valuationDomain")
				maxValDomain = PyXMCDA.getParameterByName (xmltree_valuation, "max", "valuationDomain")
				
				# We check the validity of the parameters
				if not isinstance(minValDomain,float) and not isinstance(minValDomain,int) :
					errorList.append ("min value should be an integer or a real")
				if not isinstance(maxValDomain,float) and not isinstance(maxValDomain,int) :
					errorList.append ("max value should be an integer or a real")
					
				if not errorList :
					if minValDomain >= maxValDomain :
						errorList.append ("The max value should be strictly greater than the min value")
	
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
	
		# We compute the alternative comparisons values
		fileAltValues = open(out_dir+"/alternativesComparisons.xml", 'w')
		PyXMCDA.writeHeader (fileAltValues)
		
		fileAltValues.write ("\t<alternativesComparisons>\n\t\t<pairs>\n")
		
		ElemOut = PyXMCDA.getRubisElementaryOutranking (alternativesId, criteriaId, perfTable, thresholds)
		
		for alt1 in alternativesId :
			for alt2 in alternativesId :
			
				fileAltValues.write("\t\t\t<pair>\n\t\t\t\t<initial><alternativeID>"+alt1+"</alternativeID></initial>\n\t\t\t\t<terminal><alternativeID>"+alt2+"</alternativeID></terminal>\n")
				
				# Verifier s'il manque des valeurs !!! try expect
				#fileAltValues.write ("\t\t\t\t<value><NA>not available</NA></value>\n\t\t\t</pair>\n")
				sum = 0.0
				
				for crit in criteriaId :
					
					sum += ElemOut[alt1][alt2][crit] * weights[crit]
					
				sum = sum/sumWeights
				
				# La valeur est entre 0 et 1, on la met dans le bon intervalle
				sum = (maxValDomain - minValDomain)*sum + minValDomain
				
				fileAltValues.write ("\t\t\t\t<value><real>"+str(sum)+"</real></value>\n\t\t\t</pair>\n")
					
			
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
