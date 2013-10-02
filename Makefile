# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
# DATADIR  := /usr/users/9/brenocon/s/sem/gigaword_5_anno/data
DATADIR  := gw/data
##DATADIR  := gw/data_without_apw
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
meta: $(JDOC:.jdoc=.meta)

doc_counts.txt: $(DOCID)
	grep -Po 'type=".*?"' $(DOCID) | sort -S5G | uniq -c > doc_counts.txt

%.meta: %.jdoc
	env LC_ALL=C cat $< | cut -f1-2 > $@

%.justsent: %.jdoc
	zcat $< | python2.7 jdoc2justsent.py > $@

%.jdoc: %.xml.gz
	zcat $< | python2.7 annogw2json.py full > $@
	touch $@.done

%.docid: %.xml.gz
	zgrep '^<DOC ' $< > $@
	touch $@.done

%.sentxml: %.justsent
	cat $< | python2.7 sentjson2xml.py > $@
	touch $@.done
