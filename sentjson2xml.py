"""
input: 'sentjson' format (from annogw2json.py)
output format is tokens-only, and XML
preserve headlines vs body distinction .. why not
"""

import sys,re
import ujson as json
from xml.sax.saxutils import escape

def emit_str(xmlstr):
    print xmlstr

print '<documents>'
for line in sys.stdin:
    docid,headjson,bodyjson = line.rstrip('\n').split('\t')
    head_dat = json.loads(headjson)
    body_dat = json.loads(bodyjson)
    datestr = re.search(r'_(\d\d\d\d\d\d\d\d)\.', docid).group(1)
    ymd = "{}-{}-{}".format(datestr[:4], datestr[4:6], datestr[6:8])
    print '<document id="{}" pubdate="{}" type="{}">'.format(
            docid, ymd, head_dat['type'])
    for k in ['headline','dateline']:
        if k in head_dat:
            print '<%s>' % k
            head_spacetok = u' '.join(head_dat[k]['tokens'])
            print escape(head_spacetok.encode('utf8'))
            print '</%s>' % k

    print '<sentences>'

    for i,sent in enumerate(body_dat):
        spacetok = u' '.join(sent['tokens'])
        print '<sentence id="body:{}">'.format(i)
        print escape(spacetok.encode('utf8'))
        print '</sentence>'

    print '</sentences>'

    print '</document>'
print '</documents>'
