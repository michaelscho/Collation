import os
import re
from bs4 import BeautifulSoup
import requests # for REST requests
from requests.auth import HTTPDigestAuth # for Transkribus REST requests
from requests.auth import HTTPBasicAuth # for exist REST request
import json
import config # stores basic config


def open_file_as_witness(pathtofile):
    """ Opens prepared txt files as witnesses
    """

    with open(pathtofile) as f:
        text = f.read()
        return text

def preprocessing_witness(witness):
    """ Normalises files for a more meaningful collation
    """

    witness = witness.lower()
    # for handling lb break="no"
    #witness = re.sub('(\w)_\s\s+','\g<1>',witness)
    while '  ' in witness:
        witness = witness.replace('  ',' ')
    witness = re.sub('\s+',' ',witness)
    witness = re.sub('\s+\+','',witness)
    witness = witness.replace('+ ','')
    witness = witness.replace('+','')
    # for handling supplied elements
    witness = witness.replace('_','')


    witness = witness.replace('ę','e')
    witness = witness.replace('\n',' ')
    witness = witness.replace('tv','tu')
    witness = witness.replace('vm','um')
    witness = witness.replace('vnt','unt')
    witness = witness.replace('ae','e')
    witness = witness.replace('vt','ut')
    witness = witness.replace('rv','ru')
    witness = witness.replace('coepit','cepit')
    witness = witness.replace('y','i')
    witness = witness.replace('cio','tio')
    witness = witness.replace('cia','tia')
    #witness = witness.replace('oe','e')
    witness = witness.replace('mpn','mn')
    witness = witness.replace('comprou','conprou')
    witness = witness.replace('ecles','eccles')
    witness = witness.replace('privetur','priuetur')
    witness = witness.replace('verum','uerum')
    witness = witness.replace('repperimus','reperimus')
    witness = witness.replace('[]','')
    witness = witness.replace(' decimvs ', ' decimus ')
    witness = witness.replace(' ieivnio ', ' ieiunio ')
    witness = witness.replace(' genva ', ' genua ')
    #witness = witness.replace(' v ', ' quinque ')
    #witness = witness.replace(' iii ', ' tertius ')
    #witness = witness.replace(' vi ', ' sex ')
    #witness = witness.replace(' xxx ', ' triginta ')
    #witness = witness.replace(' xlme ', ' quadragesime ')
    witness = witness.replace(' qvadragesima ', ' quadragesima ')
    #witness = witness.replace(' xlma ', ' quadragesima ')
    witness = witness.replace(' tercius ', ' tertius ')
    witness = witness.replace(' tercivs ', ' tertius ')
    witness = witness.replace(' tertivs ', ' tertius ')
    witness = witness.replace(' tercii ', ' tertii ')

    witness = witness.replace(' inicium ', ' initium ')


    return witness

def output_html(filepath, booknumber, manuscripts):
    """ Creates html table

    """
    filename = filepath + 'output/' + '_'.join(manuscripts) + '_' + str(booknumber).zfill(2) + '.html'

    with open(filename) as f:
        # open collation file in markdown format
        html = f.read()
        # convert md file to html
        html = re.sub('toc(\d+)','<br><b>\g<1>: </b>',html)
        html = re.sub('k(\d+)','<br><b>Kapitel \g<1>: </b><br>',html)

        soup = BeautifulSoup(html, 'lxml')

        rows = soup.find("table").find("tbody").find_all("tr")
        e = 1
        for row in rows:
            print(type(row))
            cells = row.find_all("td")
            if len(set(cells)) > 1:
                row['style'] = 'background-color:red;'
                #td = row.find_all('td')
                #for i in td:
                #    i['style'] = 'background-color:red;'
                #print(row)
            e += 1

        y = 1
        for tr in soup.select('tr'):
            tds = tr.select('td')
            new_td = soup.new_tag('td')
            new_input = soup.new_tag('input', **{'type':'checkbox','id':'termsChkbx', 'onchange':'isChecked(this,\'sub1\')'}) # + '<input type="checkbox" id="termsChkbx" onchange="isChecked(this,\'sub1\')"/>'
            new_td.append(str(y))
            new_td.append(new_input)
            tr.append(new_td)
            y += 1

        with open(filename.replace('.html', '_final.html'),'w') as save:
            save.write(str(soup))

def create_filename(booknumber, i, manuscripts):
    """ Constructs filename
    """

    filename_sigla = ""
    for m in manuscripts:
        filename_sigla = filename_sigla + m + '_'
    filename = './output/'+ filename_sigla + str(booknumber).zfill(2) + '_' + i +'.md'

    return filename

def xslt_transformation(manuscripts, booknumber, filepath):
    """ takes downloaded xml files and transforms them to txt based on xslt file and saxon jar
    """

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
        elif m == 'K':
            ms = 'koeln-edd-c-119-' + str(booknumber).zfill(2) + '.xml'

        os.system('java -jar '+ filepath + 'saxon/saxon9he.jar -s:'+ filepath +'xml/' + ms + ' -xsl:'+ filepath + 'xslt/xml_to_collatex.xslt -o:'+ filepath + 'witnesses/' + m + '_' + str(booknumber).zfill(2) + '.txt')

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
        elif m == 'K':
            collection = 'koeln-edd-c-119'
            ms = 'koeln-edd-c-119-'


        # Get xml-document containing list of abbreviatins as choice elements via xquery stored on exist server...
        url = base_url + collection + '/' + ms + str(booknumber).zfill(2) + '.xml'

        # ...post export request, starts export and returns xml...
        export_request = session.get(url, auth=HTTPBasicAuth(user, pw))
        export_request = export_request.text

        with open('./xml/' + ms + str(booknumber).zfill(2) + '.xml', "w") as text_file:
            text_file.write(export_request)

def normalise_files(booknumber, manuscripts, filepath):
    for ms in manuscripts:
        filename = filepath + f'witnesses/{ms}_{str(booknumber).zfill(2)}.txt'
        normalised_filename = filepath + f'witnesses/{ms}_{str(booknumber).zfill(2)}_normalised.txt'
        with open(filename, 'r') as input_file:
            text = input_file.read()
        normalised_text = preprocessing_witness(text)
        with open(normalised_filename, 'w') as output_file:
            output_file.write(normalised_text)

class Collation:
    def __init__(self, sigla, filename, booknumber):
        self.sigla = sigla.upper()
        self.filename = filename
        self.text = ""
        self.booknumber = booknumber
        self.segments_of_text = []
        self.number_of_segments = 0

    def read_file(self):
        with open(self.filename, 'r') as file:
            self.text = file.read()

    def write_file(self, n, segment):
        filename = f"witnesses/{self.sigla}_{str(self.booknumber).zfill(2)}_{n}_normalised.txt"
        with open(filename, 'w+')as file:
            file.write(segment)

    def text_to_segments(self):
        stopwords = re.findall(r'collatex:\d+', self.text)
        self.number_of_segments = len(stopwords)
        if self.number_of_segments == 0:
            self.write_file(1, self.text)
            self.number_of_segments = 1

        else:
            n = 1
            print(self.number_of_segments)
            while n < self.number_of_segments:
                segment = re.findall(f'collatex:{n}(.*?)collatex:{n+1}', self.text, re.DOTALL)
                self.write_file(n, segment[0])
                n+=1


    def prepare_collation(self):
        self.read_file()
        self.text_to_segments()

def start_collation(booknumber, segments_of_text, manuscripts, filepath):
    i = 1
    while i <= segments_of_text:
        string_of_filenames = ""
        filename_sigla = ""
        for m in manuscripts:
            filename_sigla = filename_sigla + m + '_'
        for m in manuscripts:
            if m == 'F':
                ms = filepath + f'witnesses/F_{str(booknumber).zfill(2)}_{i}_normalised.txt'
            elif m == 'V':
                    ms = filepath + f'witnesses/V_{str(booknumber).zfill(2)}_{i}_normalised.txt'
            elif m == 'B':
                ms = filepath + f'witnesses/B_{str(booknumber).zfill(2)}_{i}_normalised.txt'
            elif m == 'K':
                ms = filepath + f'witnesses/K_{str(booknumber).zfill(2)}_{i}_normalised.txt'

            string_of_filenames = string_of_filenames + ' ' + ms
        execute = 'java -jar ' + filepath + 'collatex/collatex-tools-1.7.1.jar -f json -o ' + filepath + 'output/' + filename_sigla + str(booknumber).zfill(2) + '.json' + string_of_filenames
        os.system(execute)

def collation_to_html(booknumber, manuscripts, filepath):
    ms_string = ""
    sigla_html = '<html><body><table style="width:96%;"><tbody><tr>'
    for ms in manuscripts:
        ms_string = ms_string + ms + '_'
        sigla_html = sigla_html + '<th>' + ms + '</th>'
    sigla_html = sigla_html + '</tr>'
    filename = filepath + 'output/' + ms_string + str(booknumber).zfill(2) + '.json'
    filename_html = filepath + 'output/' + ms_string + str(booknumber).zfill(2) + '.html'
    table_html = sigla_html
    with open(filename) as json_file:
        data = json.load(json_file)
    i = 0
    while i < len(data['table']):
        table_html = table_html + '<tr>'
        e = 0
        while e < len(manuscripts):
            cell = '<td>' + "".join(data['table'][i][e]) + '</td>'
            table_html = table_html + cell
            e += 1
        table_html = table_html + '</tr>'
        i += 1
    table_html = table_html + '</table><script>function isChecked(elem) {elem.parentNode.parentNode.style.backgroundColor = (elem.checked) ? \'white\' : \'red\';}</script></body></html>'
    table_html = table_html.replace('   </td>','</td>')
    table_html = table_html.replace('  </td>','</td>')
    table_html = table_html.replace(' </td>','</td>')

    with open(filename_html,'w') as html_output:
        html_output.write(table_html)

"""
def main_old():
    booknumber = 1
    manuscripts = ['V', 'F', 'B']
    user = config.user_exist
    pw = config.pw_exist
    filepath = config.cwd
    base_url = config.base_url

    # erst Daten aus Exist ziehen
    get_xml_from_exist(user, pw, manuscripts, booknumber, base_url)
    # dann transformation zu textfile
    xslt_transformation(manuscripts, booknumber, segments_of_text, filepath)
    # normalise files for mor meaningful collation
    normalise_files(booknumber, segments_of_text, manuscripts, filepath)
    # use java library for faster collation
    start_collation(booknumber, segments_of_text, manuscripts, filepath)
    # transform json into html table
    collation_to_html(booknumber, manuscripts, filepath)
    # prepare html table
    output_html(filepath, booknumber, manuscripts)
"""

def main():
    booknumber = 1
    manuscripts = ['V', 'F', 'B']
    user = config.user_exist
    pw = config.pw_exist
    filepath = config.cwd
    base_url = config.base_url

    # erst Daten aus Exist ziehen
    get_xml_from_exist(user, pw, manuscripts, booknumber, base_url)
    # dann transformation zu textfile
    xslt_transformation(manuscripts, booknumber, filepath)
    # normalise files for mor meaningful collation
    normalise_files(booknumber, manuscripts, filepath)
    # create list of segments for debug
    segments_of_text = []

    for m in manuscripts:
        filename = f"{filepath}/witnesses/{m}_{str(booknumber).zfill(2)}_normalised.txt"
        manuscript = Collation(m, filename, booknumber)
        manuscript.prepare_collation()
        segments_of_text.append(manuscript.number_of_segments)

    # compare number of text segments in each manuscripts for consistency
    if len(set(segments_of_text)) > 1:
        print("Wrong number of segments, check source files.")
    else:
        start_collation(booknumber, segments_of_text[0], manuscripts, filepath)

    # transform json into html table
    collation_to_html(booknumber, manuscripts, filepath)
    # prepare html table
    output_html(filepath, booknumber, manuscripts)

if __name__ == '__main__':
    main()



""" TODO
- zellen rot machen (noch nicht immer korrekt)
- automatisierter upload zu exist
- Dokumentation verbessern
- Marker in XML setzen und dann hier entsprechend parsen, dass immer nur das verglichen wird

<interp type="collatex" ana="1"/>
zu collatex:1
exclude in to html
include in to txt
in action packen
auch wieder alle löschen

- <collatex:1/>
- das dann per xslt in den Text bringen zb als #Collatex n#
- dann dateien durchsuchen und in abschnitte einteilen, die dann kollationiert werden

"""

