#!/usr/bin/env python

"""
A module for fetchAssemblies.py.

Authors: C-Connor (github.com/C-Connor), Yu Wan <wanyuac@126.com>
Licensed under the Apache License, version 2.
Publication: 8 July 2020; last modification: 8 July 2020.
"""

import os
import sys
import json
import time
import pipes
import base64
import getpass
import logging
import urllib.error
import urllib.parse
import urllib.request


class EnterobaseAssemblyDownloader:
    """ Communicate with Enterobase and fetch data """

    def __init__(self, barcode_list, outdir, time_interv, append_barcode, db):
        # Prompt for logging details
        self.__username = pipes.quote(input("Please enter Enterobase username: "))
        self.__password = pipes.quote(getpass.getpass("Please enter Enterobase password: "))
        self.__server = "https://enterobase.warwick.ac.uk"
        self.__apiaddress = "%s/api/v2.0/login?username=%s&password=%s" % (self.__server, self.__username, self.__password)
        self.__time = time_interv if time_interv > 0 else 4  # Time interval between two consecutive download requests
        self.__append_barcode = append_barcode  # True or False
        self.__valid_db = ["senterica", "ecoli", "clostridium", "vibrio", "yersinia", "helicobacter", "mcatarrhalis"]
        self.__barcode_error_log = list()
        self.__fasta_error_log = list()
        self.__api_token = None

        # Validate database name
        if db in self.__valid_db:
            self.__db = db  # Name of database from which assemblies are to be downloaded
        else:
            print("Invalid database name. It must be chosen from " + ", ".join(self.__valid_db) + ".")
            sys.exit(0)
        
        # Validate the input file
        if os.path.isfile(barcode_list):
            self.__barcode_list = barcode_list
        else:
            print("Could not find the file of barcode list. Exiting.")
            sys.exit(0)

        # Create the output directory if it does not exist
        self.__outdir = outdir + os.sep
        if not os.path.exists(os.path.dirname(self.__outdir)):
            os.makedirs(os.path.dirname(self.__outdir))

        print("A Downloader object has been successfully initiated.")

        return

    
    @property
    def api_token(self):  # Accessible class attribute
        return self.__api_token

    
    @property
    def barcodes(self):
        return self.__barcodes  # Returns a dictionary


    @property
    def valid_db(self):
        return  self.__valid_db  # A list of valid database names


    # No @classmethod should be placed here
    def get_api_token(self):
        """ Get an API token from Enterobase """
        print("Retrieving an API token from Enterobase.")
        try:
            response = urllib.request.urlopen(self.__apiaddress)
            data = json.load(response)
            self.__api_token = data["api_token"]
        except urllib.error.HTTPError as Response_error:
            print("A connection error ocurred:")
            print("%d %s. <%s>\n Reason: %s" %(Response_error.code, Response_error.msg, Response_error.geturl(), Response_error.read()))
            sys.exit(1)

        return self.__api_token

    
    def import_barcodes(self):
        self.__barcodes = dict()
        with open(self.__barcode_list, "r") as f_in:
            for line in f_in:
                name, barcode = line.strip().split("\t")
                self.__barcodes[name] = barcode  # The name will be used as the basename of an output FASTA file.

        return


    def download_assemblies(self):
        """ Download assemblies as FASTA files using assembly barcodes """
        n = 0
        for name, barcode in self.__barcodes.items():
            # Put the assembly barcode into an URL for database search
            url = "http://enterobase.warwick.ac.uk/api/v2.0/%s/assemblies?barcode=%s&limit=50" % (self.__db, barcode)
            try:
                # Request the URL of the target assembly FASTA file
                response = urllib.request.urlopen(self.__create_request(url))
                data = json.load(response)
                fasta_url = data["Assemblies"][0]["download_fasta_link"]
                try:
                    # Request the FASTA file using its URL
                    fasta_response = urllib.request.urlopen(self.__create_request(fasta_url))
                    if fasta_response.getcode() == 200:
                        if self.__append_barcode:
                            fasta_out_filename = self.__outdir + "__".join([name, barcode]) + ".fna"
                        else:
                            fasta_out_filename = self.__outdir + name + ".fna"
                        with open(fasta_out_filename, "w") as fasta_out:
                            fasta_out.write(fasta_response.read())  # Successfully downloaded a FASTA file
                    else:
                        self.__fasta_error_log.append([name, barcode, fasta_url, fasta_response.getcode(), "Failed download with an invalid server response."])
                except urllib.error.HTTPError as Response_error:
                    self.__fasta_error_log.append([name, barcode, str(fasta_url), "Failed download as %s, %s" % (Response_error.read(), Response_error.msg)])
            except urllib.error.HTTPError as Response_error:
                self.__barcode_error_log.append([name, barcode, "Query address: " + str(url), "Reason: %s, %s" % (Response_error.read(), Response_error.msg)])
            n += 1
            sys.stdout.write("\nProgress: %s with barcode %s (%i in total) has been processed." % (name, barcode, n))
            sys.stdout.flush()
            time.sleep(self.__time)

        # Write error messages
        self.__write_error_messages(self.__barcode_error_log, "barcode_errors")
        self.__write_error_messages(self.__barcode_error_log, "fasta_errors")
    
        return


    def __create_request(self, request_str):
        """
        A 'private' method of this class and it works for method download_assemblies
        Cf. https://enterobase.readthedocs.io/en/latest//api/api-download-schemes-assemblies.html#downloading-assemblies
        """
        if self.__api_token == None:
            self.get_api_token()
        
        request = urllib.request.Request(request_str)
        base64string = base64.encodestring("%s:%s" % (self.__api_token, "")).replace("\n", "")
        request.add_header("Authorization", "Basic %s" % base64string)

        return request
    

    def __write_error_messages(self, error_messages, base_name):
        # Write messages about barcode errors
        with open(self.__outdir + base_name + time.strftime("%Y%m%d_%H%M") + ".log", "w") as error_out:
            for line in error_messages:
                error_out.write("\t".join(line) + "\n")

        return
