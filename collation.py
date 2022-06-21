from collatex import *
import os
import pypandoc as pp
import re
from bs4 import BeautifulSoup
import requests # for REST requests
from requests.auth import HTTPDigestAuth # for Transkribus REST requests
from requests.auth import HTTPBasicAuth # for exist REST request
from json2html import *
import json
import config # stores basic config


def open_file_as_witness(pathtofile, i):
    """ Opens prepared txt files as witnesses
    """

    with open(pathtofile) as f:
        text = f.read()
        return text

def preprocessing_witness(witness):
    """ Normalises files for a more meaningful collation
    """

    witness = witness.lower()
    witness = witness.replace('ę','e')
    witness = witness.replace('tv','tu')
    witness = witness.replace('vm','um')
    witness = witness.replace('vnt','unt')
    witness = witness.replace('ae','e')
    witness = witness.replace('vt','ut')
    witness = witness.replace('rv','ru')
    witness = witness.replace('coepit','cepit')
    witness = witness.replace('y','i')
    witness = witness.replace('tio','cio')
    witness = witness.replace('tia','cia')
    #witness = witness.replace('oe','e')
    witness = witness.replace('mpn','mn')
    witness = witness.replace('comprou','conprou')
    witness = witness.replace('ecles','eccles')
    witness = witness.replace('privetur','priuetur')
    witness = witness.replace('verum','uerum')
    witness = witness.replace('repperimus','reperimus')
    witness = witness.replace('[]','')
    #witness = witness.replace(' quinque ',' v ')

    return witness

def collate_witnesses(booknumber, i, manuscripts, filename):
    """ Actuall collation
    """

    collation = Collation()

    for m in manuscripts:
        # Add witnesses
        text = open_file_as_witness('./witnesses/' + m + '_' + str(booknumber) + '_'+ i +'.txt', i)
        text = preprocessing_witness(text)
        collation.add_plain_witness(m, text)

    alignment_table = collate(collation, layout="vertical")
    #alignment_table_csv = collate(collation, output="csv")
    with open(filename, 'w') as txt:
        txt.write(str(alignment_table))

    return filename

def output_html(filename):
    """ Creates html table

    """

    with open(filename) as f:
        # open collation file in markdown format
        file = f.read()
        # convert md file to html
        html = pp.convert_text(file, 'html', format='md')
        html = re.sub('\>toc(\d+)','<b>\g<1>: </b>',html)
        html = re.sub('\w toc(\d+)','<br><b>\g<1>: </b>',html)
        html = re.sub('toc(\d+)','<br><b>\g<1>: </b>',html)
        html = re.sub('\w k(\d+)','<br><b>Kapitel \g<1>: </b><br>',html)
        html = re.sub('\>k(\d+)','<b>Kapitel \g<1>: </b><br>',html)

        # clean up html
        html = html.replace('<pre><code>','')
        html = html.replace('</code></pre>','')
        soup = BeautifulSoup(html, 'lxml')
        tag_to_remove = soup.find("colgroup")
        tag_to_remove.decompose()

        rows = soup.find("table").find("tbody").find_all("tr")
        e = 1
        for row in rows:
            print(type(row))
            cells = row.find_all("td")
            if len(set(cells)) > 1:
                td = row.find_all('td')
                for i in td:
                    i['style'] = 'background-color:red;'
                print(row)
            td1 = row.find('td')
            tag = soup.new_tag("td")
            tag.string = str(e)
            td1.insert_before(tag)

            print(row)
            e += 1
        with open(filename.replace('.md', '.html'),'w') as save:
            save.write(str(soup))


def create_filename(booknumber, i, manuscripts):
    """ Constructs filename
    """

    filename_sigla = ""
    for m in manuscripts:
        filename_sigla = filename_sigla + m + '_'
    filename = './output/'+ filename_sigla + str(booknumber) + '_' + i +'.md'

    return filename

def xslt_transformation(manuscripts, booknumber, segments_of_text):
    """ takes downloaded xml files and transforms them to txt based on xslt file and saxon jar
    """
    for i in segments_of_text:
        for m in manuscripts:
            if m == 'F':
                ms = 'frankfurt-ub-b-50-' + str(booknumber).zfill(2) + '.xml'
            elif m == 'V':
                if booknumber < 8:
                    ms = 'vatican-bav-pal-lat-585-' + str(booknumber).zfill(2) + '.xml'
                else:
                    ms = 'vatican-bav-pal-lat-586-' + str(booknumber).zfill(2) + '.xml'
            elif m == 'B':
                ms = 'bamberg-sb-c-6-' + str(booknumber).zfill(2) + '.xml'

        os.system('java -jar '+ filepath + 'saxon/saxon9he.jar -s:'+ filepath +'xml/' + ms + ' -xsl:'+ filepath + 'xslt/xml_to_collatex.xslt -o:'+ filepath + 'witnesses/' + m + '_' + str(booknumber) + '_a.txt')


# Todo take method from file
def get_xml_from_exist(user, pw, manuscripts, booknumber, base_url):
    """ Getting list of abbreviations from remote exist-db collections provided by xquery script

    Downloads list of abbreviation needed for automatic expansion from existdb instance
    queried by xquery script named 'abbreviations.xquery' on server as JSON file
    'abbreviation_dictionary.json' in resource folder specified in config.py on local machine.

    :param user: Username as string (should be specified in config.py)
    :param pw: Password as string (should be specified in config.py)
    :param exist_url: Url to xml file
    :param resources_folder: Download-folder as string (should be specified in config.py)
    :return: Returns dictionary containing abbreviations with corresponding expansions for further processing
    """

    # login to exist...
    # ...set session...
    session = requests.Session()

    for m in manuscripts:
        if m == 'F':
            collection = 'frankfurt-ub-b-50'
            ms = 'frankfurt-ub-b-50-'
        elif m == 'V':
            if booknumber < 8:
                collection = 'vatican-bav-pal-lat-585'
                ms = 'vatican-bav-pal-lat-585-'
            else:
                collection = 'vatican-bav-pal-lat-586'
                ms = 'vatican-bav-pal-lat-586-'
        elif m == 'B':
            collection = 'bamberg-sb-c-6'
            ms = 'bamberg-sb-c-6-'

        # Get xml-document containing list of abbreviatins as choice elements via xquery stored on exist server...
        url = base_url + collection + '/' + ms + str(booknumber).zfill(2) + '.xml'

        # ...post export request, starts export and returns xml...
        export_request = session.get(url, auth=HTTPBasicAuth(user, pw))
        export_request = export_request.text

        with open('./xml/' + ms + str(booknumber).zfill(2) + '.xml', "w") as text_file:
            text_file.write(export_request)

def start_collation(booknumber, segments_of_text, manuscripts, collate_or_not):
    """ Starts collation process

    :param booknumber: takes book number to be collated as integer
    :param segments_of_text: takes list of text segments 'a', 'b', 'c'...
    :manuscripts: Takes list of strings containing sigle of manuscripts
    """

    for i in segments_of_text:
        collation = Collation()
        filename = create_filename(booknumber, i, manuscripts)
        if collate_or_not == True:
            collate_witnesses(booknumber, i, manuscripts, filename)
        else:
            pass
        output_html(filename)


def start_collation_java(booknumber, segments_of_text, manuscripts, filepath):

    for i in segments_of_text:

        string_of_filenames = ""
        filename_sigla = ""
        for m in manuscripts:
            filename_sigla = filename_sigla + m + '_'

        for m in manuscripts:
            if m == 'F':
                ms = filepath + 'witnesses/F_' + str(booknumber).zfill(2) + '_' + i + '.txt'
            elif m == 'V':
                if booknumber < 8:
                    ms = filepath + 'witnesses/V_' + str(booknumber).zfill(2) + '_' + i + '.txt'
                else:
                    ms = filepath + 'witnesses/V_' + str(booknumber).zfill(2) + '_' + i + '.txt'
            elif m == 'B':
                ms = filepath + 'witnesses/B_' + str(booknumber).zfill(2) + '_' + i + '.txt'

            string_of_filenames = string_of_filenames + ' ' + ms

        execute = 'java -jar ' + filepath + 'collatex/collatex-tools-1.7.1.jar -f json -o ' + filepath + 'output/' + filename_sigla + str(booknumber).zfill(2) + '.json' + string_of_filenames
        os.system(execute)



booknumber = 13
segments_of_text = ['a']
manuscripts = ['F','V','B']
user = config.user_exist
pw = config.pw_exist
filepath = config.cwd
base_url = config.base_url
# erst Daten aus Exist ziehen
#get_xml_from_exist(user, pw, manuscripts, booknumber, base_url)
# dann transformation zu textfile
#xslt_transformation(manuscripts, booknumber, segments_of_text, filepath)
# dann collation starten
#start_collation(booknumber, segments_of_text, manuscripts, True)
# use java library for faster collation
start_collation_java(booknumber, segments_of_text, manuscripts, filepath)


""" TODO
- Normalisierungen implementieren
- Json zu Tabelle
- zellen rot machen
- automatisierter upload zu exist
- Dokumentation verbessern
"""
