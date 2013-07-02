# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
DATADIR  := /usr/users/9/brenocon/s/sem/gigaword_5_anno/data
INPUTS 	 := $(wildcard $(DATADIR)/*.xml.gz)
JUSTSENT := $(INPUTS:.xml.gz=.justsent)
JDOC     := $(INPUTS:.xml.gz=.jdoc)
DOCID 	 := $(INPUTS:.xml.gz=.docid)

justsent: $(JUSTSENT)
jdoc: $(JDOC)
docid: $(DOCID)
meta: $(JDOC:.jdoc=.meta)

doc_counts.txt: $(DOCID)
	grep -Po 'type=".*?"' $(DOCID) | sort -S5G | uniq -c > doc_counts.txt

%.meta: %.jdoc
	env LC_ALL=C cat $< | cut -f1-2 > $@

%.justsent: %.xml.gz
	zcat $< | python2.7 annogw2json.py justsent > $@

%.justsent.gz: %.justsent
	gzip $<

%.jdoc: %.xml.gz
	zcat $< | python2.7 annogw2json.py full > $@

%.jdoc.gz: %.jdoc
	gzip $<

%.docid: %.xml.gz
	zgrep '^<DOC ' $< > $@
