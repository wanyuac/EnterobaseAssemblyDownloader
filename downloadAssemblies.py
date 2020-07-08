#!/usr/bin/env python

"""
Download genome assemblies from Enterobase (enterobase.warwick.ac.uk) by their barcodes.
This script is modified from C-Connor"s script EnterobaseGenomeAssemblyDownload.py, which
is accessible at https://github.com/C-Connor/EnterobaseGenomeAssemblyDownload.

Authors: C-Connor (github.com/C-Connor), Yu Wan <wanyuac@126.com>
Licensed under the Apache License, version 2.
Publication: 8 July 2020; last modification: 8 July 2020.

Changes made by Yu:
- Converted the script for Python3 compatibility.
- Optimised code structure. Particularly, introduced object-oriented programming.
- Shortened the script name.
- Corrected some bugs in original code.
- Changed options and the input format.
- Removed the functionality of download by accession numbers for simplicity.
"""

import os
import sys
import time
import argparse
from ClassEnterobaseAssemblyDownloader import EnterobaseAssemblyDownloader as Downloader


# Get command-line arguments
def parse_arguments():
    cl_parser = argparse.ArgumentParser(description = "Downloads genome assemblies from enterobase when provided with a download list.")
    cl_parser.add_argument("-i", "--input", dest = "input", type = str, required = True,\
                           help = "Path to a two-column tab-delimited text file (Name, Barcode) for genomes to be downloaded. Set to 'i' to print instructions.")
    cl_parser.add_argument("-d","--database", dest = "db", type = str, required = False, default = "ecoli",\
                           help = "Enterobase database to download assemblies from. [ecoli (default), senterica, clostridium, vibrio, yersinia, helicobacter, mcatarrhalis].")
    cl_parser.add_argument("-o","--outdir", dest = "outdir", type = str,\
                           default = os.getcwd() + os.sep + "Enterobase_Assemblies" + time.strftime("%Y%m%d_%H%M"),
                           help = "Specify output directory to save assemblies")
    cl_parser.add_argument("-a","--append_barcode", dest = "append_barcode", action = "store_true", required = False,\
                           help = "Turn on this option to append a barcode to each downloaded assembly.")
    cl_parser.add_argument("-t", "--time", dest = "time", type = int, default = 4, required = False,\
                           help = "Number of seconds between two consecutive download requests.")

    return cl_parser.parse_args()


def main():
    # Initiate a Downloader object
    args = parse_arguments()
    if args.input != "i":
        downloader = Downloader(barcode_list = args.input, outdir = args.outdir, time_interv = args.time,\
                                append_barcode = args.append_barcode, db = args.db)
    else:
        print_instructions()
    
    # Get an API token from Enterobase
    downloader.get_api_token()
    print("API token: " + downloader.api_token)
    
    # Read the file of barcodes
    downloader.import_barcodes()

    # Download assemblies
    downloader.download_assemblies()  

    return


def print_instructions():
    print("\nInstructions for creating the download file from enterobase required by this script: \n")
    print("1. Go to enterobase.warwick.ac.uk and select your database of interest. Select \"Search strains\".")
    print("2. Search for your desired strains.")
    print("3. Ensure that \"Experimental Data\" in the top right corner, is set to \"Assembly Stats\".")
    print("4. Download the text file by selecting \"Data > Save to Local File\".")
    print("5. The resulting text file should contain columns corresponding to those on enterobase. There should also be a column called \"Assembly Barcode\".")
    print("6. Create a two-column TSV file (Name, Barcode) from the downloaded text file as the input list.\n")
    print("This script requires a valid enterobase login with API access to your database of interest.")
    sys.exit(0)
    
    return


if __name__ == "__main__":
    main()
