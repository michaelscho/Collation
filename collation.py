import os
import re
from bs4 import BeautifulSoup
import requests # for REST requests
from requests.auth import HTTPDigestAuth # for Transkribus REST requests
from requests.auth import HTTPBasicAuth # for exist REST request
import json
import config # stores basic config
import argparse # for passing arguments from cli
import lxml.etree as LET # for handling xslt


# Todo take method from file
def get_xml_from_exist(manuscripts, booknumber):
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
    user = config.user_exist
    pw = config.pw_exist
    filepath = config.cwd
    base_url = config.base_url

    # ...set session...
    session = requests.Session()

    for m in manuscripts:
        if m[0] == 'F':
            collection = 'frankfurt-ub-b-50'
            ms = 'frankfurt-ub-b-50-'
        elif m[0] == 'V':
            if booknumber < 8:
                collection = 'vatican-bav-pal-lat-585'
                ms = 'vatican-bav-pal-lat-585-'
            else:
                collection = 'vatican-bav-pal-lat-586'
                ms = 'vatican-bav-pal-lat-586-'
        elif m[0] == 'B':
            collection = 'bamberg-sb-c-6'
            ms = 'bamberg-sb-c-6-'
        elif m[0] == 'K':
            collection = 'koeln-edd-c-119'
            ms = 'koeln-edd-c-119-'


        # Get xml-document containing list of abbreviatins as choice elements via xquery stored on exist server...
        url = base_url + collection + '/' + ms + str(booknumber).zfill(2) + '.xml'

        # ...post export request, starts export and returns xml...
        export_request = session.get(url, auth=HTTPBasicAuth(user, pw))
        export_request = export_request.text

        with open('./xml/' + ms + str(booknumber).zfill(2) + '.xml', "w") as text_file:
            text_file.write(export_request)


def get_arguments_from_cli():
    parser = argparse.ArgumentParser(
        description='Download, convert and collate manuscripts stored in existdb.')
    parser.add_argument('siglum', metavar='S', help='Angabe der Handschriften-Siglen und Kapitelrange, z.B. "F 70-94, V 70-94, B 70-94, K 70-94"')
    parser.add_argument('book', metavar='B', type=int, help='Angabe der Buchnummer')
    parser.add_argument('-dl', help='Download?', action='store_true')
    args = parser.parse_args()

    # creating sigla and page range from arguments
    argument_cli = args.siglum
    booknumber = args.book
    arguments = argument_cli.split(",")
    download = args.dl
    manuscripts = []
    for argument in arguments:
        argument = argument.strip()
        sigla, page_range = argument.split()
        page_min, page_max = page_range.split("-")
        manuscript = (sigla, page_min, page_max)
        manuscripts.append(manuscript)
    return manuscripts, booknumber, download


class Manuscript():

    def __init__(self, m, booknumber):
        self.booknumber = booknumber
        self.sigla = m[0]
        self.chapter_min = m[1]
        self.chapter_max = m[2]
        self.filename = ""
        self.get_filename()
        self.tree = LET.parse(self.filename)
        self.root = self.tree.getroot()
        self.create_plain_text()
         

    def get_filename(self):
        if self.sigla == 'F':
            ms = 'frankfurt-ub-b-50-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'V':
            if self.booknumber < 8:
                ms = 'vatican-bav-pal-lat-585-' + str(self.booknumber).zfill(2) + '.xml'
            else:
                ms = 'vatican-bav-pal-lat-586-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'B':
            ms = 'bamberg-sb-c-6-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'K':
            ms = 'koeln-edd-c-119-' + str(self.booknumber).zfill(2) + '.xml'

        self.filename = config.cwd + "xml/" + ms


    def element_to_plain_text(self, i):
        xpath = "//tei:div[@type='chapter'][@n='" + str(i) + "']"
        chapter = self.root.xpath(xpath, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        element = chapter[0]
        xslt_root = LET.XML(config.xslt)
        transform = LET.XSLT(xslt_root)
        newdom = str(transform(element))
        return newdom


    def preprocessing_witness(self, witness):
        """ Normalises files for a more meaningful collation
        """

        witness = witness.lower()
        while '  ' in witness:
            witness = witness.replace('  ',' ')
        witness = re.sub('\s+',' ',witness)
        witness = re.sub('\s+\+','',witness)

        for character in config.characters_to_normalise:  
            witness = witness.replace(character[0], character[1])

        return witness


    def create_plain_text(self):
        # iterate through chapters
        i = int(self.chapter_min)
        while i <= int(self.chapter_max):
            print(f"Processing Chapter {str(i)}")
            plain_text = self.element_to_plain_text(i)
            normalised_text = self.preprocessing_witness(plain_text)
            print(normalised_text)
            # write plain text to file
            filename = f"witnesses/{str(self.booknumber).zfill(2)}/{self.sigla}_book_{str(self.booknumber).zfill(2)}_chapter_{str(i).zfill(3)}_normalised.txt"
            with open(filename, 'w+') as file:
                file.write(normalised_text)
            i += 1


class Collation:

    def __init__(self, manuscripts, booknumber):
        self.booknumber = booknumber
        self.manuscripts = manuscripts
       

    def collate_chapters(self):
        number_of_chapters = []
        sigla = ""
        for m in self.manuscripts:
            sigla = sigla + "_" + m[0]
            chapter_min = m[1]
            chapter_max = m[2]
            number_of_chapter = int(m[2])-int(m[1])
            number_of_chapters.append(number_of_chapter)
        
        sigla = sigla[1:]
        
        if len(set(number_of_chapters)) > 1:
            print("Unequal chapter numbers in collation")
            
        i = 1
        while i <= number_of_chapters[0]:
            string_of_filenames, chapternumber = self.append_filenames(i)
            json_filename = config.cwd + 'output/' + sigla + "_" + str(self.booknumber).zfill(2) + "_chapter_" + str(chapternumber).zfill(3) + '.json'
            html_filename = config.cwd + 'output/' + sigla + "_" + str(self.booknumber).zfill(2) + "_chapter_" + str(chapternumber).zfill(3) + '.html'
            execute = 'java -jar ' + config.cwd + 'collatex/collatex-tools-1.7.1.jar -f json -o ' + json_filename + string_of_filenames
            print(execute)
            os.system(execute)        
            self.chapter_to_html(json_filename, html_filename, chapternumber)
            self.output_html(html_filename)
            i+=1


    def chapter_to_html(self, json_filename, html_filename, chapternumber):
        ms_string = ""
        sigla_html = '<html><body><table style="width:96%;"><tbody><tr>'

        for m in self.manuscripts:
            sigla_html = sigla_html + '<th>' + m[0] + "(" + str(chapternumber) + ")" + '</th>'
        sigla_html = sigla_html + '</tr>'
        table_html = sigla_html

        with open(json_filename) as json_file:
            data = json.load(json_file)
        i = 0
        while i < len(data['table']):
            table_html = table_html + '<tr>'
            e = 0
            while e < len(self.manuscripts):
                cell = '<td>' + "".join(data['table'][i][e]) + '</td>'
                table_html = table_html + cell
                e += 1
            table_html = table_html + '</tr>'
            i += 1
        table_html = table_html + '</table><script>function isChecked(elem) {elem.parentNode.parentNode.style.backgroundColor = (elem.checked) ? \'white\' : \'red\';}</script></body></html>'
        table_html = table_html.replace('   </td>','</td>')
        table_html = table_html.replace('  </td>','</td>')
        table_html = table_html.replace(' </td>','</td>')

        with open(html_filename,'w') as html_output:
            html_output.write(table_html)


    def output_html(self, html_filename):
        """ Creates final html table

        """

        with open(html_filename) as f:
            # open collation file in markdown format
            html = f.read()

            soup = BeautifulSoup(html, 'lxml')

            rows = soup.find("table").find("tbody").find_all("tr")
            e = 1
            for row in rows:
                cells = row.find_all("td")
                cells_to_evaluate = []
                for cell in cells:
                    text_cell = cell.get_text()
                    text_cell = re.sub('\s+',' ',text_cell).strip()
                    cells_to_evaluate.append(text_cell)
                print(cells_to_evaluate)
                print(len(set(cells_to_evaluate)))
                if len(set(cells_to_evaluate)) > 1:
                    row['style'] = 'background-color:red;'

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

            with open(html_filename.replace('.html', '_final.html'),'w') as save:
                save.write(str(soup))


    def append_filenames(self, i):
        string_of_filenames = ""
        
        for m in self.manuscripts:
            chapternumber = int(m[1]) -1 + i
            print(chapternumber)
            if m[0] == 'F':
                ms = config.cwd + f"witnesses/{str(self.booknumber).zfill(2)}/{m[0]}_book_{str(self.booknumber).zfill(2)}_chapter_{str(chapternumber).zfill(3)}_normalised.txt"
            elif m[0] == 'V':
                    ms = config.cwd + f"witnesses/{str(self.booknumber).zfill(2)}/{m[0]}_book_{str(self.booknumber).zfill(2)}_chapter_{str(chapternumber).zfill(3)}_normalised.txt"
            elif m[0] == 'B':
                ms = config.cwd + f"witnesses/{str(self.booknumber).zfill(2)}/{m[0]}_book_{str(self.booknumber).zfill(2)}_chapter_{str(chapternumber).zfill(3)}_normalised.txt"
            elif m[0] == 'K':
                ms = config.cwd + f"witnesses/{str(self.booknumber).zfill(2)}/{m[0]}_book_{str(self.booknumber).zfill(2)}_chapter_{str(chapternumber).zfill(3)}_normalised.txt"

            string_of_filenames = string_of_filenames + ' ' + ms
            
        return string_of_filenames, chapternumber


def main():
    # Get variables from console
    # example "python collation 'V 70-94, F 70-94, B 70-94, K 70-94' 1 -dl"
    manuscripts, booknumber, download = get_arguments_from_cli()
    
    if download == True:
        # Daten aus Exist ziehen
        get_xml_from_exist(manuscripts, booknumber)
    
    for m in manuscripts:
        # prepare witnesses
        manuscript = Manuscript(m, booknumber)

    # collate
    collate_witnesses = Collation(manuscripts, booknumber)
    collate_witnesses.collate_chapters()

    
if __name__ == '__main__':
    main()