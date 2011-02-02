def format_criteria_weights(weights):
    output = "<criteriaValues>\n"
    for crit, weight in weights.iteritems():
        output += "\t<criterionValue>\n"
        output += "\t\t<criterionID>%s</criterionID>\n" % crit
        output += "\t\t<value><real>%s</real></value>\n" % weight
        output += "\t</criterionValue>\n"
    output += "</criteriaValues>\n"
    return output

def format_category_profiles(profiles, palts_id, cat_id):
    output = "<categoriesProfiles>\n"
    for i, profile in enumerate(profiles):
        output += "\t<categoryProfile>\n"
        output += "\t\t<alternativeID>%s</alternativeID>\n" % palts_id[i]
        output += "\t\t<limits>\n"
        output += "\t\t\t<lowerCategory><categoryID>%s</categoryID></lowerCategory>\n" % cat_id[i]
        output += "\t\t\t<upperCategory><categoryID>%s</categoryID></upperCategory>\n" % cat_id[i+1]
        output += "\t\t</limits>\n"
        output += "\t</categoryProfile>\n"
    output += "</categoriesProfiles>\n"
    return output

def format_pt_reference_alternatives(profiles, palts_id, crit_id):
    output = "<performanceTable>\n"
    output += "\t<description>\n"
    output += "\t\t<title>Performance table of reference alternatives</title>\n"
    output += "\t</description>\n"
    for i, profile in enumerate(profiles):
        output += "\t<alternativePerformances>\n"
        output += "\t\t<alternativeID>%s</alternativeID>\n" % palts_id[i]
        for j, crit in enumerate(crit_id): 
            output += "\t\t<performance>\n"
            output += "\t\t\t<criterionID>%s</criterionID>\n" % crit
            output += "\t\t\t<value><real>%s</real></value>\n" % profile['refs'][crit]
            output += "\t\t</performance>\n"
        output += "\t</alternativePerformances>\n"

    output += "</performanceTable>\n"
    return output

def format_lambda(lbda):
    output = "<methodParameters>\n"
    output += "\t<parameter name=\"lambda\">\n"
    output += "\t\t<value><real>%s</real></value>\n" % lbda
    output += "\t</parameter>\n"
    output += "</methodParameters>\n"
    return output

def format_format_compatible_alternatives(compat, alts_id):
    output = "<alternatives>\n"
    output += "\t<description>\n"
    output += "\t\t<title>Compatible alternatives</title>\n"
    output += "\t</description>\n"
    for i, compatible in enumerate(compat):
        if compatible == 0:
            continue

        output += "\t<alternative id=\"%s\">\n" % alts_id[i]
        output += "\t\t<active>true</active>\n"
        output += "\t</alternative>\n"
    output += "</alternatives>\n"
    return output

def add_xmcda_tags(xml_data):
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '<?xml-stylesheet type="text/xsl" href="xmcdaXSL.xsl"?>\n'
    output += '<xmcda:XMCDA xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.decision-deck.org/2009/XMCDA-2.0.0 file:../XMCDA-2.0.0.xsd" xmlns:xmcda="http://www.decision-deck.org/2009/XMCDA-2.0.0" instanceID="void">\n'
    output += xml_data
    output += "</xmcda:XMCDA>\n"
    return output

def get_lambda(xmltree):
    xml_lbda = xmltree.find(".//methodParameters/parameter/value/real")
    return float(xml_lbda.text)
