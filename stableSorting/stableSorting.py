import os
import sys
import getopt
import subprocess

import PyXMCDA

from optparse import OptionParser

VERSION = "1.0"

PyXMCDA_version_required = '20111208-001'
if getattr(PyXMCDA,'__version__', '00000000-000') < PyXMCDA_version_required:
	raise ImportError('found an old PyXMCDA lib., expecting %s or higher'%PyXMCDA_version_required)

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
	if not os.path.isfile (in_dir+"/alternatives.xml") or not os.path.isfile (in_dir+"/categories.xml") or not os.path.isfile (in_dir+"/categoriesProfiles.xml") or not os.path.isfile (in_dir+"/stabilityRelation.xml"):
		errorList.append("Some input files are missing")
	
	else :
		
		if os.path.isfile (in_dir+"/sortingMode.xml") :
			xmltree_mode = PyXMCDA.parseValidate(in_dir+"/sortingMode.xml")
			if xmltree_mode == None :
				errorList.append ("sortingMode file cannot be validated.")
			else :
				mode = PyXMCDA.getParameterByName (xmltree_mode, "sortingMode")
				if not (mode == "pessimistic" or mode == "optimistic"):
					errorList.append ("Value of parameter sortingMode should be 'pessimistic' or 'optimistic'.")			
			
		xmltree_alternatives = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
		xmltree_categories = PyXMCDA.parseValidate(in_dir+"/categories.xml")
		xmltree_profiles = PyXMCDA.parseValidate(in_dir+"/categoriesProfiles.xml")
		xmltree_altStability = PyXMCDA.parseValidate(in_dir+"/stabilityRelation.xml")
		
		if xmltree_alternatives == None :
			errorList.append("The alternatives file cannot be validated.")
		if xmltree_categories == None :
			errorList.append("The categories file cannot be validated.")
		if xmltree_profiles == None :
			errorList.append("The categoriesProfiles file cannot be validated.")
		if xmltree_altStability == None :
			errorList.append("The alternatives comparisons file cannot be validated.")
				
		if not errorList :
		
			alternativesId = PyXMCDA.getAlternativesID(xmltree_alternatives, "ACTIVEREAL")
			allalt = PyXMCDA.getAlternativesID(xmltree_alternatives, "ACTIVE")
			categoriesId = PyXMCDA.getCategoriesID(xmltree_categories)
			categoriesRank = PyXMCDA.getCategoriesRank(xmltree_categories, categoriesId)
			altStability = PyXMCDA.getAlternativesComparisons (xmltree_altStability, allalt)
			
			if not alternativesId:
				errorList.append("No alternatives found.")
			if not categoriesId:
				errorList.append("No categories found.")
			if not altStability :
				errorList.append("No alternatives comparisons found.")
					
	if not errorList :
		
		catPro = PyXMCDA.getCategoriesProfiles(xmltree_profiles, categoriesId)
		proCat = PyXMCDA.getProfilesCategories(xmltree_profiles, categoriesId)
		profilesId = proCat.keys()
		
		# On retourne la liste pour trier selon les rangs
		rankCategories = {}
		for i, j in categoriesRank.iteritems():
			rankCategories[j] = i
			
		ranks = rankCategories.keys()[:]
		
		ranks.sort()
		lowestRank = ranks.pop()
		
		# Un tableau pour conserver les affectations
		affectations = {}
		
		if mode == "pessimistic":
			# Electre tri pessimistic rule
			for alt in alternativesId:
				affectations[alt] = []
				for rank in ranks:
					profile = catPro[rankCategories[rank]]["lower"]
					if altStability[alt][profile] >= -1 and altStability[alt][profile] <= 1:
						# Surclassement instable, on ajoute les categories sup et inf
						if affectations[alt].count(proCat[profile]["lower"]) == 0:
							affectations[alt].append(proCat[profile]["lower"])
						if affectations[alt].count(proCat[profile]["upper"]) == 0:
							affectations[alt].append(proCat[profile]["upper"])
					if altStability[alt][profile] > 1:
						# Surclassement stable, on ajoute que sup et on arrete
						if affectations[alt].count(proCat[profile]["upper"]) == 0:
							affectations[alt].append(proCat[profile]["upper"])
							break
				
				if affectations[alt] == []:
					# Tous les surc stables et negatifs, on force la categorie la plus basse
					affectations[alt] = [rankCategories[lowestRank]]

		else:
			errorList.append("Optimistic rule is not taken into account yet")
	
	if not errorList :	
					
		# Creating alternativesAffectations file
		fileAffectations = open(out_dir+"/alternativesAffectations.xml",'w')
		PyXMCDA.writeHeader(fileAffectations)
		
		# We write some information about the generated file
		fileAffectations.write ("\t<projectReference>\n\t\t<title>Stable alternatives affectation</title>\n\t\t<version>"+VERSION+"</version>\n\t\t<author>ws_PyXMCDA suite (TV)</author>\n\t</projectReference>\n\n")
		
		fileAffectations.write("\t<alternativesAffectations>\n")
		
		for alt in alternativesId:
			fileAffectations.write("\t\t<alternativeAffectation>\n\t\t\t<alternativeID>"+alt+"</alternativeID>\n\t\t\t<categoriesSet>\n")
			
			for cat in affectations[alt]:
				fileAffectations.write("\t\t\t\t<element><categoryID>"+cat+"</categoryID></element>\n")

			fileAffectations.write("\t\t\t</categoriesSet>\n\t\t</alternativeAffectation>\n")
		
		fileAffectations.write("\t</alternativesAffectations>\n")
		PyXMCDA.writeFooter(fileAffectations)
		fileAffectations.close()
	
	
	# Creating log and error file, messages.xml
	fileMessages = open(out_dir+"/messages.xml", 'w')
	PyXMCDA.writeHeader (fileMessages)
	
	if not errorList :
		logList.append("Execution ok")
		PyXMCDA.writeLogMessages (fileMessages, logList)
	else :
		PyXMCDA.writeErrorMessages (fileMessages, errorList)
		
	PyXMCDA.writeFooter(fileMessages)
	fileMessages.close()

if __name__ == "__main__":
    sys.exit(main())
