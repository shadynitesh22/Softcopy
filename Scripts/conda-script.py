#!C:\Users\user\Web1\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'conda==4.2.7','console_scripts','conda'
__requires__ = 'conda==4.2.7'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('conda==4.2.7', 'console_scripts', 'conda')()
    )
