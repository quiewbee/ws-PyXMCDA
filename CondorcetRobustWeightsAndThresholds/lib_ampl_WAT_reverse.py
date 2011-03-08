import commands
import PyXMCDA

def create_ampl_reverse_data (file, altId, critId, perfTable, altComparisons, thresholds, maxWeight, criComparisons, criLB, criUB, criIndLB, criIndUB, criPreLB, criPreUB) :

	#Les contraintes du style g_i > g_j
	for crit in critId :
		file.write('set cr_'+crit+' := {"'+crit+'"};\n')
		
	#Un compteur pour numeroter les contraintes et les ensembles
	count = 1
	for comp in criComparisons :
		# On ecrit l'ensemble des neuds initiaux
		file.write('\nset crs_init_'+str(count)+' := {')
		file.write(PyXMCDA.getListOnString (comp["initial"], '"', '"', ', '))
		file.write('};\n')
		# On ecrit l'ensemble des noeuds terminaux
		file.write('set crs_term_'+str(count)+' := {')
		file.write(PyXMCDA.getListOnString (comp["terminal"], '"', '"', ', '))
		file.write('};\n')
		file.write("s.t. ct_comp_"+str(count)+" : sum{init in crs_init_"+str(count)+"} sum {k in WEIGHTUNIT} Accumulator[init,k] >= sum{term in crs_term_"+str(count)+"} sum {k in WEIGHTUNIT} Accumulator[term,k] +1;\n")
		count = count + 1
	
	#Les contraintes du style g_i > lower_bound_i
	file.write("\n")
	for crit in criLB.keys() :
		file.write("s.t. ct_LB_"+crit+"{j in cr_"+crit+"} : sum {k in WEIGHTUNIT} Accumulator[j,k] >= "+str(criLB[crit])+";\n")
	
	
	#Les contraintes du style g_i < upper_bound_i
	file.write("\n")
	for crit in criUB.keys() :
		file.write("s.t. ct_UB_"+crit+"{j in cr_"+crit+"} : sum {k in WEIGHTUNIT} Accumulator[j,k] <= "+str(criUB[crit])+";\n")
		
	#Les contraintes du style q_i > lower_bound_i
	file.write("\n")
	for crit in criIndLB.keys() :
		file.write("s.t. ct_q_LB_"+crit+"{j in cr_"+crit+"} : " + str(criIndLB[crit]) + " <=  q[j];\n")
	
	
	#Les contraintes du style q_i < upper_bound_i
	file.write("\n")
	for crit in criIndUB.keys() :
		file.write("s.t. ct_q_UB_"+crit+"{j in cr_"+crit+"} :  q[j] <= " + str(criIndUB[crit]) + ";\n")
	
	#Les contraintes du style p_i > lower_bound_i
	file.write("\n")
	for crit in criPreLB.keys() :
		file.write("s.t. ct_p_LB_"+crit+"{j in cr_"+crit+"} : " + str(criPreLB[crit]) + " <=  p[j];\n")
	
	
	#Les contraintes du style p_i < upper_bound_i
	file.write("\n")
	for crit in criPreUB.keys() :
		file.write("s.t. ct_p_UB_"+crit+"{j in cr_"+crit+"} :  p[j] <= " + str(criPreUB[crit]) + ";\n")

	file.write ("\n\n\ndata;\n\n")
	file.write ("set CRITERIA := ")
	for c in critId :
		file.write (c+" ")
	file.write(";\n\n")

	pairs2 = []
	pairsm2 = []
	pairs1 = []
	pairsm1 = []
	
	tabVeto = PyXMCDA.getVetos (altId, critId, perfTable, thresholds)
	
	for init in altComparisons.keys() :
		for term in altComparisons[init].keys() :
			
			if tabVeto.has_key(init) and tabVeto[init].has_key(term) and not tabVeto[init][term] is None :
				# Veto situation
				continue
				
			if init != term :
				val = altComparisons[init][term]
	
				if val == 2 :
					pairs2.append (""+init+term)
				elif val == -2 :
					pairsm2.append (""+init+term)
				elif val == 1 :
					pairs1.append (""+init+term)
				elif val == -1 :
					pairsm1.append (""+init+term)
				else:
					# On met une valeur pour dire que l'on n'a pas pris en compte cette valeur
					altComparisons[init][term] = 0
		
	file.write ("set ROBUSTPREFPAIRS :=\n")
	
	count = 0
	for pair in pairs2 :
		count = count + 1
		file.write (pair+" ")
		if count == 10 :
			count = 0
			file.write ("\n")
	file.write (";\n\nset ROBUSTnotPREFPAIRS :=\n")
	count = 0
	for pair in pairsm2 :
		count = count + 1
		file.write (pair+" ")
		if count == 10 :
			count = 0
			file.write ("\n")
	file.write (";\n\nset SIMPLEPREFPAIRS :=\n")
	count = 0
	for pair in pairs1 :
		count = count + 1
		file.write (pair+" ")
		if count == 10 :
			count = 0
			file.write ("\n")
	file.write (";\n\nset SIMPLEnotPREFPAIRS :=\n")
	count = 0
	for pair in pairsm1 :
		count = count + 1
		file.write (pair+" ")
		if count == 10 :
			count = 0
			file.write ("\n")
	
	file.write(";\n\n")
	
	file.write ("param maxWeight := "+str(maxWeight)+";\n\n")
	
	# On ecrit le tableau de performance
	file.write("param Perf : ")
	for c in critId :
		file.write (c+" ")
	file.write (":=\n")
	for init in altComparisons.keys() :
		for term in altComparisons[init].keys() :
			
			if tabVeto.has_key(init) and tabVeto[init].has_key(term) and not tabVeto[init][term] is None:
				# Veto situation
				continue
			if altComparisons[init][term] == 0:
				continue
			if init != term :
				file.write (str(init)+str(term)+" ")
				for crit in critId :
					file.write(str(perfTable[init][crit] - perfTable[term][crit])+" ")
				file.write ("\n")
	file.write(";\n\n")
	
	# On ecrit l'ensemble des couples d'alt et des criteres pour lesquels la premiere alt performe mieux que la deuxieme sur le critere choisi (en gros, les surclassements ne dependant pas des seuils)
#	file.write ("param SureOut : ")
#	for c in critId :
#		file.write (c+" ")
#	file.write (":=\n")
#	for init in altComparisons.keys() :
#		for term in altComparisons[init].keys() :
#			
#			if tabVeto.has_key(init) and tabVeto[init].has_key(term) and not tabVeto[init][term] is None :
#				# Veto situation
#				continue
#				
#			if init != term :
#				file.write (str(init)+str(term)+" ")
#				for crit in critId :
#					if perfTable[init][crit] >= perfTable[term][crit]:
#						file.write ("1 ")
#					else:
#						file.write ("0 ")
#				file.write ("\n")
#	file.write(";\n\n")
	
	# Les valeurs max sur chaque critere, pour normaliser
	file.write("param MaxCrit [*] := \n")
	for c in critId :
		# On suppose les valeurs toutes positives !!!!!!!!!
		valMax = 0
		for alt in altId:
			if perfTable[alt][c] > valMax:
				valMax = perfTable[alt][c]
		file.write (c+" "+str(valMax)+"\n")
	file.write (";\n\n")

