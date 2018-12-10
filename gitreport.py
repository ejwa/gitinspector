
import os
import re
import sys
import getopt
import datetime

helpinfo = ("""Usage: gitreport [OPTION]...
  -r, --repo=<repo configfile>  a space separated list of git repositories
                                line formart likes:
                                tag         repository  since       until       
                                gitinspectory  https://github.com/ejwa/gitinspector.git 2018-01-01  2018-12-01  
                                gitinspectorycvs  https://github.com/de2sl2pfds/gitinspector.git 2018-01-01  2018-12-01  
  -o, --output=<output file>    output filename of csv format 
  -h, --help                    display this help and exit
""")

def report(repo,output):
    if not os.path.isfile(repo):
        print("repo config file not exists")
        sys.exit(-3)
    if os.path.isfile(output):
        output = output + "." + datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        print("output file exists. new file name is : " + output)
    else:
        print("output file name is : " + output)
    os.system("> " + output)
    i = 0
    for line in open(repo):
        a = re.compile("\s+").split(line.strip())
        if a[0].lower().strip() == 'tag':
            print("title: " + line.strip())
            continue
        if len(a) > 3 and a[1].lower().find('.git') > -1:
            print("No.[" + str(i) + "] : " + line.strip())
            print(" repository info: tag=" + a[0] + " since=" + a[2] + " until=" + a[3] + " gitrepo=" + a[1])
            cmd = ("python gitinspector.py --since="+a[2]+" --until="+a[3]+" --tag="+a[0]+" -F csv "+ a[1] + ">> " + output)
            print(" command: " + cmd)
            os.system(cmd)
            i += 1
            print("")


    if i < 1:
        print("no repository found.")
        os.unlink(output)
    else:
        print("processed " + str(i) + " repositories.")

def main(argv):
    repofile = "repo.txt"
    outputfile = "report.csv"

    try:
        opts, args = getopt.getopt(argv, "h:r:o:",
                                   ["help=","repo=","output="])
    except getopt.GetoptError:
        print helpinfo
        sys.exit(-1)
    if len(argv) == 0:
        print helpinfo
        sys.exit(-2)

    for o, a in opts:
        if o in("-h", "--help"):
            print(helpinfo)
            sys.exit(0)
        elif o in("-r", "--repo"):
            repofile = a
        elif o in("-o", "--output"):
            outputfile = a
        else:
            print(helpinfo)
            sys.exit(0)
    report(repofile,outputfile)

if __name__ == "__main__":
    main(sys.argv[1:])



