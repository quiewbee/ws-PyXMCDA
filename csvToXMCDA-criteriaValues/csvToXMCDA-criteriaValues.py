import csv, getopt, sys, os
from optparse import OptionParser

import PyXMCDA

def csv_reader(csv_file):
    csvfile = open(csv_file, "rb")
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    return csv.reader(csvfile, dialect)


def transform(csv_file, errorList):
    try:
        content = csv_reader(csv_file)
    except:
        errorList.append("Could not read csv file")
        return (None, None, None)
    
    try:
        criteria_ids = content.next()
    except: # StopIteration
        errorList.append("Invalid csv file (is it empty?)")
        return (None, None, None)

    try:
        weights = content.next()
    except: # StopIteration
        errorList.append("Invalid csv file (second line is missing)")
        return (None, None, None)

    criteria_ids = criteria_ids[1:]
    mcdaConcept = weights[0]
    weights = weights[1:]

    if len(criteria_ids)==0 or len(weights)==0:
        errorList.append("csv should contain at least one criteria/value")
        return (None, None, None)
    if len(criteria_ids) != len(weights):
        errorList.append("csv should contain the same number of criteria and values")
        return (None, None, None)

    return (criteria_ids, mcdaConcept, weights)

def output_criteria(filename, criteria_ids):
    outfile = open(filename, 'w')
    PyXMCDA.writeHeader(outfile)
    outfile.write('  <criteria>\n')
    for id in criteria_ids:
        outfile.write('    <criterion id="%s" />\n'%id)
    outfile.write('  </criteria>\n')
    PyXMCDA.writeFooter(outfile)
    outfile.close()
    
def output_criteriaValues(filename, criteria_ids, mcdaConcept, weights):
    outfile = open(filename, 'w')
    PyXMCDA.writeHeader(outfile)
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
    PyXMCDA.writeFooter(outfile)
    outfile.close()

def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    parser = OptionParser()
    
    parser.add_option("-i", "--in", dest="in_dir")
    parser.add_option("-o", "--out", dest="out_dir")
    
    (options, args) = parser.parse_args(argv[1:])

    in_dir = options.in_dir
    out_dir = options.out_dir

    csv_file = os.path.join(in_dir, 'criteriaValues.csv')
    out_criteria = os.path.join(out_dir, 'criteria.xml')
    out_criteriaValues = os.path.join(out_dir, 'criteriaValues.xml')

    # Creating a list for error messages
    errorList = []
    
    # If some mandatory input files are missing
    if not os.path.isfile(csv_file):
        errorList.append("input file 'criteriaValues.csv' is missing")
    
    else :
        criteria_ids, mcdaConcept, weights = transform(csv_file, errorList)
        if not errorList:
            output_criteria(out_criteria, criteria_ids)
            output_criteriaValues(out_criteriaValues, criteria_ids, mcdaConcept, weights)
    
    # Creating log and error file, messages.xml
    fileMessages = open(os.path.join(out_dir,"messages.xml"), 'w')
    PyXMCDA.writeHeader (fileMessages)
    if not errorList :
        PyXMCDA.writeLogMessages(fileMessages, ["Execution ok"])
    else :
        PyXMCDA.writeErrorMessages(fileMessages, errorList)
    PyXMCDA.writeFooter(fileMessages)
    fileMessages.close()

if __name__ == "__main__":
    sys.exit(main())
