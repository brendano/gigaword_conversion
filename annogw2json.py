import sys,os,re,itertools
import xml.etree.ElementTree as ET
import json
import parsetools
try:
    import core2json
except ImportError:
    pass

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
        if line.startswith('<DOC '):
            has_started = True
        if not has_started: continue
        cur_doclines.append(line)
        if line.strip() == '</DOC>':
            yield '\n'.join(cur_doclines)
            cur_doclines = []
    if cur_doclines and cur_doclines[0].startswith('<DOC '):
        yield '\n'.join(cur_doclines)

def create_text_object_from_parse(parsestr):
    parsestr = convert_to_unicode(parsestr).encode('utf8')
    parsestr = re.sub(r'\s+', ' ', parsestr)
    parsestr = parsestr.strip()
    parsestr = parsestr.decode('utf8')
    if not parsestr:
        return {'tokens':[], 'parse':parsestr}
    try:
        parse = parsetools.parse_sexpr(parsestr)
        return {'tokens': parsetools.terminals(parse),
                'parse': parsestr}
    except parsetools.BadSexpr:
        return {'text': parsestr, 'sexpr_parse_failed':True}

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

def process_sentences_justsent(sentences_x):
    for sentence_x in sentences_x:
        tokens = []
        for token_x in sentence_x.find('tokens'):
            wordstr = token_x.find('word').text
            # it's nondeterministic. sometimes a string, sometimes a unicode. WTF!
            wordstr = convert_to_unicode(wordstr)
            wordstr = wordstr.strip()
            tokens.append(wordstr)
        yield {'tokens': tokens}

def process_sentences_full(sentences_x):
    return core2json.convert_corexml_sentences_fromnode(sentences_x)

def process_stream(stream, mode):
    for docstr in yield_annogw_docstr(stream):
        # docstr = docstr.decode('utf8','ignore').encode('utf8')
        try:
            doc_x = ET.fromstring(docstr)
        except ET.ParseError:
            print>>sys.stderr, "XML PARSE ERROR, str length %s, start:\t%s" % (len(docstr), repr(docstr[:100]))
            continue
        out_meta = {}
        out_meta.update( dict(doc_x.items()) )
        out_sentences = []
        out_entities = None
        for topchild in doc_x:
            tag = topchild.tag
            if tag=='HEADLINE' or tag=='DATELINE':
                out_meta[tag.lower()] = create_text_object_from_parse(topchild.text)
            elif tag=='TEXT':
                pass
            elif tag=='coreferences' or tag=='coreference':
                # the file nyt_eng_199710.xml has <coreference> instead of
                # <coreferences> in the topchidld.  didn't see this in any
                # other file. argh!
                if mode=='full':
                    out_entities = core2json.convert_corexml_coref_fromnode(topchild, out_sentences)
                else:
                    pass
            elif tag=='sentences':
                f = eval('process_sentences_' + mode)
                for sentinfo in f(topchild):
                    out_sentences.append(sentinfo)
            else:
                assert False, "dunno what to do with XML node type " + tag

        payload = out_sentences if mode=='justsent' else {'sentences':out_sentences, 'entities':out_entities} if mode=='full' else None
        assert payload is not None
        print "%s\t%s\t%s" % (out_meta['id'], mydumps(out_meta), mydumps(payload))

procname = None
def main():
    import argparse; p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['full','justsent'])
    args = p.parse_args()
    process_stream(sys.stdin, mode=args.mode)

if __name__=='__main__':
    main()
