#Matthew Boyer's addition to gauage responsibility per file in a more clear cut way
#than resposibilitiesoutput.py

from __future__ import print_function
from __future__ import unicode_literals
import textwrap
from ..localization import N_
from .. import format, gravatar, terminal
from .. import responsibilities as resp
from .outputable import Outputable

FILE_RESPONSIBILITIES_INFO_TEXT = N_("The following files, were found in the current "
                                "revision of the repository and the ownership of "
                                "each is classified by author (excluding comments)")

class Responsibility_Per_File_Output(Outputable):
    def __init__(self, changes, blame):
        self.changes = changes
        self.blame = blame
        Outputable.__init__(self)

    def output_json(self):
        message_json = "\t\t\t\"message\": \"" + _(FILE_RESPONSIBILITIES_INFO_TEXT) + "\",\n"
        resp_json = ""
        #file_dict = {"file name as key": [{"array of author_dictionaries as value"}]}
        file_dict = {}
        total_rows_dict = {}
        #iterate over each author
        for i in sorted(set(i[0] for i in self.blame.blames)):
            responsibilities = sorted(((i[1], i[0]) for i in resp.Responsibilities.get(self.blame, i)))

            if responsibilities:
                email = self.changes.get_latest_email_by_author(i)
                name = i
                #iterate over each responsibility
                for j, entry in enumerate(responsibilities):
                    file = entry[1]
                    rows = entry[0]
                    author_dict = {}
                    author_dict["author_name"] = name
                    author_dict["author_email"] = email
                    author_dict["rows_owned"] = rows

                    #add file to the dictionary if it doesn't exist, and set it equal to an author_dict
                    if (file_dict.get(file, -1) == -1 or file_dict.get(file) == None):
                        file_dict[file] = [author_dict]
                    #append the array of the file_dict[file] value with an author dict
                    else:
                        new_values = file_dict.get(file)
                        new_values.append(author_dict)
                        file_dict[file] = new_values
                    if j >= 100000000:
						break

        #calculate the total rows for each file and put into a dict with
        #key = file and value = total_rows
        for file in file_dict:
            count = 0
            for author_dict in file_dict.get(file):
                count += author_dict["rows_owned"]
            total_rows_dict[file] = count

        #construct the response in a json format
        for file in file_dict: #Make json object, add file name, total rows, and authors array
            resp_json += "{\n"
            resp_json += "\t\t\t\t\"file name\": \"" + file + "\",\n"
            resp_json += "\t\t\t\t\"total rows\": " + str(total_rows_dict[file]) + ",\n"
            resp_json += "\t\t\t\t\"authors\": [\n\t\t\t\t"
            #construct the authors array with a json object.
            for author_dict in file_dict.get(file):
                resp_json += "{\n"
                resp_json += "\t\t\t\t\t\"author name\": \"" + author_dict["author_name"] + "\",\n"
                resp_json += "\t\t\t\t\t\"author email\": \"" + author_dict["author_email"] + "\", \n"
                resp_json += "\t\t\t\t\t\"rows owned\": " + str(author_dict["rows_owned"]) + ",\n"
                resp_json += "\t\t\t\t\t\"perctenage of document\": " + str(float(author_dict["rows_owned"])/float(total_rows_dict[file])*100) + "\n"
                resp_json += "\t\t\t\t},"

            #next 3 lines are diddo from responsibilitiesoutput.py
            resp_json = resp_json[:-1]
            resp_json += "]\n\t\t\t},"
        resp_json = resp_json[:-1]
        #print the final results
        print(",\n\t\t\"responsibility_per_file\": {\n" + message_json + "\t\t\t\"files\": [\n\t\t\t" + resp_json + "]\n\t\t}", end="")

#the final message format.
#   {
#       "responsibility_per_file": {
#           "files": [
#                       {
#                       "file name": /gitinspector/file_example.py":
#                           "total rows": XXXX,
#                           "authors": [
#                               "Author": {
#                                   "author_email": "example@github.com",
#                                   "author_name": "Justin Example",
#                                   "rows owned": "XXX",
#                                   "percentage control": XX%
#                       }, ....
#                   ]
#               }, ....
#            ]
#       }
#   }
