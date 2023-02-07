# Collation
Python library for collating witnesses in project BDD.

## Install
Clone the repository and copy config_template.py to `config.py`. 
Insert existdb username and password as well as url to existdb data in `config.py`. 
Also, insert path to sourcecode in `config.cwd`. Script uses xslt transformation to create plain text files can be specified in `config.xslt`. Characters that need to be normalized are set in `config.characters_to_normalise`. 

## Usage
Script can be called from commandline using sigla and chapter range that needs to be collated in single quotation marks, e.g. `'V 70-94, F 70-94, B 70-94, K 70-94'`. Table of COntent needs to be indicated as '0'. After that, the booknumber needs to be specified as an integer. If xml files need to be downloaded, add `-dl` flag at the end of command: `python collation.py 'V 70-94, F 70-94, B 70-94, K 70-94' 1 -dl`. Collations are stored in html files for each chapter in `./output/`.


## Todo
- automatisierter upload zu exist
- Dokumentation verbessern
