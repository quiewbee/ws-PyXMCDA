#! /usr/bin/env python2.7
'''
Transforms a file containing criteria discrimination thresholds and preference directions from a comma-separated values (CSV) file to an XMCDA compliant file, containing the criteria ids with their preference direction and related discrimination thresholds.
'''
import argparse, csv, sys, os

# not using PyXMCDA, to avoid the unnecessary dependency to lxml
def xmcda_write_header(xmlfile) :
    xmlfile.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    xmlfile.write("<xmcda:XMCDA xmlns:xmcda='http://www.decision-deck.org/2009/XMCDA-2.1.0' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:schemaLocation='http://www.decision-deck.org/2009/XMCDA-2.1.0 http://www.decision-deck.org/xmcda/_downloads/XMCDA-2.1.0.xsd'>\n")


def xmcda_write_footer(xmlfile) :
    xmlfile.write("</xmcda:XMCDA>\n")


def xmcda_write_method_messages(xmlfile, type, messages) :
    if type not in ('log', 'error'):
        raise ValueError, 'Invalid type: %s' % type
    xmlfile.write('<methodMessages>\n')
    for message in messages :
        xmlfile.write('<%sMessage><text><![CDATA[%s]]></text></%sMessage>\n' % (type, message, type))
    xmlfile.write('</methodMessages>\n')


def csv_reader(csv_file):
    csvfile = open(csv_file, "rb")
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    return csv.reader(csvfile, dialect)


def transform(csv_file, errorList):
    try:
        content = csv_reader(csv_file)
    except:
        raise ValueError, 'Could not read csv file'

    try:
        criteria_ids = content.next()
    except StopIIteration:
        raise ValueError, 'Invalid csv file (is it empty?)'

    thresholds_list = []
    for line in content:
        thresholds_list.append(line)
        if len(line) != len(criteria_ids):
            raise ValueError, 'Invalid csv file: all lines should have the same number of elements'
            
    if len(thresholds_list) <= 2:
        raise ValueError, 'Invalid csv file, at least 3 lines are required'

    criteria_ids = criteria_ids[1:]
    preferenceDirections = thresholds_list[-1]
    thresholds_list=thresholds_list[:-1]

    if preferenceDirections[0] != 'preferenceDirection':
        raise ValueError, "Invalid csv file: last line must start with 'preferenceDirection'"
    preferenceDirections = preferenceDirections[1:]

    thresholds_per_criteria = []
    for i in range(len(criteria_ids)):
        thresholds_per_criteria.append([])

    try:
        for thresholds in thresholds_list:
          mcdaConcept=thresholds[0]
          thresholds=thresholds[1:]
          for i in range(len(criteria_ids)):
            thresholds_per_criteria[i].append((mcdaConcept, float(thresholds[i])))
    except ValueError:
        raise ValueError, 'Invalid csv file: thresholds should be floats'

    return criteria_ids, preferenceDirections, thresholds_per_criteria


xmcda_scale='''
            <scale>
                <quantitative>
                    <preferenceDirection>%s</preferenceDirection>
                </quantitative>
            </scale>
'''

xmcda_threshold='''
                <threshold mcdaConcept="%s">
                    <constant>
                        <real>%s</real>
                    </constant>
                </threshold>
'''

def output_criteria(filename, criteria_ids, preferenceDirections, thresholds_list):
    outfile = open(filename, 'w')
    xmcda_write_header(outfile)
    outfile.write('    <criteria>\n')
    for i in range(len(criteria_ids)):
        id, prefDir, thresholds = (criteria_ids[i], preferenceDirections[i], thresholds_list[i])
        outfile.write('        <criterion id="%s">'%id)
        outfile.write(xmcda_scale % prefDir)
        outfile.write('            <thresholds>')
        for mcdaConcept, threshold in thresholds:
            outfile.write(xmcda_threshold % (mcdaConcept, threshold))
        outfile.write('            </thresholds>')
        outfile.write('\n        </criterion>\n')

    outfile.write('    </criteria>\n')
    xmcda_write_footer(outfile)
    outfile.close()

def output_criteriaValues(filename, criteria_ids, mcdaConcept, weights):
    outfile = open(filename, 'w')
    PyXMCDA.xmcda_write_header(outfile)
    outfile.write('  <criteriaValues mcdaConcept="%s">'%mcdaConcept)
    for id, weight in map(None,criteria_ids, weights):
        outfile.write("""
    <criterionValue>
      <criterionID>%s</criterionID>
      <value>
        <real>%s</real>
      </value>
    </criterionValue>
"""%(id, weight))
    outfile.write('  </criteriaValues>\n')
    PyXMCDA.xmcda_write_footer(outfile)
    outfile.close()

def csv_to_criteriaThresholds(csv_file, out_criteria):
    # If some mandatory input files are missing
    if not os.path.isfile(csv_file):
        raise ValueError, 'input file "%s" is missing'%csv_file

    criteria_ids, mcdaConcept, thresholds = transform(csv_file, out_criteria)
    output_criteria(out_criteria, criteria_ids, mcdaConcept, thresholds)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description=__doc__)

    grp_input = parser.add_mutually_exclusive_group(required=True)
    grp_input.add_argument('-I', '--in-dir')
    grp_input.add_argument('-i', '--csv')

    grp_output = parser.add_mutually_exclusive_group(required=True)
    grp_output.add_argument('-O', '--out-dir', metavar='<output directory>', help='If specified, the file "criteria.xml" will be created in this directory.  The directory must exist beforehand.')
    grp_output.add_argument('-o', '--thresholds', metavar='output.xml')

    parser.add_argument('-m', '--messages', metavar='<file.xml>', help='All messages are redirected to this XMCDA file instead of being sent to stdout or stderr.  Note that if an output directory is specified (option -O), the path is relative to this directory.')

    args = parser.parse_args()

    csv_file = os.path.join(args.in_dir, 'thresholds.csv') if args.in_dir is not None else args.csv
    out_criteria = os.path.join(args.out_dir, 'criteria.xml') if args.out_dir is not None else args.thresholds
    if args.messages and args.out_dir is not None:
        args.messages = os.path.join(args.out_dir, args.messages)

    if args.messages:
        args.messages_fd = open(args.messages, 'w')
        xmcda_write_header(args.messages_fd)

    exitStatus = 0
    try:
        csv_to_criteriaThresholds(csv_file, out_criteria)
    except ValueError as e:
        exitStatus = -1
        if args.messages:
            xmcda_write_method_messages(args.messages_fd, 'error', [e.message])
        else:
            sys.stderr.write(e.message)
    else:
       if args.messages: xmcda_write_method_messages(args.messages_fd, 'log', ['Execution ok'])
    finally:
        if args.messages:
            xmcda_write_footer(args.messages_fd)
            args.messages_fd.close()

    return exitStatus

if __name__ == "__main__":
    sys.exit(main())
