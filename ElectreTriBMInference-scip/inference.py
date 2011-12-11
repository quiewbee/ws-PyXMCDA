import os
import sys
import logging
from optparse import OptionParser
from xml.etree import ElementTree

from mcda.types import performance_table
from mcda.types import alternatives
from mcda.types import criteria
from mcda.types import alternatives_affectations
from mcda.types import categories
from model import leroy_linear_problem

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

def xml_get_root(fname, tag):
    tree = ElementTree.parse(fname)
    root = tree.getroot()
    return root.find(tag)

def parse_xmcda_files(in_dir):
    pt = performance_table()
    root = xml_get_root(in_dir+'/perfs_table.xml', 'performanceTable')
    try:
        pt.from_xmcda(root)
    except:
        error_list.append("Cannot parse perfs_table.xml")

    a = alternatives()
    root = xml_get_root(in_dir+'/alternatives.xml', 'alternatives')
    try:
        a.from_xmcda(root)
    except:
        error_list.append("Cannot parse alternatives.xml")

    c = criteria()
    root = xml_get_root(in_dir+'/criteria.xml', 'criteria')
    try:
        c.from_xmcda(root)
    except:
        error_list.append("Cannot parse criteria.xml")

    af = alternatives_affectations()
    root = xml_get_root(in_dir+'/assign.xml', 'alternativesAffectations')
    try:
        af.from_xmcda(root)
    except:
        error_list.append("Cannot parse assign.xml")

    cat = categories()
    root = xml_get_root(in_dir+'/categories.xml', 'categories')
    try:
        cat.from_xmcda(root)
    except:
        error_list.append('Cannot parse categories.xml')

    return a, c, pt, af, cat

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

    # Parsing and checking input 
    (in_dir, out_dir) = parse_cmdline(argv)
    if error_list:
        return error_list

    check_input_files(in_dir)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    a, c, pt, af, cat = parse_xmcda_files(in_dir)
    if error_list:
        create_error_file(out_dir, error_list)
        return error_list

    model = leroy_linear_problem(a, c, pt, af, cat)
    model.solve()

if __name__ == "__main__":
    sys.exit(main())
