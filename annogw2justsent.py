import sys,os,re,itertools
import xml.etree.ElementTree as ET
import json
import parsetools

# XML_PARSER = ET.XMLParser(encoding="utf-8")

try:
    import ujson
    def mydumps(x, *args, **kwargs):
        # README on https://github.com/esnme/ultrajson
        kwargs['ensure_ascii'] = False
        return ujson.dumps(x, *args, **kwargs)
except ImportError:
    def mydumps(x, *args, **kwargs):
        return json.dumps(x, separators=(',',':'), *args, **kwargs)

def smartopen(filename):
    if filename.endswith('.gz'):
        import gzip
        return gzip.open(filename)
    else:
        return open(filename)

def yield_annogw_docstr(stream):
    cur_doclines = []
    has_started = False
    for line in stream:
        line = line.rstrip('\n')
        if not line: continue
        if line.startswith('<DOC'):
            has_started = True
        if not has_started: continue
        cur_doclines.append(line)
        if line == '</DOC>':
            yield '\n'.join(cur_doclines)
            cur_doclines = []
    if cur_doclines and cur_doclines[0].startswith('<DOC'):
        yield '\n'.join(cur_doclines)

def create_text_object_from_parse(parsestr):
    parsestr = convert_to_unicode(parsestr).encode('utf8')
    parsestr = re.sub(r'\s+', ' ', parsestr)
    parsestr = parsestr.strip()
    parsestr = parsestr.decode('utf8')
    try:
        parse = parsetools.parse_sexpr(parsestr)
        return {'tokens': parsetools.terminals(parse),
                'parse': parsestr}
    except parsetools.BadSexpr:
        return {'text': parsestr}

unicode_counts = {'x':0, 'n':0}
def convert_to_unicode(mystr):
    unicode_counts['n'] += 1
    if isinstance(mystr, unicode):
        unicode_counts['x'] += 1
        return mystr
    if isinstance(mystr, str):
        return mystr.decode('utf8')
    if mystr is None:
        return u''
    assert False, "wtf is " + repr(mystr)

def process_sentences(sentences_x):
    for sentence_x in sentences_x:
        tokens = []
        for token_x in sentence_x.find('tokens'):
            wordstr = token_x.find('word').text
            # it's nondeterministic. sometimes a string, sometimes a unicode. WTF!
            wordstr = convert_to_unicode(wordstr)
            wordstr = wordstr.strip()
            tokens.append(wordstr)
        yield {'tokens': tokens}


# def process_file(filename):
#     process_stream(smartopen(filename))

def process_stream(stream):
    for docstr in yield_annogw_docstr(stream):
        # docstr = docstr.decode('utf8','ignore').encode('utf8')
        doc_x = ET.fromstring(docstr)
        # doc_x = XML_PARSER.fromstring(docstr)
        out_meta = {}
        out_meta.update( dict(doc_x.items()) )
        out_sentences = []
        for topchild in doc_x:
            tag = topchild.tag
            if tag=='HEADLINE' or tag=='DATELINE':
                out_meta[tag.lower()] = create_text_object_from_parse(topchild.text)
            elif tag=='TEXT':
                pass
            elif tag=='coreferences':
                pass
            elif tag=='sentences':
                for sentinfo in process_sentences(topchild):
                    out_sentences.append(sentinfo)
            else:
                assert False, "dunno what to do with XML node type " + tag

        print "%s\t%s\t%s" % (out_meta['id'], mydumps(out_meta), mydumps(out_sentences))

        # bigdict = out_meta
        # bigdict['sentences'] = out_sentences
        # print "%s\t%s" % (out_meta['id'], mydumps(bigdict))
    print>>sys.stderr, "num ET-gives-unicode tokens", unicode_counts

def main():
    process_stream(sys.stdin)

    # for filename in sys.argv[1:]:
    #     process_file(filename)

if __name__=='__main__':
    main()
