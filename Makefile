# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
DATADIR  := /cab1/corpora/gigaword_5_anno/data
INPUTS 	 := $(wildcard $(DATADIR)/*.xml.gz)
SENTJSON := $(INPUTS:.xml.gz=.sentjson)
JDOC     := $(INPUTS:.xml.gz=.jdoc)
DOCID 	 := $(INPUTS:.xml.gz=.docid)

sentjson: $(SENTJSON)
jdoc: $(JDOC)
docid: $(DOCID)

doc_counts.txt: $(DOCID)
	grep -Po 'type=".*?"' $(DOCID) | sort -S5G | uniq -c > doc_counts.txt

%.sentjson: %.xml.gz
	zcat $< | python2.7 annogw2json.py justsent > $@

%.sentjson.gz: %.sentjson
	gzip $<

%.jdoc: %.xml.gz
	zcat $< | python2.7 annogw2json.py full > $@

%.docid: %.xml.gz
	zgrep '^<DOC ' $< > $@
