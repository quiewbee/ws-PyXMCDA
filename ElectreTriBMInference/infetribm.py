import os
import sys
import getopt
import subprocess
import tempfile
from optparse import OptionParser

import glpk
import xmcda 
import PyXMCDA

error_list = []
verbose = False

def log(msg):
    if verbose == True:
        print >>sys.stderr, msg

def parse_cmdline(argv=None):
    parser = OptionParser()
    parser.add_option("-i", "--in", dest="in_dir")
    parser.add_option("-o", "--out", dest="out_dir")
    (options, args) = parser.parse_args(argv[1:])
    in_dir = options.in_dir
    out_dir = options.out_dir
    if not in_dir:
        error_list.append("option --in is missing")
    if not out_dir:
        error_list.append("option --out is missing")
    return (in_dir, out_dir)

def check_input_files(in_dir):
    if not os.path.isfile(in_dir+"/criteria.xml"):
        error_list.append("No criteria.xml file") 

    if not os.path.isfile(in_dir+"/alternatives.xml"):
        error_list.append("No alternatives.xml file") 

    if not os.path.isfile(in_dir+"/perfs_table.xml"):
        error_list.append("No perfs_table.xml file") 

    if not os.path.isfile(in_dir+"/assign.xml"):
        error_list.append("No assign.xml file")

    if not os.path.isfile(in_dir+"/categories.xml"):
        error_list.append("No categories.xml file")

def parse_xmcda_files(in_dir):
    xml_crit = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
    xml_alt = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
    xml_pt = PyXMCDA.parseValidate(in_dir+"/perfs_table.xml")
    xml_assign = PyXMCDA.parseValidate(in_dir+"/assign.xml")
    xml_cat = PyXMCDA.parseValidate(in_dir+"/categories.xml")

    if xml_crit == None:
        error_list.append("Invalid criteria file")
        return
    if xml_alt == None:
        error_list.append("Invalid alternative file")
        return
    if xml_pt == None:
        error_list.append("Invalid performance table file")
        return
    if xml_assign == None:
        error_list.append("Invalid assignment file")
        return
    if xml_cat == None:
        error_list.append("Invalid categories file")
        return

    try:
        alt_id = PyXMCDA.getAlternativesID(xml_alt)
        crit_id = PyXMCDA.getCriteriaID(xml_crit)
        pt = PyXMCDA.getPerformanceTable(xml_pt, alt_id, crit_id)
        cat_id = PyXMCDA.getCategoriesID(xml_cat)
        cat_rank = PyXMCDA.getCategoriesRank(xml_cat, cat_id)
        assign = PyXMCDA.getAlternativesAffectations(xml_assign)
        pref_dir = PyXMCDA.getCriteriaPreferenceDirections(xml_crit, crit_id)
    except:
        error_list.append("Failed to parse one or more file")
        return

    return (alt_id, crit_id, pt, cat_id, cat_rank, assign, pref_dir)

def get_fixed_parameters(in_dir, alt_id, crit_id, pt, cat_id, cat_rank, pref_dir):
    weights = None
    lbda = None
    cat_profiles = None
    pt_refalts = None

    xml_weights = PyXMCDA.parseValidate(in_dir+"/crit_weights.xml")
    xml_lbda = PyXMCDA.parseValidate(in_dir+"/lambda.xml")
    xml_catprofiles = PyXMCDA.parseValidate(in_dir+"/cat_profiles.xml")
    xml_refalts = PyXMCDA.parseValidate(in_dir+"/reference_alts.xml")

    if xml_weights != None and xml_lbda != None:
        if xml_weights == None or xml_lbda == None:
            error_list.append("You must give both weights and lambda")
            
        try:
            weights = PyXMCDA.getCriterionValue(xml_weights, crit_id) 
            weights_sum = sum(weights.values())
            for key, value in weights.iteritems():
                weights[key] = value/weights_sum

            lbda = xmcda.get_lambda(xml_lbda)
        except:
            error_list.append("Unable to get fixed weights or lambda")

    if xml_catprofiles != None and xml_refalts != None:
        if xml_catprofiles == None or xml_refalts == None:
            error_list.append("You must give both categories profiles and performance table of reference alternatives")

        try:
            cat_profiles = xmcda.get_categories_profiles(xml_catprofiles)
            pt_refalts = PyXMCDA.getPerformanceTable(xml_refalts, cat_id, crit_id)
        except:
            error_list.append("Unable to get fixed profiles")

    if weights != None and lbda != None and pt_refalts != None:
        error_list.append("No parameters to infer")

    return (weights, lbda, cat_profiles, pt_refalts)

def get_sorted_profiles(cat_profiles, cat_rank, pt):
    lower_cat_rank = {}
    for profile, limits in cat_profiles.iteritems():
        lower_cat_rank[profile] = limits["lower"]


    profiles_rank = {}
    for profile, category in lower_cat_rank.iteritems():
        profiles_rank[cat_rank[category]] = profile

    ranks = profiles_rank.keys()
    ranks.sort()
    pt_profiles = []
    for rank in ranks:
        profile = profiles_rank[rank]
        pt_profiles.append(pt[profile])

    return pt_profiles

def get_min_max(pt):
    gmax = {}
    gmin = {}
    for alt, perfs in pt.iteritems():
        for crit, perf in perfs.iteritems():
            if gmax.has_key(crit) == False or perf > gmax[crit]:
                gmax[crit] = perf

            if gmin.has_key(crit) == False or perf < gmin[crit]:
                gmin[crit] = perf

    return (gmin, gmax)

def normalize(pt, gmin, gmax, prefdir):
    for alt, perfs in pt.iteritems():
        for crit, perf in perfs.iteritems():
            div = gmax[crit]-gmin[crit]
            if div == 0:
                div = 1

            if prefdir[crit] == "min":
                pt[alt][crit] = float(gmax[crit]-perf)/div
            else:
                pt[alt][crit] = float(perf-gmin[crit])/div

def denormalize(pt, gmin, gmax, prefdir):
    for alt, perfs in pt.iteritems():
        for crit, perf in perfs.iteritems():
            if prefdir[crit] == "min":
                pt[alt][crit] = gmax[crit] - float(perf)*(gmax[crit]-gmin[crit])
            else:
                pt[alt][crit] = gmin[crit] + float(perf)*(gmax[crit]-gmin[crit])

def check_input_parameters(alt_id, crit_id, pt, cat_id, assign):
    if not alt_id:
        error_list.append("The alternatives file can't be validated.")
    if not crit_id:
        error_list.append("The criteria file can't be validated.")
    if not pt:
        error_list.append("The performance table file can't be validated.")
    if not cat_id:
        error_list.append("The categories file can't be validated.")
    if not assign:
        error_list.append("The assign file can't be validated.")

def create_output_file(xml_data, filename):
    f = open(filename, 'w')
    data = xmcda.add_xmcda_tags(xml_data)
    f.write(data)
    f.close()

def create_output_files(out_dir, weights, catprof, refalts, lbda, compat):
    create_output_file(weights, out_dir+"/crit_weights.xml") 
    create_output_file(catprof, out_dir+"/cat_profiles.xml") 
    create_output_file(refalts, out_dir+"/reference_alts.xml") 
    create_output_file(lbda, out_dir+"/lambda.xml") 
    create_output_file(compat, out_dir+"/compatible_alts.xml") 

def create_error_file(out_dir, errors):
    msgfile = open(out_dir+"/messages.xml", 'w')
    PyXMCDA.writeHeader(msgfile)
    PyXMCDA.writeErrorMessages(msgfile, errors)
    PyXMCDA.writeFooter(msgfile)
    msgfile.close()

def create_log_file(out_dir, logs):
    msgfile = open(out_dir+"/messages.xml", 'w')
    PyXMCDA.writeHeader(msgfile)
    PyXMCDA.writeLogMessages(msgfile, logs)
    PyXMCDA.writeFooter(msgfile)
    msgfile.close()

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Parsing of the options
    (in_dir, out_dir) = parse_cmdline(argv)
    if error_list:
        return error_list

    check_input_files(in_dir)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    (alt_id, crit_id, pt, cat_id, cat_rank, assign, pref_dir) = parse_xmcda_files(in_dir)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    # Name of the profile alternatives
    palts_id = [ "b%d" % (i+1) for i in range(len(cat_id)-1) ]

    log("GLPK INPUT:")
    log('alt  ids   : %s' % alt_id)
    log('crit ids   : %s' % crit_id)
    log('perfs      : %s' % pt)
    log('categories : %s' % cat_id)
    log('affect     : %s' % assign)
    log('pref_dir   : %s' % pref_dir)

    check_input_parameters(alt_id, crit_id, pt, cat_id, assign)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    fixed_params = get_fixed_parameters(in_dir, alt_id, crit_id, pt, cat_id, cat_rank, pref_dir)
    fixed_weights = fixed_params[0]
    fixed_lambda = fixed_params[1]
    fixed_cat_profiles = fixed_params[2]
    fixed_pt_profiles = fixed_params[3]
    log('fixed_weights  : %s' % fixed_weights)
    log('fixed_lambda  : %s' % fixed_lambda)
    log('fixed_cat_profiles  : %s' % fixed_cat_profiles)
    log('fixed_pt_profiles  : %s' % fixed_pt_profiles)

    try:
        (gmin, gmax) = get_min_max(pt)
        if fixed_pt_profiles:
            (gmin2, gmax2) = get_min_max(fixed_pt_profiles)
            for c, val in gmin.iteritems():
                if gmin[c] > gmin2[c]:
                    gmin[c] = gmin2[c]
                if gmax[c] < gmax2[c]:
                    gmax[c] = gmax2[c]
    except:
        error_list.append("Impossible to get min max values in pt")
        create_error_file(out_dir, error_list)
        return error_list

    try:
        normalize(pt, gmin, gmax, pref_dir) 
    except:
        error_list.append("Impossible to convert performance table")
        create_error_file(out_dir, error_list)
        return error_list

    if fixed_pt_profiles:
        try:
            normalize(fixed_pt_profiles, gmin, gmax, pref_dir)
            fixed_profiles = get_sorted_profiles(fixed_cat_profiles, cat_rank, fixed_pt_profiles)
        except:
            error_list.append("Impossible to convert profile performance table")
            create_error_file(out_dir, error_list)
            return error_list
    else:
        fixed_profiles = None

    if fixed_weights:
        glpk_model = "inf_etri_bm_fixed_weights.mod"
    elif fixed_pt_profiles:
        glpk_model = "inf_etri_bm_fixed_profiles.mod"
    else:
        glpk_model = "inf_etri_bm.mod"

    log("GLPK model used: %s" % glpk_model)

    try:
        input_file = glpk.create_input_file(alt_id, crit_id, pt, cat_id, cat_rank, assign, fixed_weights, fixed_lambda, fixed_profiles)
    except:
        error_list.append("Impossible to create glpk input file")

    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    (status, output) = glpk.solve(glpk_model, input_file.name)
    if status:
        error_list.append("GLPK returned status %d" % status);
        input_file.close()
        create_error_file(out_dir, error_list)
        return error_list

    input_file.close()

    out_params = glpk.parse_output(output, alt_id, crit_id)
    if out_params == None:
        error_list.append("Error parsing output parameters")
        create_error_file(out_dir, error_list)
        return error_list

    weights = out_params[0]
    profiles = out_params[1]
    for profile in profiles:
        denormalize(profile, gmin, gmax, pref_dir)
    lbda = out_params[2]
    compat = out_params[3]
    
    log("GLPK OUTPUT:")
    log("weights  : %s" % weights)
    log("profiles : %s" % profiles)
    log("lambda   : %s" % lbda)
    log("compat   : %s" % compat)
    
    if not weights:
        error_list.append("Impossible to get weights from the solver")
    
    if not profiles:
        error_list.append("Impossible to get profiles from the solver")
    
    if not lbda:
        error_list.append("Impossible to get lambda from the solver")
    
    if not compat:
        error_list.append("Impossible to get compatible alternatives from the solver")

    if error_list:
        create_error_file(out_dir, error_list)
        return error_list
    
    out_weights = xmcda.format_criteria_weights(weights)
    out_catprof = xmcda.format_category_profiles(profiles, palts_id, cat_id)
    out_refalts = xmcda.format_pt_reference_alternatives(profiles, palts_id, crit_id)
    out_lambda = xmcda.format_lambda(lbda)
    out_compat = xmcda.format_format_compatible_alternatives(compat, alt_id)
    create_output_files(out_dir, out_weights, out_catprof, out_refalts, out_lambda, out_compat)

    logs = [ "Execution ok" ]
    create_log_file(out_dir, logs)

if __name__ == "__main__":
    sys.exit(main())
