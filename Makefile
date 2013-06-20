# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
DATADIR  := /cab1/corpora/gigaword_5_anno/data
INPUTS 	 := $(wildcard $(DATADIR)/*.xml.gz)
SENTJSON := $(INPUTS:.xml.gz=.sentjson)
DOCID 	 := $(INPUTS:.xml.gz=.docid)

sentjson: $(SENTJSON)
docid: $(DOCID)

doc_counts.txt: $(DOCID)
	grep -Po 'type=".*?"' $(DOCID) | sort -S5G | uniq -c > doc_counts.txt

%.sentjson: %.xml.gz
	cat $< | zcat | python2.7 annogw2justsent.py > $@

%.sentjson.gz: %.sentjson
	gzip $<

%.docid: %.xml.gz
	zgrep '^<DOC ' $< > $@
