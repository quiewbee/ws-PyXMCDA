#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
# genericRequest.py
# Sébastien Bigaret, February 2009
# adapted from a script by Raymond Bisdorff, April 2008
########################
"""
Usage: genericRequest.py -n <service's name> [options] [command] [arguments]

Commands:

  -s, --submit-problem                submit a problem (see below);
                                      a ticket-id is printed on the standard
                                      output
  -g, --request-solution <ticket-id>  request the solution corresponding to
      --get-solution                  this ticket. The solution is written in
                                      the file 'kappalabSolution.xml', unless
                                      option '-' is given (see below)

  -S, --submit-and-wait-solution      submit a problem (see below), and waits
                                      for the solution. The solution is
                                      written on the disk the same way as
                                      for option -g

Options:
  -U, --url                    Specify an alternate url for accesing than the
                               default.
                               Default is:
                               http://webservices.decision-deck.org/soap/%s.py

                               You can specify either a string like the default
                               one, using '%s' which will be replaced by the
                               service's name, or a regular, plain url.

  -n <service's name>          It is mandatory if -U is not supplied.

  -v, --verbose                increase verbosity
  -t, --timeout <seconds>      wait for a solution during <seconds> seconds
                               at most, then exit if no solution was found.
                               Use zero (0) to disable the timeout.
                               Defaults to 60 seconds.
  (-h) --help                  show this help (-h works with no other options)

Arguments:  a list of <parameter_name>:<file_path>, separated by whitespaces

  For example, if you want to supply the file 'my_criteria.xml' as input
  to the parameter 'criteria', the argument is:

    criteria:my_criteria.ml

Exit status:

  0  no problem
  1  usage error
  2  timed out while waiting for a solution (with commands -g and -S)
  
"""
import getopt, sys, time
from StringIO import StringIO
from xml.etree import ElementTree as ET
#this was the old one, kept here a moment just in case
#ET._namespace_map['http://www.decision-deck.org/2008/UMCDA-ML-1.0']='xmcda'
ET._namespace_map['http://www.decision-deck.org/2009/XMCDA-2.0.0']='xmcda'
ET._namespace_map['http://www.w3.org/2001/XMLSchema-instance']='xsi'

from ZSI.client import NamedParamBinding

#service_url='http://ernst-schroeder.uni.lu/cgi-bin/%s.py'
#default_service_url='http://ddeck.lgi.ecp.fr/cgi-bin/%s.py'
default_service_url='http://webservices.decision-deck.org/soap/%s.py'
service_url=default_service_url

verbose = 0

def log(msg):
    if verbose:
        print >>sys.stderr, msg
def debug(msg):
    if verbose>1:
        print >>sys.stderr, msg

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

#from utils import prettyprint
#inlined utils.indent & prettyprint, so this script is executable as-is
def indent(elem, level=0):
    """
    Adds whitespace to the tree, so that saving it as usual results in a
    prettyprinted tree.
    Written by Fredrik Lundh, http://effbot.org/zone/element-lib.htm
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        
        #for elem in elem:
        #    indent(elem, level+1)
        #if not elem.tail or not elem.tail.strip():
        #    elem.tail = i
        
        for child in elem:
            indent(child, level+1)
        if not child.tail or not child.tail.strip():
            child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def prettyprint(root, file, encoding='us-ascii'):
  indent(root.getroot())
  root.write(file, encoding)

def submitProblem(url, problem, params):
    debug("entering submitProblem()\n")

    host=url.split('/')[2]
    
    debug("building NamedParamBinding, host:%s, url: %s\n"%(host, url))
    debug(params.keys())
    service = NamedParamBinding(host=host,
                                port=80,
                                url=url,
                                tracefile=verbose>2 and sys.stderr or None)
    
    log(service.hello()['message'].encode('UTF-8'))
    
    debug("submitting problem\n")
    sp = service.submitProblem(**params)
    debug(sp['message']+"\n")
    log("Return Ticket: "+sp['ticket'])
    return sp['ticket']

def requestSolution(url, ticket_id, timeout=0):
    host=url.split('/')[2]

    service = NamedParamBinding(host=host,
                                port=80,
                                url=url,
                                tracefile=verbose>2 and sys.stderr or None)
  
    log("Request solution for problem %s" % (ticket_id))
    
    start = time.time()
    while True:
        answer = service.requestSolution(ticket=ticket_id)
        if answer['service-status'] != 1: # NOT AVAILABLE
            break;
        time.sleep(0.5)
        if timeout and time.time()>start+timeout:
            log('timeout: solution not available after %i seconds: exiting'%timeout)
            return None

    filenames = []

    debug('Got the following keys in the answer: '+', '.join(answer.keys()))
    for k,v in answer.items():
        if k in ('ticket', 'service-status'):
            continue

        xml = None
        try:
            xml = ET.ElementTree(ET.fromstring(v))
        except Exception, e:
            log('Unable to parse answer for key: %s, writing raw file'%k)
            debug('Answer for key %s was: "%s"'%(k,v))
            filename = k
        else:
            filename = k+'.xml'
        
        if xml:
            # re-read it to prettyprint it
            prettyprint(xml, filename, 'utf-8')
        else:
            f=open(filename, 'w')
            f.write(v)
            f.close()

        #import codecs
        #fileOUT = codecs.open(filename,'w',encoding='utf-8')
        #fileOUT.write(answer['solution'])
        log('Wrote file:%s'%filename)
        filenames.append(filename)
    return filenames

def main(argv=None):
    global verbose, service_url
    
    if argv is None:
        argv = sys.argv

    # problem is True or False while parsing arguments.
    # When -s/-S is supplied, problem contains the string representation (xml)
    # of the problem
    problem=False
    ticket=None
    service_name=None
    timeout=60
    
    method_data_params = []
    try:

        #if len(argv)<3:
        #    if len(argv)==2 and argv[1] in ('-h', '--help'):
        #        print __doc__
        #        return 0
        #    raise Usage("Missing service and/or command")
        try:
            opts, args = getopt.getopt(sys.argv[1:],
                                       "n:hvsg:St:M:U:",
                                       ['service-name',
                                        'help',
                                        'verbose',
                                        'submit-problem',
                                        'request-solution=', 'get-solution=',
                                        'submit-and-wait-solution',
                                        'timeout=',
                                        'add-method-data-parameter=',
                                        'url=',
                                        ])
        except getopt.error, msg:
            raise Usage(msg)
        # process options
        for opt, arg in opts:
            if opt in ("-n", "--service-name"):
                service_name=arg
            if opt in ("-h", "--help"):
                print __doc__
                return 0
            if opt in ('-v', '--verbose'):
                verbose += 1
            if opt in ('-s', '--submit-problem'):
                problem=True
            if opt in ('-g', '--request-solution', '--get-solution'):
                ticket=arg
            if opt in ('-S', '--submit-and-wait-solution'):
                problem=True
                ticket=-1
            if opt in ('-t', '--timeout'):
                try:
                    timeout=int(arg)
                except ValueError, err:
                    timeout=-1
                if timeout<0:
                    raise Usage('timeout value should be a valid, positive or null integer')
            if opt in ('-M', '--add-method-data-parameter'):
                method_data_params.append(arg)

            if opt in ('-U', '--url='):
                service_url=arg

        # check the URL is plain, or that the service's name is supplied
        if service_name is None and service_url is None:
            raise Usage("Both service's name and url are not supplied")
        if service_url == default_service_url and service_name is None:
            raise Usage("The service's name should be supplied when no URL is provided")
            
        if service_name is not None:
          try:
              service_url = service_url%service_name
          except TypeError:
              pass
        if not problem and not ticket:
            raise Usage("")

        debug("Using url: %s"%service_url)
        params = {}
        if problem:
            for arg in args:
                k,v=arg.split(':',1) #TODO check ValueError
                fileIN = open(v,'r')
                content = fileIN.read()
                params[k] = content
                fileIN.close()
            if not params:
                #raise Usage("Options -s/-S require that at least one argument")
                # a service may have reasonable default values for all of
                # its parameters (services randomly generating data e.g.)
                pass
                
            #problem = insert_data_params(problem, method_data_params)
            
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 1
    
    if problem:
        ticketNb = submitProblem(service_url, problem, params)
        print ticketNb
        if ticket==-1:
            ticket=ticketNb

    if ticket:
        ##ticket=sys.stdin.readline()
        ##if not ticket:
        ##    sys.stderr.write("no ticket id, either on the commandline or in stdin")
        files = requestSolution(service_url, ticket, timeout)
        if not files:
            return 2
        for file in files:
            print file
        
if __name__ == "__main__":
    sys.exit(main())

