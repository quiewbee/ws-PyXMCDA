import os
import sys
import getopt
import subprocess
import tempfile
from optparse import OptionParser

import xmcda 
import PyXMCDA

error_list = []

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

    if not os.path.isfile(in_dir+"/performanceTable.xml"):
        error_list.append("No perfs_table.xml file") 

    if not os.path.isfile(in_dir+"/assign.xml"):
        error_list.append("No assign.xml file")

    if not os.path.isfile(in_dir+"/categories.xml"):
        error_list.append("No categories.xml file")

def convert_performance_table(pt, prefdir):
    for alt, perfs in pt.iteritems():
        for crit, perf in perfs.iteritems():
            if prefdir[crit] == "min":
                pt[alt][crit] = -perf

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

def create_glpk_input_file(alt_id, crit_id, pt, cat_id, cat_rank, assign):
    f = tempfile.NamedTemporaryFile(delete=True)
    if not f:
        error_list.append("Impossible to create input file")
        return

    f.write("param ncat := %d;\n" % len(cat_id))
    f.write("param nalt := %d;\n" % len(alt_id))
    f.write("param ncrit := %d;\n" % len(crit_id))
    f.write("param perfs :\t")
    for i in range(len(crit_id)):
        f.write("%d\t" % (i+1))
    f.write(":=\n")
    for i in range(len(pt)):
        f.write("\t%d\t" % (i+1))
        perfs = pt[alt_id[i]]
        for j in range(len(crit_id)):
            f.write("%f\t" % perfs[crit_id[j]])
        f.write("\n")
    f.write(";\n")

    f.write("param assign :=")
    for i in range(len(alt_id)):
        f.write("[%d] %d " % ((i+1), cat_rank[assign[alt_id[i]]]))
    f.write(";\n")

    f.flush()

    return f

def glpk_solve(input_file):
    p = subprocess.Popen(["glpsol", "-m", "inf_etri_bm.mod", "-d", "%s" % input_file], stdout=subprocess.PIPE)

    output = p.communicate()
    status = p.returncode

    return (status, output[0])

def glpk_parse_output(output, crit_id):
    glpk_weigths = (output.partition("\n### Criteria weights ###\n")[2]).partition("\n### Criteria weights ###\n")[0]
    weights = glpk_weigths.split()

    glpk_profiles = (output.partition("\n### Profiles ###\n")[2]).partition("\n### Profiles ###\n")[0]
    profiles = []
    for profile in glpk_profiles.split("\n"):
        profiles.append(profile.split())

    glpk_lambda = (output.partition("### Lambda ###\n")[2]).partition("### Lambda ###\n")[0]
    lbda = glpk_lambda

    glpk_compat = (output.partition("### Compatible alternatives ###\n")[2]).partition("### Compatible alternatives ###\n")[0]
    compat = glpk_compat.split()

    print "weights", weights
    print "profiles", profiles
    print "lambda", lbda
    print "compat", compat

    if not weights:
        error_list.append("Impossible to get weights from the solver")

    if not profiles:
        error_list.append("Impossible to get profiles from the solver")

    if not lbda:
        error_list.append("Impossible to get lambda from the solver")

    if not compat:
        error_list.append("Impossible to get compatible alternatives from the solver")

    return (weights, profiles, lbda, compat)

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
    PyXMCDA.writeErrorMessages(msgfile, errors)
    msgfile.close()

def create_log_file(out_dir):
    msgfile = open(out_dir+"/messages.xml", 'w')
    PyXMCDA.writeLogMessages(msgfile, "Execution ok")
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

    xml_crit = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
    xml_alt = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
    xml_pt = PyXMCDA.parseValidate(in_dir+"/performanceTable.xml")
    xml_assign = PyXMCDA.parseValidate(in_dir+"/assign.xml")
    xml_cat = PyXMCDA.parseValidate(in_dir+"/categories.xml")

    alt_id = PyXMCDA.getAlternativesID(xml_alt)
    crit_id = PyXMCDA.getCriteriaID(xml_crit)
    pt = PyXMCDA.getPerformanceTable(xml_pt, alt_id, crit_id)
    cat_id = PyXMCDA.getCategoriesID(xml_cat)
    cat_rank = PyXMCDA.getCategoriesRank(xml_cat, cat_id)
    assign = PyXMCDA.getAlternativesAffectations(xml_assign)
    pref_dir = PyXMCDA.getCriteriaPreferenceDirections(xml_crit, crit_id)

    print 'alt  ids  ', alt_id
    print 'crit ids  ', crit_id
    print 'perfs     ', pt
    print 'categories', cat_id
    print 'affect    ', assign
    print 'pref_dir  ', pref_dir

    convert_performance_table(pt, pref_dir)
    print 'perfs     ', pt

    check_input_parameters(alt_id, crit_id, pt, cat_id, assign)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    input_file = create_glpk_input_file(alt_id, crit_id, pt, cat_id, cat_rank, assign)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    (status, output) = glpk_solve(input_file.name)
    if status:
        error_list.append("gklp returned status %d" % status);
        input_file.close()
        create_error_file(out_dir, error_list)
        return error_list

    input_file.close()

    (weights, profiles, lbda, compat) = glpk_parse_output(output, crit_id)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    out_weights = xmcda.format_criteria_weights(weights, crit_id)
    out_catprof = xmcda.format_category_profiles(profiles, crit_id, cat_id)
    out_refalts = xmcda.format_pt_reference_alternatives(profiles, crit_id)
    out_lambda = xmcda.format_lambda(lbda)
    out_compat = xmcda.format_format_compatible_alternatives(compat, alt_id)
    create_output_files(out_dir, out_weights, out_catprof, out_refalts, out_lambda, out_compat)

    create_log_file(out_dir)

if __name__ == "__main__":
    sys.exit(main())
