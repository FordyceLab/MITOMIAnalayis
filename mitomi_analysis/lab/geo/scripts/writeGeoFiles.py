#!/usr/local/bin/python2.2

#########################################################
#  writeGeoFiles.py
#  --------------------
#  Prepares a geo family submission file for a set of arrays.
#  Reads in the array ids from an input file and also reads the
#  platform, sample, and series headers from files.
#  Input file format example:
#          ARRAYS
#          array_id
#          [...]         
#          EXPERIMENTS
#          experiment_name
#          [...]
#          PROJECTS
#          project_name
#          [...]
#      Input types can be in any order. If no input type is provided,
#      ARRAYS is assumed.
#
#  If a platform_header_filename is not passed in then the platform
#  file will not be added to the family and the samples
#  will reference the given platform ID.
#
#  Authors: Michelle and Kael
#  Latest Revision: February, 2007
#########################################################

import sys
import os
from lab.geo import NCBI
from getopt import getopt

####  String Constants
ARRAYS_INPUT = "ARRAYS"
EXPERIMENTS_INPUT = "EXPERIMENTS"
PROJECTS_INPUT = "PROJECTS"

FAMILY_REQUIRED_PARAMS = ["-g", "-a", "-r", "-s", "-e", "-o"]
PLATFORM_REQUIRED_PARAMS = ["-g", "-a", "-q", "-p", "-o"]


class InputFormatException (Exception):
    pass

class DifferentPlatformsException (Exception):
    pass

def usage(scriptName):
    return """Usage: %s [options]

Description:
    This script creates a GEO family file for submission of 
    array data from Nomad.  For more details on the GEO file
    format created see: 
    http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html
    This script creates files in the SOFT format.

Using the script:
    1.  Create the default template files by running this script
       with the "-t" option.  Four files will be created:
    \ta.  platform_template.txt
    \tb.  sample_template.txt
    \tc.  series_template.txt
    \td.  arrayids.txt
    2.  Open up the template files and fill out the fields you
    \twant to include in your submission file.  See the GEO page
    \tabove for information on which fields are required.
    \t-- The arrayids.txt file contains the array ids, experiment ids,
    \t   and/or project ids for the arrays you are submitting to GEO.
    \t   This should be filled out to contain the Nomad ids.
    \t-- If you are using an existing platform (the array design
    \t   has already been submitted to GEO), you can ignore the
    \t   platform file but you need to look up the Platform ID of
    \t   the existing platform.
    \t-- The files contain instructions on how to use them.
    4.  Run the script to generate a test copy of the GEO files.  For example:
    \tpython writeGeoFiles.py -g malaria -a arrayids.txt -m my_sample.txt -s my_series.txt -o my_output.txt -p MY_PLATFORM_ID -e MY_SERIES_ID -l 5
    5.  Look through the output file you created and verify it 
       looks accurante.
    6.  Run the script to generate the GEO files.  This would be exactly the same
    \tcommand as in step 4, but without the "-l" flag.

Modes:
    * Help: use -h flag
    * Create template files, use -t flag
    * Create Platform files, use "-m Platform".  Required Parameters: -g, -a, -q, -p, -o
    * Create Family file (combines both samples and series, with optional platform file), use "-m Family".  Required Parameters: -g, -a, (-d OR both -q and -p), -s, -r, -e, -o

Parameters:
    -h\tPrint this message
    -t\tCreate the template files
    -g\tGene Type on the array ("malaria" or "virochip")
    -a\tArray IDs file name
    -q\tPlatform ID (existing GEO Platform ID or new) (optional)
    -d\tExisting platform file (optional -- either -d or -q flag must be used)
    -p\tPlatform template file name (optional)
    -s\tSample template file name
    -r\tSeries templatefile name
    -e\tSeries ID
    -o\tOutput file name
    -l\tMax number of lines per data table.  Used for debugging. (optional)

Examples:
    To create a test file with only 5 lines of each data file using an 
    existing platform id:
    %s -m Family -l 5 -g malaria -a arrayids.txt -s my_sample.txt -r my_series.txt -q MY_PLATFORM_ID -e MY_SERIES_ID -o output.txt

    To create the full family file, including a platform:
    %s -m Family -g malaria -a arrayids.txt -p my_platform.txt -s my_sample.txt -r my_series.txt -q MY_PLATFORM_ID -e MY_SERIES_ID -o output.txt


A Note on Platforms:
    There are two main options as far as the Platform.  Either you are using an existing platform
    or you are creating a new platform.  The platform describes the design of the array -- which
    oligos relate to which genes from which species.  If your oligo design has been used for a previous
    GEO submission (for example, for most of the virochip projects), then you probably have an existing
    platform you can use.  If your array design is unique to your project or you are the first to submit
    a project for this array, then you will have to generate a platform file.

    To generate a platform file, use the "-p" flag to specify a template file for your platform.  You 
    still need to use the "-q" flag also with the name you have chosen to give your platform.

    To use an existing platform, there are two options:  either your platform has unique ids that can
    be generated from a spot record on nomad or not.  If your platform unique ids can be generated from
    the spot record (this will generally be true for malaria arrays), then you just need to use the
    "-q" flag with the existing platform id and you are done.  If your platform unique ids cannot be
    generated from the spot record (or if you are not sure), you must specify the file containing the
    existing platform.  These can be downloaded from the GEO website.  Save the existing platform file
    and then specify this file using the "-d" flag on the command line.

    When creating a platform file, the first array in the array ids file will be used as the template
    for the platform.
    """ % (scriptName, scriptName, scriptName)


def main(argv=sys.argv):

    try:
        optlist, args = getopt(argv[1:], "hl:tg:a:m:r:s:p:q:e:o:d:")
    except:
        doPrint("FAILED PARSING")
        doPrint(usage(argv[0]))
        sys.exit(1)

    # set the defaults and declare every variable
    numLines = NCBI.ALL_LINES
    array_ids = None
    geneType = None
    sam_file = None
    ser_file = None
    p_file = None
    p_id = None
    series_id = None
    out_file = None
    existing_platform = None
    mode = None

    usedParams = []

    for (opt, opt_arg) in optlist:
        if opt == '-h':
            doPrint("") 
            doPrint(usage(argv[0]))
            sys.exit(1)
        elif opt == '-t':
            dumpTemplateFiles()
            sys.exit(0)
        elif opt == '-m':
            mode = opt_arg
        elif opt == '-l':
            numLines = int(opt_arg)
        elif opt == '-g':
            geneType = opt_arg
            usedParams.append(opt)
        elif opt == '-a':
            array_ids = opt_arg
            usedParams.append(opt)
        elif opt == '-s':
            sam_file = opt_arg
            usedParams.append(opt)
        elif opt == '-r':
            ser_file = opt_arg
            usedParams.append(opt)
        elif opt == '-p':
            p_file = opt_arg
        elif opt == '-q':
            p_id = opt_arg
        elif opt == '-e':
            series_id = opt_arg
            usedParams.append(opt)
        elif opt == '-o':
            out_file = opt_arg
            usedParams.append(opt)
        elif opt == '-d':
            existing_platform = opt_arg
        else:
            doPrint("Unknown param: %s" % opt)
            doPrint(usage(argv[0]))
            sys.exit(1)

    # if we made it to here, we need the following parameters
    if mode == "Platform":
        requiredParams = PLATFORM_REQUIRED_PARAMS
    elif mode == "Family":
        requiredParams = FAMILY_REQUIRED_PARAMS
    else:
        doPrint("Please specify a mode (-m) of either Family or Platform.")
        doPrint("Use '-h' for details.")
        sys.exit(1)
        
    missingParams = set(requiredParams) - set(usedParams)
    if len(missingParams) > 0:
        doPrint("Missing required parameters:")
        doPrint(", ".join(missingParams))
        doPrint("Use '-h' for details.")
        sys.exit(1)

    # in addition, we require either a platform id OR an existing platform
    if (p_id == None) and (existing_platform == None):
        doPrint("Either a platform id or an existing platform file is required.")
        doPrint("Use '-h' for details.")
        sys.exit(1)

    # now actually run the program
    if geneType == "malaria":
        import geo_malaria
        plugin = geo_malaria
    elif geneType == "virochip":
        import geo_virochip
        plugin = geo_virochip
    else:
        raise InputFormatException("The only known gene types are 'malaria' and 'virochip'")

    # if we got an existing platform file, use it
    if existing_platform != None:
        f = open(existing_platform)
        for line in f:
            if line.startswith("^PLATFORM"):
                p_id = line.split("=")[1].strip()
                # we found it, we're done, no need to continue processing
                break
        f.close
        plugin.parseExistingPlatform(existing_platform)

    # run the actual program, finally!
    createGeoFiles(plugin, array_ids, sam_file, ser_file, out_file, p_id, series_id, numLines, p_file)


def createGeoFiles(plugin, array_ids_filename, sample_header_filename, series_header_filename,
                  output_filename, platform_ID, series_id, numLines, platform_header_filename=None):
    """Creates a GEO family file and subfiles for submission."""

    arrayNames, experimentNames, projectNames = parseInputFile(array_ids_filename)

    family = NCBI.Family(platform_ID, series_id, plugin, arrayNames, experimentNames, projectNames)

    if platform_header_filename:
        setPlatform(plugin, platform_header_filename, family)
        family.platform.checkValidity()
          
    setSampleParams(sample_header_filename, family)
    family.sample.checkValidity()
    setSeriesParams(series_header_filename, family)
    family.series.checkValidity()

    family.dump(platform_header_filename!=None, output_filename, numLines)


def parseInputFile(input_filename):
    """ Gets the array id, experiment ids, and project ids from the input file.

    Based on Anatoly's parse_input_file function."""
    ifile = open(input_filename)

    flag = None
    arrayIds = []
    experimentIds = []
    projectIds = []
    for line in ifile:
        line = line.strip()
        if len(line) < 2:
            continue
        if line.find(ARRAYS_INPUT) >= 0:
            flag = "a"
        elif line.find("EXPERIMENTS") >= 0:
            flag = "e"
        elif line.find("PROJECTS") >= 0:
            flag = "p"
        else:
            if flag == "e":
                experimentIds.append(line)
            elif flag == "p":
                projectIds.append(line)
            else:
                arrayIds.append(line)

    doPrint("Array Ids:" + str(arrayIds))
    doPrint("Experiement Ids:" + str(experimentIds))
    doPrint("Project Ids:" + str(projectIds))

    return arrayIds, experimentIds, projectIds


def setPlatform(plugin, platform_header_filename, family):
    """Writes the platform file information to the output file."""

    headerNames, headerDesc, fieldNames = parseTemplateFile(platform_header_filename, family.platform)
    family.setPlatformDataTable(headerNames, headerDesc, plugin)


def setSampleParams(sample_header_filename, family):
    """Writes the sample (array) information to the output file."""

    headerNames, headerDesc, fieldNames = parseTemplateFile(sample_header_filename, family.sample)
    family.setSampleDataFields(headerNames, headerDesc, fieldNames)

def setSeriesParams(series_header_filename, family):
    """Writes the series information (the set of samples) to the output file."""

    parseTemplateFile(series_header_filename, family.series)
    
    
def parseTemplateFile(fileName, dataFile):
    tf = open(fileName)
    headerNames = []
    headerDesc = []
    fieldNames = []
    for line in tf:
        if line.startswith("##"):
            # these are comments and should be ignored
            pass
        elif line.startswith("!"):
            # this is a parameter for the platform
            pieces = line.split("=")
            name = pieces[0].strip()[1:] # remove the initial "!"
            val = pieces[1].strip()
            dataFile.addParameter(name, val)
        elif line.startswith("#ID_REF"):
            headerDesc.append("")
            fieldNames.append("ID_REF")
            headerNames.append("ID_REF")
        elif line.startswith("#"):
            # this is a data table header
            pieces = line.split("=")
            headerNames.append(pieces[0].strip()[1:]) # remove the initial "#"
            if len(pieces) > 1:
                open_curly = pieces[1].find("{")
                close_curly = pieces[1].find("}")
                if open_curly < 0 or close_curly < 0:
                    headerDesc.append(pieces[1].strip())
                    fieldNames.append("") # keep the lists parallel
                else:
                     fieldNames.append(pieces[1][open_curly+1:close_curly])
                     headerDesc.append(pieces[1][:open_curly])
            else:
                # need to keep the names and descriptions parallel
                headerDesc.append("")
                fieldNames.append("")

    return headerNames, headerDesc, fieldNames


def dumpTemplateFiles():
    dumpPlatformTemplate()
    dumpSampleTemplate()
    dumpSeriesTemplate()
    dumpArrayIdsTemplate()

def dumpPlatformTemplate():
    f = open("platform_template.txt", "w")
    f.write("""
## Platform File:  Information about your microarray design (which spots correspond to which genes)
##
## You may not need this file if your platform has already been submitted to GEO previously.  In that case, don't include
##        this file name when calling the script and include the Platform ID of the previous platform submission.
##        
## Notes on completing this file:
##    -- Any line starting with ## will not be transferred to the final file (for comments like this)
##
##    -- Lines that start with ! are part of the data header information
##    -- See http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html for all the optional data header lines
##    -- Lines that start with # denote the columns for the data table
##    -- These are generally set per geneType (malaria or virochip) and shouldn't be changed.
##       For malaria, the headings are ID, NAME, SPECIES, and SEQUENCE.  If you need other spot data, 
##       let Michelle know and she'll have to adjust the script.
!Platform_title = Malaria Oligo p19
!Platform_technology = spotted oligonucleotide
!Platform_distribution = non-commercial
!Platform_organism = Plasmodium falciparum, Saccharomyces cerevisiae
!Platform_manufacturer = DeRisi lab
!Platform_manufacture_protocol = As described at http://derisilab.ucsf.edu
!Platform_support = glass
!Platform_coating = poly-lysine
!Platform_description = Plasmodium falciparum coding specific 70mer oligonucleotides designed by ArrayOligoSelector
!Platform_web_link = http://derisilab.ucsf.edu
#ID = 
#NAME = The plasmodb_id(s) for Plasmodium falciparum spots, otherwise the yeast identifier.  
#SPECIES = The species of the oligo
#SEQUENCE = Sequence of oligonucleotide probe
""")
    f.close()
    doPrint("Created platform_template.txt")

def dumpSampleTemplate():
    f = open("sample_template.txt", "w")
    f.write("""
## Sample File: Data from one microarray run
##
## Notes on completing this file:
##    -- Any line starting with ## will not be transferred to the final file (for comments like this)
##
##    -- The ^SAMPLE line will be automatically added
##    -- Lines that start with ! are part of the data header information
##    -- Don't change the !Sample_platform_id line -- the script will add in the platform id you gave
##    -- See http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html for all the optional data header lines
##    -- Values in curly brackets will be looked up in the Array table of NOMAD. 
##          Some examples:
##              --- {Array_Description}: returns the array description in NOMAD
##              --- {Array_Name}: returns the array name in NOMAD
##
##    -- Lines that start with # denote the columns for the data table
##    -- Don't change the line for the ID data column
##    -- To add a column to the data table, add a line starting with # in the format 
##           #HEADER_NAME = some description here {field_name}
##    -- Values in curly braces denote the field in the result record to use for the data column.  
##           Some examples:
##              --- 635_Mean_Intensity
##              --- 532_Mean_Intensity
##              --- 635_Percent_Pixel_Saturation
##              --- Log_Ratio_Of_Medians
##              --- Ratio_Of_Medians
!Sample_title = {Array_Description}
!Sample_source_name_ch1 = Plasmodium falciparum strain 3D7
!Sample_organism_ch1 = Plasmodium falciparum
!Sample_extract_protocol_ch1 = Something was done to extract the RNA
!Sample_characteristics_ch1 = Plasmodium falciparum strain 3D7
!Sample_molecule_ch1 = total RNA
!Sample_label_ch1 = Cy5
!Sample_source_name_ch2 = Plasmodium falciparum
!Sample_organism_ch2 = Plasmodium falciparum
!Sample_extract_protocol_ch2 = Something was done to get the RNA
!Sample_characteristics_ch2 =  Plasmodium falciparum strain 3D7 total RNA reference pool
!Sample_molecule_ch2 = total RNA
!Sample_label_ch2 = Cy3
!Sample_description = {Array_Description}
!Sample_data_processing = Spot analysis was performed with GenePix v3.0 and stored in a relational database (NOMAD). Extracted values are directly as calculated by GenePix and not normalized.
!Sample_hyb_protocol = Some hybing was done.  This should be explained in detail.
!Sample_scan_protocol = Some scanning was done.  It should be explained here.
!Sample_platform_id = {Platform_id}
#ID_REF =
#VALUE = Ratio of Median Intensities {Ratio_Of_Medians}
#CH1_MEDIAN = Channel 1 (Cy5) intensity median {635_Median_Intensity}
#CH1_MEAN = Channel 1 (Cy5) intensity mean {635_Mean_Intensity}
#CH1_SD = Channel 1 (Cy5) intensity standard deviation {635_Foreground_Standard_Deviation}
#CH1_BGD_MEDIAN = Channel 1 (Cy5) background intensity median {635_Median_Background}
#CH1_BGD_MEAN = Channel 1 (Cy5) background intensity mean {635_Mean_Background}
#CH1_BGD_SD = Channel 1 (Cy5) background intensity standard deviation {635_Background_Standard_Deviation}
#CH1_NET_MEDIAN = Channel 1 (Cy5) net intensity median {F635_Median_Net}
#CH1_NET_MEAN = Channel 1 (Cy5) net intensity mean {F635_Mean_Net}
#CH2_MEDIAN = Channel 2 (Cy3) intensity median {532_Median_Intensity}
#CH2_MEAN = Channel 2 (Cy3) intensity mean {532_Mean_Intensity}
#CH2_SD = Channel 2 (Cy3) intensity standard deviation {532_Foreground_Standard_Deviation}
#CH2_BGD_MEDIAN = Channel 2 (Cy3) background intensity median {532_Median_Background}
#CH2_BGD_MEAN = Channel 2 (Cy3) background intensity mean {532_Mean_Background}
#CH2_BGD_SD = Channel 2 (Cy3) background intensity standard deviation {532_Background_Standard_Deviation}
#CH2_NET_MEDIAN = Channel 2 (Cy3) net intensity median {F532_Median_Net}
#CH2_NET_MEAN = Channel 2 (Cy3) net intensity mean {F532_Mean_Net}
#ARRAY_BLOCK = Array Block {Array_Block}
#ARRAY_COLUMN = Array Column {Array_Column}
#ARRAY_ROW = Array Row {Array_Row}
#FLAG = GenePix v.3 spot flag {Spot_Flag}
""")
    f.close()
    doPrint("Created sample_template.txt")

def dumpSeriesTemplate():
    f = open("series_template.txt", "w")
    f.write("""
## Series File: The list of Samples (Arrays) in your whole Experiment
##
## Notes on completing this file:
##    -- Any line starting with ## will not be transferred to the final file (for comments like this)
##    -- Don't add the "^SERIES" line, it will be automatically added by the script
##
##    -- Lines that start with ! are part of the data header information
##    -- See http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html for all the optional data header lines
##
!Series_title = Tetracyclines Specifically Target the Apicoplast of the Malaria Parasite Plasmodium falciparum
!Series_type = Plasmodium falciparum treated with Doxycycline
!Series_summary = Tetracyclines are effective but slow-acting antimalarial drugs whose mechanism of action remains uncertain. To characterize the antimalarial mechanism of tetracyclines, we evaluated their stage-specific activities, impacts on parasite transcription, and effects on two predicted organelle targets, the apicoplast and the mitochondrion, in cultured Plasmodium falciparum. Antimalarial effects were much greater after two 48-h life cycles than after one cycle, even if the drugs were removed at the end of the first cycle. Doxycycline-treated parasites appeared morphologically normal until late in the second cycle of treatment but failed to develop into merozoites. Doxycycline specifically impaired the expression of apicoplast genes. Apicoplast morphology initially appeared normal in the presence of doxycycline. However, apicoplasts were abnormal in the progeny of doxycycline-treated parasites, as evidenced by a block in apicoplast genome replication, a lack of processing of an apicoplast-targeted protein, and failure to elongate and segregate during schizogeny. Replication of the nuclear and mitochondrial genomes and mitochondrial morphology appeared normal. Our results demonstrate that tetracyclines specifically block expression of the apicoplast genome, resulting in the distribution of nonfunctional apicoplasts into daughter merozoites. The loss of apicoplast function in the progeny of treated parasites leads to a slow but potent antimalarial effect.
!Series_overall_design = We analyzed a series of 12 microarrays covering 55 hours of Plasmodium falciparum treated with doxycycline and 12 microarrays covering the same 55 hours with no doxycycline treatment
!Series_contributor = Erica, L, Dahl
!Series_contributor = Jennifer, L, Shock
!Series_contributor = Bhaskar, R, Shenai
!Series_contributor = Jiri, Gut
!Series_contributor = Joseph, L, DeRisi
!Series_contributor = Philip, J, Rosenthal
""")
    f.close()
    doPrint("Created series_template.txt")

def dumpArrayIdsTemplate():
    f = open("arrayids_template.txt", "w")
    f.write("""
ARRAYS
    MOS19-010
    MOS19-011
EXPERIMENTS
PROJECTS
""")
    f.close()
    doPrint("Created arrayids_template.txt")


def doPrint(str):
    print("\t", str)



#####################################################################
if __name__ == "__main__":
    main()



        
