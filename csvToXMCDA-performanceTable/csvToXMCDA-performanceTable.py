#! /usr/bin/env python2.7
'''
Transforms a file containing a performance tablec from a comma-separated values (CSV) file ...'''
import argparse, csv, sys, os
from optparse import OptionParser

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


def string_to_numeric_list(alist):
    """
    Check that the list is made of numeric values only.  If the values in the
    list are not valid numeric values, it also tries to interpret them with
    the comma character (",") as the decimal separator.  This may happen when
    the csv is exported by MS Excel on Windows platforms, where the csv format
    depends on the local settings.

    Note that we do not check whether the decimal separator is the same
    everywhere: a list containing "4.5" and "5,7" will be accepted.

    Return the list filled with the corresponding float values, or raise
    ValueError if at least one value could not be interpreted as a numeric
    value.
    """
    l = None
    try:
        l = [ float(i) for i in alist ]
    except ValueError:
        pass
    else:
        return l
    # try with ',' as a comma separator
    try:
        l = [ float(i.replace(',', '.')) for i in alist ]
    except ValueError:
        raise ValueError, "Invalid literal for float"
    else:
        return l


def transform(csv_file):
    try:
        content = csv_reader(csv_file)
    except Exception as e:
        raise ValueError, 'Could not read csv file, reason: '+e.message
    
    try:
        criteria_ids = content.next()
    except StopIteration:
        raise ValueError, 'Invalid csv file (is it empty?)'

    criteria_ids = criteria_ids[1:]
    if len(criteria_ids)==0:
        raise ValueError, 'csv should contain at least one criteria'

    alternatives_ids = []
    performanceTable = []
    expected_len = len(criteria_ids) + 1

    for values in content:
        if len(values) != expected_len:
            raise ValueError, 'Invalid csv file (all lines should have the same number of elements)'
        alternatives_ids.append(values[0])
        try:
            values = string_to_numeric_list(values[1:])
        except ValueError:
            raise ValueError, 'performance table should contain numeric values only'
        performanceTable.append(values)

    if len(alternatives_ids)==0:
        raise ValueError, 'csv should contain at least one alternative'
    return alternatives_ids, criteria_ids, performanceTable


def output_alternatives(filename, alternatives_ids):
    outfile = open(filename, 'w')
    xmcda_write_header(outfile)
    outfile.write('  <alternatives>\n')
    for id in alternatives_ids:
        outfile.write('    <alternative id="%s">\n      <active>true</active>\n    </alternative>\n'%id)
    outfile.write('  </alternatives>\n')
    xmcda_write_footer(outfile)
    outfile.close()


def output_criteria(filename, criteria_ids):
    outfile = open(filename, 'w')
    xmcda_write_header(outfile)
    outfile.write('  <criteria>\n')
    for id in criteria_ids:
        outfile.write('    <criterion id="%s">\n      <active>true</active>\n    </criterion>\n'%id)
    outfile.write('  </criteria>\n')
    xmcda_write_footer(outfile)
    outfile.close()


def output_performanceTable(filename,
                            alternatives_ids, criteria_ids, performanceTable):
    outfile = open(filename, 'w')
    xmcda_write_header(outfile)
    outfile.write('<performanceTable>\n')
    for alt_id, values in map(None, alternatives_ids, performanceTable):
        outfile.write('  <alternativePerformances>\n');
        outfile.write('    <alternativeID>%s</alternativeID>\n'%alt_id);
        for crit_id, value in map(None, criteria_ids, values):
            outfile.write('''      <performance>
        <criterionID>%s</criterionID>
        <value>
          <real>%s</real>
        </value>
      </performance>
'''%(crit_id, value));
        outfile.write('  </alternativePerformances>\n');

    outfile.write('</performanceTable>\n')
    xmcda_write_footer(outfile)
    outfile.close()


def csv_to_performanceTable(csv_file,
                            out_alternatives, out_criteria, out_perfTable):
    # If some mandatory input files are missing
    if not os.path.isfile(csv_file):
        raise ValueError, "input file '%s' is missing"%csv_file
    alternatives_ids, criteria_ids, performanceTable = transform(csv_file)
    output_alternatives(out_alternatives, alternatives_ids)
    output_criteria(out_criteria, criteria_ids)
    output_performanceTable(out_perfTable,
							alternatives_ids, criteria_ids, performanceTable)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    parser = argparse.ArgumentParser(description=__doc__)

    grp_input = parser.add_mutually_exclusive_group(required=True)
    grp_input.add_argument('-I', '--in-dir')
    grp_input.add_argument('-i', '--csv')

    grp_output = parser.add_argument_group("Outputs",
                                           description="Options -c and -C are linked and should be supplied (or omitted) together.  They are mutually exclusive with option -O")
    grp_output.add_argument('-O', '--out-dir', metavar='<output directory>', help='If specified, the files "criteria.xml" and "criteriaValues.xml" will be created in this directory.  The directory must exist beforehand.')
    grp_output.add_argument('-a', '--alternatives', metavar='output.xml')
    grp_output.add_argument('-c', '--criteria', metavar='output.xml')
    grp_output.add_argument('-p', '--perfTable', metavar='output.xml')

    grp_output.add_argument('-m', '--messages', metavar='<file.xml>', help='All messages are redirected to this XMCDA file instead of being sent to stdout or stderr.  Note that if an output directory is specified (option -O), the path is relative to this directory.')

    args = parser.parse_args()
    #in_dir = options.in_dir
    #out_dir = options.out_dir
    if args.out_dir and (args.alternatives or args.criteria or args.perfTable):
        parser.error('Options -O and -p/-a/-p are mutually exclusive')
    if args.criteria != args.perfTable \
        and None in (args.alternatives, args.criteria, args.perfTable):
        parser.error('Options -a, -c and -P must be supplied (or omitted) together')

    if args.in_dir:
        csv_file = os.path.join(args.in_dir, 'performanceTable.csv')
    else:
        csv_file = args.csv

    if args.out_dir:
        out_alternatives = os.path.join(args.out_dir, 'alternatives.xml')
        out_criteria     = os.path.join(args.out_dir, 'criteria.xml')
        out_perfTable    = os.path.join(args.out_dir, 'performanceTable.xml')
    else:
        out_criteria = args.criteria
        out_criteriaValues = args.criteriaValues

    if args.messages and args.out_dir is not None:
        args.messages = os.path.join(args.out_dir, args.messages)

    if args.messages:
        args.messages_fd = open(args.messages, 'w')
        xmcda_write_header(args.messages_fd)

    exitStatus = 0
    try:
        csv_to_performanceTable(csv_file,
                                out_alternatives, out_criteria, out_perfTable)
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
