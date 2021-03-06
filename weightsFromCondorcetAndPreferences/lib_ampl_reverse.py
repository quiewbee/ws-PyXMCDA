import commands
import PyXMCDA

def create_ampl_reverse_data (file, altId, critId, perfTable, altComparisons, thresholds, maxWeight, criComparisons, criLB, criUB) :

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
		file.write("s.t. ct_LB_"+crit+"{i in cr_"+crit+"} : sum {k in WEIGHTUNIT} Accumulator[i,k] >= "+str(criLB[crit])+";\n")
	
	
	#Les contraintes du style g_i < upper_bound_i
	file.write("\n")
	for crit in criUB.keys() :
		file.write("s.t. ct_UB_"+crit+"{i in cr_"+crit+"} : sum {k in WEIGHTUNIT} Accumulator[i,k] <= "+str(criUB[crit])+";\n")

	file.write ("\n\n\ndata;\n\n")
	file.write ("set CRITERIA := ")
	for c in critId :
		file.write (c+" ")
	file.write(";\n\nset ALLPAIRS :=\n")
	for a1 in altId :
		for a2 in altId :
			file.write (a1+a2+" ")
		file.write ("\n")
	file.write (";\n\n")

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
		
	
	file.write ("\nparam maxWeight := "+str(maxWeight))
	file.write (";\nparam S : ")
	for c in critId :
		file.write (c+" ")
	file.write (":=\n")
	
	ElemOut = PyXMCDA.getRubisElementaryOutranking (altId, critId, perfTable, thresholds)
	
	for alt1 in altId :
		for alt2 in altId :
			file.write (str(alt1)+str(alt2)+" ")
			for crit in critId :
				file.write (str(ElemOut[alt1][alt2][crit])+" ")						
			
			file.write ("\n")
	file.write(";\n")

###

def ampl_solve (scriptfilename) :
	return commands.getstatusoutput("ampl "+scriptfilename)


