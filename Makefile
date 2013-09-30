# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
DATADIR  := /cab1/corpora/gigaword_5_anno/data
INPUTS 	 := $(wildcard $(DATADIR)/*.xml.gz)
JUSTSENT := $(INPUTS:.xml.gz=.justsent)
JDOC     := $(INPUTS:.xml.gz=.jdoc)
DOCID 	 := $(INPUTS:.xml.gz=.docid)

# mass conversion commands
justsent: $(JUSTSENT)
jdoc: $(JDOC)
docid: $(DOCID)
SX := $(INPUTS:.xml.gz=.sentxml)
sentxml: $(SX)

doc_counts.txt: $(DOCID)
	grep -Po 'type=".*?"' $(DOCID) | sort -S5G | uniq -c > doc_counts.txt

%.justsent: %.xml.gz
	zcat $< | python2.7 annogw2json.py justsent > $@

%.justsent.gz: %.justsent
	gzip $<

%.jdoc: %.xml.gz
	zcat $< | python2.7 annogw2json.py full > $@

%.docid: %.xml.gz
	zgrep '^<DOC ' $< > $@

%.sentxml: %.justsent
	cat $< | python2.7 sentjson2xml.py > $@
