def format_criteria_weights(weights, crit_id):
    output = "<criteriaValues>\n"
    for i, crit in enumerate(crit_id):
        output += "\t<criterionValue>\n"
        output += "\t\t<criterionID>%s</criterionID>\n" % crit
        output += "\t\t<value><real>%s</real></value>\n" % weights[i]
        output += "\t</criterionValue>\n"
    output += "</criteriaValues>\n"
    return output

def format_category_profiles(profiles, crit_id, cat_id):
    output = "<categoriesProfiles>\n"
    for i, profile in enumerate(profiles):
        if i == 0 or i == len(profiles)-1:
            continue

        output += "\t<categoryProfile>\n"
        output += "\t\t<alternativeID>b%d</alternativeID>\n" % i
        output += "\t\t<limits>\n"
        output += "\t\t\t<lowerCategory><categoryID>%s</categoryID></lowerCategory>\n" % cat_id[i-1]
        output += "\t\t\t<upperCategory><categoryID>%s</categoryID></upperCategory>\n" % cat_id[i]
        output += "\t\t</limits>\n"
        output += "\t</categoryProfile>\n"
    output += "</categoriesProfiles>\n"
    return output

def format_pt_reference_alternatives(profiles, crit_id):
    output = "<performanceTable>\n"
    output += "\t<description>Performance table of reference alternatives</description>\n"
    for i, profile in enumerate(profiles):
        if i == 0 or i == len(profiles)-1:
            continue

        output += "\t<alternativePerformances>\n"
        output += "\t\t<alternativeID>b%d</alternativeID>\n" % i
        for j, crit in enumerate(crit_id): 
            output += "\t\t<performance>\n"
            output += "\t\t\t<criterionID>%s</criterionID>\n" % crit
            output += "\t\t\t<value><real>%s</real></value>\n" % profile[j]
            output += "\t\t</performance>\n"
        output += "\t</alternativePerformances>\n"

    output += "<performanceTable>\n"
    return output

def format_lambda(lbda):
    output = "<methodParameters>\n"
    output += "\t<parameter>\n"
    output += "\t\t<value><real>%s</real></value>\n" % lbda
    output += "\t</parameter>\n"
    output += "</methodParameters>\n"
    return output

def format_format_compatible_alternatives(compat, alts_id):
    output = "<alternatives>\n"
    output += "\t<description>Compatible alternatives</description>\n"
    for i, compatible in enumerate(compat):
        if compatible == 0:
            continue

        output += "\t<alternative id=%s>\n" % alts_id[i]
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
