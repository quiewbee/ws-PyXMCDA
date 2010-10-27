import os
import sys
import getopt
import subprocess
import tempfile
from optparse import OptionParser

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

    if not os.path.isfile(in_dir+"/perfs_table.xml"):
        error_list.append("No perfs_table.xml file") 

    if not os.path.isfile(in_dir+"/assign.xml"):
        error_list.append("No assign.xml file")

    if not os.path.isfile(in_dir+"/categories.xml"):
        error_list.append("No categories.xml file")

def check_input_parameters(alt_id, crit_id, pt, cat, assign):
    if not alt_id:
        error_list.append("The alternatives file can't be validated.")
    if not crit_id:
        error_list.append("The criteria file can't be validated.")
    if not pt:
        error_list.append("The performance table file can't be validated.")
    if not cat:
        error_list.append("The categories file can't be validated.")
    if not assign:
        error_list.append("The assign file can't be validated.")

def create_glpk_input_file(alt_id, crit_id, pt, cat, assign):
    f = tempfile.NamedTemporaryFile(delete=False)
    if not f:
        error_list.append("Impossible to create input file")
        return

    f.write("param ncat := %d;\n" % len(cat))
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
        f.write("[%d] %d " % ((i+1), cat.index((assign[alt_id[i]]))+1))
    f.write(";\n")

    return f.name

def glpk_solve(input_file):
    f = tempfile.NamedTemporaryFile(delete=False)
    if not f:
        error_list.append("Impossible to create output file")
        return

    output_file = f.name

    subprocess.Popen(["glpsol", "-m", "inf_etri_bm.mod", "-d", "%s" % input_file])
#    subprocess.Popen("-m inf_etri_bm.mod -d %s -o %s" % (input_file, output_file), executable="/usr/bin/glpsol")

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Parsing of the options
    (in_dir, out_dir) = parse_cmdline(argv)
    if error_list:
        return error_list

    check_input_files(in_dir)
    if error_list:
        return error_list

    xml_crit = PyXMCDA.parseValidate(in_dir+"/criteria.xml")
    xml_alt = PyXMCDA.parseValidate(in_dir+"/alternatives.xml")
    xml_pt = PyXMCDA.parseValidate(in_dir+"/perfs_table.xml")
    xml_assign = PyXMCDA.parseValidate(in_dir+"/assign.xml")
    xml_cat = PyXMCDA.parseValidate(in_dir+"/categories.xml")

    alt_id = PyXMCDA.getAlternativesID(xml_alt)
    crit_id = PyXMCDA.getCriteriaID(xml_crit)
    pt = PyXMCDA.getPerformanceTable(xml_pt, alt_id, crit_id)
    cat = PyXMCDA.getCategoriesID(xml_cat)
    assign = PyXMCDA.getAlternativesAffectation(xml_assign)
    print 'alt  ids  ', alt_id
    print 'crit ids  ', crit_id
    print 'perfs     ', pt
    print 'categories', cat
    print 'affect    ', assign
    check_input_parameters(alt_id, crit_id, pt, cat, assign)
    if error_list:
        return error_list

    input_file = create_glpk_input_file(alt_id, crit_id, pt, cat, assign)
    if error_list:
        return error_list

    glpk_solve(input_file)

if __name__ == "__main__":
    sys.exit(main())
