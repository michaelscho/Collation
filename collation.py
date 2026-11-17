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
import subprocess


def get_xml_from_exist(manuscripts, booknumber):
    """
        Download TEI XML documents from eXist-db.

        Retrieves the XML file for each requested witness and book
        using the WebDAV URL and credentials defined in config.py.

        The downloaded files are saved in the local xml/ directory.

        Args:
            manuscripts: List of tuples (siglum, chapter_min, chapter_max).
            booknumber: Number of the book to download.
        """

    # Get eXist-db credentials and base URL
    user = config.user_exist
    pw = config.pw_exist
    base_url = config.base_url

    # Create an HTTP session
    session = requests.Session()

    for m in manuscripts:
        if m[0] == 'F':
            collection = 'frankfurt-ub-b-50'
            ms = 'frankfurt-ub-b-50-'
        elif m[0] == 'V':
            if booknumber <= 8:
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

        # Build the URL of the requested TEI XML document
        url = base_url + collection + '/' + ms + str(booknumber).zfill(2) + '.xml'

        # Download the XML document from eXist-db
        export_request = session.get(url, auth=HTTPBasicAuth(user, pw))
        export_request = export_request.text

        with open(os.path.join(os.path.dirname(__file__),'xml', ms + str(booknumber).zfill(2) + '.xml'), "w", encoding='utf8') as text_file:
            text_file.write(export_request)


def get_arguments_from_cli():
    """
    Parse command-line arguments for collation generation.

    Expected arguments:
        siglum: Witness sigla and chapter ranges, e.g.
                'V 1-10, F 1-10, B 1-10, K 1-10'.
        book: Book number.
        -dl: Optional flag to download XML files from eXist-db.

    Returns:
        tuple: (manuscripts, booknumber, download), where
        manuscripts is a list of (siglum, chapter_min, chapter_max)
        tuples and download is a boolean.
    """
    parser = argparse.ArgumentParser(
        description='Download, convert and collate manuscripts stored in existdb.')
    parser.add_argument('siglum', metavar='S', help='Angabe der Handschriften-Siglen und Kapitelrange, z.B. "F 70-94, V 70-94, B 70-94, K 70-94"')
    parser.add_argument('book', metavar='B', type=int, help='Angabe der Buchnummer')
    parser.add_argument('-dl', help='Download?', action='store_true')
    args = parser.parse_args()

    # Parse witness sigla and chapter ranges
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
    """
    Prepare manuscript texts for collation.

    Loads the TEI XML document for a witness, extracts the requested
    chapters, applies the configured XSLT transformation and text
    normalisation, and saves the resulting TXT files.

    The normalised texts are stored in witnesses/BOOK/.
    """

    def __init__(self, m, booknumber):
        self.booknumber = booknumber
        self.sigla = m[0]
        self.chapter_min = m[1]
        self.chapter_max = m[2]
        self.filename = ""
        self.get_filename()
        # Default XML parsing (strict)
        self.tree = LET.parse(self.filename)
        self.root = self.tree.getroot()

        # Alternative: recover from XML parsing errors. Tested with Book 16, where an invalid xml:id in a later chapter prevented the extraction of earlier chapters.
        # Use only for testing.
        #parser = LET.XMLParser(recover=True)
        #self.tree = LET.parse(self.filename, parser)
        #self.root = self.tree.getroot()

        self.create_plain_text()


    def get_filename(self):
        """
        Determine the local TEI XML filename for the current witness.

        Maps the manuscript siglum to its corresponding XML filename.
        For witness V, Books 1-8 use Pal. lat. 585, while later books
        use Pal. lat. 586.

        The resulting path is stored in self.filename.
        """
        if self.sigla == 'F':
            ms = 'frankfurt-ub-b-50-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'V':
            if self.booknumber <= 8:
                ms = 'vatican-bav-pal-lat-585-' + str(self.booknumber).zfill(2) + '.xml'
            else:
                ms = 'vatican-bav-pal-lat-586-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'B':
            ms = 'bamberg-sb-c-6-' + str(self.booknumber).zfill(2) + '.xml'
        elif self.sigla == 'K':
            ms = 'koeln-edd-c-119-' + str(self.booknumber).zfill(2) + '.xml'

        self.filename = os.path.join(os.path.dirname(__file__), "xml", ms)


    def element_to_plain_text(self, i):
        """
        Extract and transform a chapter from the TEI XML document.

        Chapter 0 corresponds to the Table of Contents (TOC).
        Other chapters are selected using their @n attribute.

        The selected TEI element is transformed using config.xslt.

        Args:
            i: Chapter number to extract.

        Returns:
            str: Text produced by the XSLT transformation,
            or None if chapter extraction fails.
        """
        if i==0:
            xpath = "//tei:div[@type='toc']"
            chapter = self.root.xpath(xpath, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})

            element = chapter[0]
            xslt_root = LET.XML(config.xslt)
            transform = LET.XSLT(xslt_root)
            newdom = str(transform(element))
        else:
            try:
                xpath = "//tei:div[@type='chapter'][@n='" + str(i) + "']"
                chapter = self.root.xpath(xpath, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
                element = chapter[0]
                xslt_root = LET.XML(config.xslt)
                transform = LET.XSLT(xslt_root)
                newdom = str(transform(element))
            except Exception as e:
                print(e)
                return
        
        return newdom


    def preprocessing_witness(self, witness):
        """
        Normalise extracted manuscript text before collation.

        Converts text to lowercase, normalises whitespace, removes
        whitespace followed by '+', and applies the character
        substitutions defined in config.characters_to_normalise.

        Args:
            witness: Extracted manuscript text.

        Returns:
            str: Normalised text ready for CollateX.
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
        """
        Generate normalised TXT files for the requested chapter range.

        Extracts and normalises each chapter, then saves it in
        witnesses/BOOK/ using the naming convention:

            SIGLUM_book_BOOK_chapter_CHAPTER_normalised.txt

        Displays progress information in the terminal.
        """
        # Iterate through chapters
        chapter_min = int(self.chapter_min)
        chapter_max = int(self.chapter_max)
        total_chapters = chapter_max - chapter_min + 1

        print(f"\nWitness {self.sigla} (chapters {chapter_min}-{chapter_max})")

        i = chapter_min
        while i <= chapter_max:
            plain_text = self.element_to_plain_text(i)
            normalised_text = self.preprocessing_witness(plain_text)

            # write plain text to file
            path_to_witness_folder = os.path.join(os.getcwd(), 'witnesses', f'{str(self.booknumber).zfill(2)}')
            #check if folder for book exists
            if not os.path.exists(path_to_witness_folder):
                os.mkdir(path_to_witness_folder)
            
            filename = os.path.join(path_to_witness_folder, f"{self.sigla}_book_{str(self.booknumber).zfill(2)}_chapter_{str(i).zfill(3)}_normalised.txt")
            with open(filename, 'w+', encoding='utf8') as file:
                file.write(normalised_text)

            current_chapter = i - chapter_min + 1
            print(f"  [{current_chapter}/{total_chapters}] Chapter {i} - Normalised")

            i += 1


class Collation:
    """
    Generate collation tables from normalised manuscript texts.

    Selects the available witnesses for each chapter, runs CollateX,
    converts the resulting JSON alignments into HTML tables, and
    creates the final HTML files.

    Intermediate and final files are stored separately in output/,
    with subdirectories organised by book number.
    """

    def __init__(self, manuscripts, booknumber):
        self.booknumber = booknumber
        self.manuscripts = manuscripts

    def collate_chapters(self):
        """
        Generate collation tables for the requested chapter ranges.

        Determines the overall chapter range and selects the witnesses
        available for each chapter. Chapters with fewer than two
        witnesses are skipped.

        For each chapter, the function:
        - Builds the input filenames and checks that they exist.
        - Runs CollateX to generate a JSON alignment.
        - Converts the JSON into an intermediate HTML table.
        - Generates the final HTML table.

        Processing stops if an input file is missing or CollateX fails.
        Progress information is displayed in the terminal.
        """

        chapter_min = min(int(m[1]) for m in self.manuscripts)
        chapter_max = max(int(m[2]) for m in self.manuscripts)

        # Display an overview of the requested collation
        total_chapters = chapter_max - chapter_min + 1
        witnesses = ", ".join(m[0] for m in self.manuscripts)

        print("\n" + "=" * 40)
        print(f"COLLATION - BOOK {self.booknumber:02d}")
        print("=" * 40)
        print(f"Witnesses: {witnesses}")
        print(f"Chapters: {chapter_min}-{chapter_max}")
        print()

        for chapter in range(chapter_min, chapter_max + 1):

            # Select witnesses available for this chapter
            active_manuscripts = [
                m for m in self.manuscripts
                if int(m[1]) <= chapter <= int(m[2])
            ]

            # Skip chapters with fewer than two witnesses
            if len(active_manuscripts) < 2:
                print(f"Skipping chapter {chapter}: fewer than two witnesses")
                continue

            sigla = "_".join(m[0] for m in active_manuscripts)

            current_chapter = chapter - chapter_min + 1

            print(f"[{current_chapter}/{total_chapters}] Chapter {chapter} - {sigla}")
            print("Running CollateX...", flush=True)

            # Define intermediate output directory
            intermediate_dir = os.path.join(
                os.path.dirname(__file__),
                'output',
                'intermediate',
                f'{self.booknumber:02d}'
            )
            os.makedirs(intermediate_dir, exist_ok=True)

            # Define output filenames
            base_filename = f"{sigla}_{self.booknumber:02d}_chapter_{chapter:03d}"

            json_filename = os.path.join(
                intermediate_dir, base_filename + '.json'
            )
            html_filename = os.path.join(
                intermediate_dir, base_filename + '.html'
            )

            # Get input files for active witnesses
            string_of_filenames = self.append_filenames(
                chapter, active_manuscripts
            )

            # Check that all normalised input files exist
            witness_dir = os.path.join(
                os.getcwd(),
                'witnesses',
                f'{self.booknumber:02d}'
            )

            for m in active_manuscripts:
                filename = os.path.join(
                    witness_dir,
                    f"{m[0]}_book_{self.booknumber:02d}_chapter_{chapter:03d}_normalised.txt"
                )

                if not os.path.isfile(filename):
                    print(f"\nERROR: Missing input file for chapter {chapter}.")
                    print(f"Witness: {m[0]}")
                    print(f"Expected file: {filename}")
                    print("Collation stopped before running CollateX.")
                    raise SystemExit(1)

            # Run CollateX
            execute = (
                    'java -jar "'
                    + os.path.join(
                os.path.dirname(__file__),
                'collatex',
                'collatex-tools-1.7.1.jar'
            )
                    + '" -f json -o "'
                    + json_filename
                    + '"'
                    + string_of_filenames
            )

            # Run CollateX and check for errors
            try:
                subprocess.run(execute, shell=True, check=True)

            except subprocess.CalledProcessError as e:
                print(f"\nERROR: CollateX failed while processing chapter {chapter}.")
                print(f"Exit code: {e.returncode}")
                print("Collation stopped. No HTML table will be generated for this chapter.")
                raise SystemExit(1)

            # Generate HTML tables only if CollateX completed successfully
            self.chapter_to_html(
                json_filename,
                html_filename,
                chapter,
                active_manuscripts
            )

            self.output_html(html_filename)


        # All chapters have been processed
        print("\n" + "=" * 40)
        print("Collation completed.")
        print("=" * 40)

    def chapter_to_html(self, json_filename, html_filename, chapternumber, manuscripts):
        """
        Convert a CollateX JSON alignment into an HTML table.

        Creates one column for each witness included in the current
        chapter and populates the table with the aligned text.

        Args:
            json_filename: Path to the CollateX JSON file.
            html_filename: Path for the intermediate HTML output.
            chapternumber: Number of the chapter being processed.
            manuscripts: List of witnesses included in the collation.
        """
        ms_string = ""
        sigla_html = '<html><body><table style="width:96%;"><tbody><tr>'

        for m in manuscripts:
            sigla_html = sigla_html + '<th>' + m[0] + "(" + str(chapternumber) + ")" + '</th>'
        sigla_html = sigla_html + '</tr>'
        table_html = sigla_html

        with open(json_filename, 'r', encoding='utf8') as json_file:
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

        with open(html_filename,'w', encoding='utf8') as html_output:
            html_output.write(table_html)


    def output_html(self, html_filename):
        """
        Post-process an intermediate HTML table and save the final version.

        Uses BeautifulSoup to identify rows containing textual variants
        and highlight them in red. Adds row numbers and checkboxes for
        manually marking reviewed rows.

        Saves the completed table in output/final/BOOK/ using the
        filename suffix _final.html.

        Args:
            html_filename: Path to the intermediate HTML file.
        """

        with open(html_filename, 'r', encoding='utf8') as f:
            # Read the intermediate HTML collation table
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

                if len(set(cells_to_evaluate)) > 1:
                    row['style'] = 'background-color:red;'

                e += 1

            y = 1
            for tr in soup.select('tr'):
                tds = tr.select('td')
                new_td = soup.new_tag('td')
                new_input = soup.new_tag('input', **{'type':'checkbox','id':'termsChkbx', 'onchange':'isChecked(this,\'sub1\')'})
                new_td.append(str(y))
                new_td.append(new_input)
                tr.append(new_td)
                y += 1

            # Create the folder for final HTML tables
            final_dir = os.path.join(
                os.path.dirname(__file__),
                'output',
                'final',
                f'{self.booknumber:02d}'
            )
            os.makedirs(final_dir, exist_ok=True)

            # Define the final HTML filename
            final_filename = os.path.basename(html_filename).replace('.html', '_final.html')
            final_path = os.path.join(final_dir, final_filename)

            # Save the final HTML table
            with open(final_path, 'w', encoding='utf8') as save:
                save.write(str(soup))

            print(f"Final HTML saved: {os.path.relpath(final_path, os.path.dirname(__file__))}")
            print()

    def append_filenames(self, chapter, manuscripts):
        """
        Build the input file arguments for CollateX.

        Constructs the paths to the normalised TXT files for the
        specified chapter and witnesses. Each path is enclosed in
        quotation marks for use in the Java command.

        Args:
            chapter: Chapter number.
            manuscripts: List of witnesses to be included.

        Returns:
            str: Space-separated, quoted TXT file paths.
        """
        path_to_witness_folder = os.path.join(
            os.getcwd(),
            'witnesses',
            f'{self.booknumber:02d}'
        )

        filenames = []

        for m in manuscripts:
            filename = os.path.join(
                path_to_witness_folder,
                f"{m[0]}_book_{self.booknumber:02d}_chapter_{chapter:03d}_normalised.txt"
            )

            filenames.append(f'"{filename}"')

        return " " + " ".join(filenames)


def main():
    """Execute the complete collation workflow.

    Parses command-line arguments, optionally downloads the TEI XML
    documents, prepares the normalised texts for each witness,
    and generates the collation tables.
    """
    # Get variables from console
    # TOC as 0
    # example "python collation.py 'V 70-94, F 70-94, B 70-94, K 70-94' 1 -dl"
    manuscripts, booknumber, download = get_arguments_from_cli()
    
    if download == True:
        # Download XML files if requested
        get_xml_from_exist(manuscripts, booknumber)

    print("\n" + "=" * 40)
    print(f"PREPARING WITNESSES - BOOK {booknumber:02d}")
    print("=" * 40)

    for m in manuscripts:
        # prepare witnesses
        manuscript = Manuscript(m, booknumber)

    # collate
    collate_witnesses = Collation(manuscripts, booknumber)
    collate_witnesses.collate_chapters()

    
if __name__ == '__main__':
    main()