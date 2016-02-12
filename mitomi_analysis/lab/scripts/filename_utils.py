#!/usr/bin/env python
#
# [File Name Here]
#
# Author: [Your Name Here]
#
# [A Description Here]

__version__ = "$Revision: 1.1 $".split(':')[-1].strip(' $') # don't edit this line.
                                                            # cvs will set it.

import os
import sys
import shutil

def make_filename_dict(namefile):
     """This program takes a tab-delimited file with old filenames in the first column and
     new filenames in the second column and makes a dictionary linking the two."""

     #open name file and make dictionary to hold names
     name_file = open(namefile,'r')
     d_name = {}

     #read file line by line and create a dictionary linking old and new names
     for line in name_file:
         temp_list = line.split("\t")
         old_name, new_name  = temp_list[0], temp_list[1].split("\r")[0]
         d_name[old_name]=new_name

     # close the file and return your nice new dictionary
     name_file.close()
     return d_name

def rename_files(directory,namefile):
     """This program reads in all of the filenames from a given directory
     and then renames them according to the dictionary created from a tab-delimited file."""

     filename_list = os.listdir(directory)
     name_dict = make_filename_dict(namefile)
     #print name_dict
     
     for item in filename_list:
          root_name = item.split(".")[0].split("_")[0]
          #print "root_name = "+root_name

          num_parts = len(item.split(".")) # this next part tries to keep the suffix the same
          if num_parts == 1:
               suffix = ""
               #print "suffix1 = "+suffix
          elif num_parts == 2:
               suffix = "."+item.split(".")[1] # this just selects all of the text before the first "."
               #print "suffix2 = "+suffix
          elif num_parts == 3:
               suffix = "."+item.split(".")[1]+"."+item.split(".")[2]
               #print "suffix3 = "+suffix
          else:
               print "Something funny is going on with the filenames!"
               
          dummy_var = name_dict.has_key(root_name)
          if dummy_var == True:
               #print "Filename root IS in dictionary!"
               #print "root_name = "+root_name
               #print "dictionary item = "+name_dict[root_name]
               old_name = directory+item
               #print "old_name = "+old_name
               new_name = directory+name_dict[root_name]+suffix
               #print "new_name = "+new_name
               os.rename(old_name,new_name)
          else:
               print "Filename root is not in dictionary!"


##############################################
if __name__ == "__main__":
    main()
