#!/usr/bin/python
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 3 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
import sys
import os
from os.path import expanduser
import getpass

from xml.dom.minidom import parseString
from SafeInCloud.sic.decrypter import Decrypter
from SafeInCloud.sic.entry import Entry
from pykeepass import PyKeePass
import click

@click.command()
@click.argument('input_File', type=click.Path(exists=True))
@click.argument('target_file', type=click.Path())
@click.option('--password', prompt=True, hide_input=True)
def main(input_file, target_file, password):
    
    def matches( query, card ):
        try:
            if query is None:
                return True
    
            query = query.lower()
            if query in card['@title'].lower():
                return True
    
            # for field in card['field']:
            #     if query in field['@name'].lower():
            #         return True
    
            #     if '#text' in field and query in field['#text'].lower():
            #         return True
        except:
            pass
    
        return False
    
    if len(sys.argv) == 2:
        search = sys.argv[1]
    else:
        search = None
    
    
    db = Decrypter( input_file, password )
    kp = PyKeePass('New3.kdbx', password='test')
    kp.root_group.name = "test_title"
    kp.password = password
    entries = []
    try:
        xml = db.decrypt()
        xml = parseString(xml)
    except:
        print("cannot decrypt, maybe wrong password?")
        sys.exit(1)
    
    for node in xml.getElementsByTagName('card'):
        is_template = False
        if node.hasAttribute('template'):
            is_template = ( node.attributes['template'].value == 'true' )
    
        if not is_template:
            entries.append( Entry(node) )
    
    duplicate_check = set()
    for entry in entries:
    
        password = ""
        login = ""
        url = ""
        notes = ""
        # extract all types the fields and their value
        type_value = {entry.fields[x].type: entry.fields[x].value for x in entry.fields}
        # map the type of the field in safeincloud to the field type in pykeepass
        map_types = {"password": "password", "login": "username", "website": "url", "notes": "notes"}
        # username and password are required fields
        mapped_type_value =  {"username": "", "password": ""}
        # add all other fields with the new names
        mapped_type_value.update({map_types[x]: type_value[x] for x in type_value if x in map_types})
          
        # ensure that the title is unique 
        title = entry.title
        if title in duplicate_check:
            i = 2
            while title + str(i) in duplicate_check:
                i = i +1
            title = title + str(i)
            assert title not in duplicate_check
    
        # add entry to keepass file
        kp.add_entry(kp.root_group, title, **mapped_type_value)
        # add title to duplicate check
        duplicate_check.add(title)
    
    kp.save(target_file)
    print("file successful mapped")

if __name__ == "__main__":
    main()
