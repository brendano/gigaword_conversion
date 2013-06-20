#!/usr/bin/env python
r"""
Convert Stanford CoreNLP XML files into json document ('jdoc') format:
one line (record) per document.

'jdoc' has three fields

    DocID \t ShallowInfo \t DeepInfo

DocID is a bare string
ShallowInfo and DeepInfo are both JSON.
ShallowInfo is smaller, more like bare text, and intended for quicker
processing.  It is a repetitive subset of DeepInfo, but it's 10x smaller.
DeepInfo has 'sentences' and 'entities':
 * sentence-level parse/syntax info
 * list of entities (and
relations? etc.) for deeper processing.

There's also a 'jsent' format (one line per sentence):
    DocID \t SentID \t Text \t SentInfo
where SentInfo is JSON, and the others are strings.
Currently 'Text' is a space-tokenized version of the text.

In 'jsent', discourse-level info is awkward to include.
Currently entities are encoded as separate records.
    DocID \t EntID \t EntInfo

Commandline usage is stdin/stdout.

Note:
Stanford's XML format is 1-indexed for both sentences and tokens
This script converts everything to 0-indexed for convenience.
"""
import sys,os,re,itertools
import xml.etree.ElementTree as ET
import json

try:
    import ujson
    def mydumps(x, *args, **kwargs):
        # README on https://github.com/esnme/ultrajson
        kwargs['ensure_ascii'] = False
        return ujson.dumps(x, *args, **kwargs)
except ImportError:
    def mydumps(x, *args, **kwargs):
        return json.dumps(x, separators=(',',':'), *args, **kwargs)

def convert_to_unicode(mystr):
    if isinstance(mystr, unicode):
        return mystr
    if isinstance(mystr, str):
        return mystr.decode('utf8')
    if mystr is None:
        return u''
    assert False, "wtf is " + repr(mystr)

def convert_corexml_sentences(doc_x, deptype='collapsed-ccprocessed-dependencies'):
    """doc_x is an ElementTree object (document or node?)"""
    sents_x = doc_x.find('document').find('sentences').findall('sentence')
    sents = []
    for sent_x in sents_x:
        sent_infos = {}
        toks_x = sent_x.findall(".//token")
        # toks_j = [(t.findtext(".//word"), t.findtext(".//lemma"), t.findtext(".//POS"), t.findtext(".//NER")) for t in toks_x]
        # sent_infos['tokens'] = toks_j

        sent_infos['tokens'] = [t.findtext(".//word") for t in toks_x]
        sent_infos['lemmas'] = [t.findtext(".//lemma") for t in toks_x]
        sent_infos['pos'] = [t.findtext(".//POS") for t in toks_x]
        sent_infos['ner'] = [t.findtext(".//NER") for t in toks_x]

        char_offsets = []
        for t in toks_x:
            start = int(t.findtext('CharacterOffsetBegin'))
            end = int(t.findtext('CharacterOffsetEnd'))
            char_offsets.append( (start,end) )
        sent_infos['char_offsets'] = char_offsets

        deps_x = sent_x.find('.//' +deptype)
        #deps_x = sent_x.find('.//collapsed-dependencies')
        #deps_x = sent_x.find('.//basic-dependencies')
        if deps_x is not None:
            deps_j = []
            for dep_x in deps_x.findall('.//dep'):

                # the version in Annotated Gigaword looks like
                # <dep type="nsubj">
                #   <governor>4</governor>
                #   <dependent>2</dependent>
                # </dep>

                # the version when I run CoreNLP myself looks like this, and seems to be 0-indexed.
                # <dep type="prt">
                #   <governor idx="3">washed</governor>
                #   <dependent idx="4">up</dependent>
                # </dep>

                gov = dep_x.find('.//governor')
                gi = int(gov.get('idx')) - 1 if gov.get('idx') is not None else int(gov.text) -1
                dept= dep_x.find('.//dependent')
                di = int(dept.get('idx')) - 1 if dept.get('idx') is not None else int(dept.text) -1
                # tupl = [dep_x.get('type'), di,gi]  ## my old format was [dep,gov]
                tupl = [dep_x.get('type'), gi,di]    ## but [gov,dep] seems more standard
                deps_j.append(tupl)
            sent_infos['deps'] = deps_j
        if sent_x.findtext(".//parse") is not None:
            # normalize the sexpr
            parse = sent_x.findtext(".//parse").strip()
            parse = re.sub(r'\s+', ' ', parse)
            sent_infos['parse'] = parse
        sents.append(sent_infos)

    return sents

### Entity coref conversion

class Entity(dict):
    def __hash__(self):
        return hash('entity::' + self['id'])

def convert_corexml_coref(doc_etree, sentences):
    coref_x = doc_etree.find('document').find('coreference')
    if coref_x is None:
        return []

    entities = []
    for entity_x in coref_x.findall('coreference'):
        mentions = []
        for mention_x in entity_x.findall('mention'):
            m = {}
            m['sentence'] = int(mention_x.find('sentence').text) - 1
            m['start'] = int(mention_x.find('start').text) - 1
            m['end'] = int(mention_x.find('end').text) - 1
            m['head'] = int(mention_x.find('head').text) - 1
            mentions.append(m)
        ent = Entity()
        ent['mentions'] = mentions
        first_mention = min((m['sentence'],m['head']) for m in mentions)
        ent['first_mention'] = first_mention
        # ent['id'] = '%s:%s' % first_mention
        entities.append(ent)
    entities.sort()
    for i in range(len(entities)):
        ent = entities[i]
        ent['num'] = i
        s,pos = ent['first_mention']
        ent['id'] = "E%s" % i
        # ent['nice_name'] = sentences[s]['tokens'][pos]['word']

    return entities


### Everything below is to input different formats of the corexml
### except annotated gigaword

def corexml_inputter():
    """with autodetection"""
    firstline = sys.stdin.readline()
    if '\t' in firstline:
        print>>sys.stderr, "Assuming input is TSV version of CoreXML"
        fn = corexmls_from_tsv
    else:
        print>>sys.stderr, "Assuming input is CoreXML filenames"
        fn = corexmls_from_files
    gen = itertools.chain([firstline], sys.stdin)
    gen = (L.rstrip('\n') for L in gen)
    for item in fn(gen):
        yield item

def smartopen(filename):
    if filename.endswith('.gz'):
        import gzip
        return gzip.open(filename)
    else:
        return open(filename)

def corexmls_from_files(linegen):
    for doc_i,filename in enumerate(linegen):
        if doc_i % 100==0: sys.stderr.write('.')
        data = smartopen(filename).read().decode('utf-8','replace').encode('utf-8')
        s = filename
        s = os.path.basename(s)
        s = re.sub(r'\.gz$', '', s)
        s = re.sub(r'\.xml$','',s)
        s = re.sub(r'\.txt$','',s)
        docid = s
        yield docid, data

def corexmls_from_tsv(linegen):
    for line in linegen:
        parts = line.split('\t')
        if len(parts)<2:
            print>>sys.stderr, "skipping line starting with: ", line[:50]
            continue
        docid = '\t'.join(parts[:-1])
        data = parts[-1]
        yield docid, data

def convert_corexml_document(xm):
    """ 'xm' is a parsed XML document """
    sentences = convert_corexml_sentences(xm)
    entities = convert_corexml_coref(xm, sentences)
    return sentences,entities


## Outputter routines

def output_sentents_as_jdoc(docid, sentences, entities):
    """One line per document."""
    print "{docid}\t{shallow_info}\t{full_info}".format(
            docid = docid,
            shallow_info = mydumps({'sentences': [{'spacetok': sent_text} for sent_text in sent_texts]}),
            full_info = mydumps({'sentences':sentences, 'entities':entities}),
    )

def output_sentents_as_jsent(docid, sentences, entities):
    """One line per sentence.  (And entity.)"""
    for sent_i,sent_info in enumerate(sentences):
        print u"{docid}\t{sentid}\t{sent_text}\t{sent_info}".format(
                docid = docid,
                sentid="S{}".format(sent_i),
                sent_text = u' '.join(t for t in sent_info['tokens']),
                sent_info = mydumps(sent_info).decode('utf8')
            ).encode('utf8')
    for ent in entities:
        print "{docid}\t{entid}\t{ent_info}".format(
                docid=docid, entid=ent['id'], ent_info=mydumps(ent))

def do_output(output_format, docid, sentences, entities):
    outputter = eval('output_sentents_as_' + output_format)
    outputter(docid, sentences, entities)

def corexml_mainloop(args):
    Ndoc, Nsent, Nent = 0,0,0

    for docid,data in corexml_inputter():
        try:
            doc_etree = ET.fromstring(data)
        except ET.ParseError:
            print>>sys.stderr, "XML parse failed on doc: ",docid
            continue

        sentences, entities = convert_corexml_document(doc_etree)

        # for sent in sentences: sent['docid'] = docid
        # for ent in entities: ent['docid'] = docid

        do_output(args.output_format, docid, sentences, entities)

        Ndoc += 1
        Nsent += len(sentences)
        Nent += len(entities)
    print>>sys.stderr, "\nProcessed {} documents, {} sentences, {} entities".format(Ndoc, Nsent, Nent)

#################################################

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


def annogw_mainloop(args):
    for doclines in yield_annogw_doclines(sys.stdin):
        d = get_annogw_shallowinfo(doclines)
        if d['corexml']:
            xml = ET.fromstring(d['corexml'])
            sentences, entities = convert_corexml_document(xml)
        else:
            sentences, entities = [], []
        deep_info = {'sentences':sentences, 'entities':entities}

        print '{docid}\t{shallow_info}\t{deep_info}'.format(
            docid=d['docinfo']['id'], 
            shallow_info=mydumps({'docinfo':d['docinfo'], 'sentences':d['sentences']}),
            deep_info=mydumps(deep_info))


if __name__=='__main__':
    import argparse; p=argparse.ArgumentParser()
    p.add_argument('input_format', choices=['corexml','annogw'], default='corexml')
    p.add_argument('output_format', choices=['jdoc','jsent','shallow'], default='jdoc')
    args = p.parse_args()
    if args.input_format=='corexml':
        corexml_mainloop(args)
    elif args.input_format=='annogw':
        annogw_mainloop(args)



