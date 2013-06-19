# run 'make' or 'make -j16' or whatever from this directory.
# but first edit this path
DATADIR := /cab1/corpora/gigaword_5_anno/data
INPUTS := $(wildcard $(DATADIR)/*.xml.gz)
OUTPUTS := $(INPUTS:.xml.gz=.sentjson)

all: $(OUTPUTS)

%.sentjson: %.xml.gz
	time cat $< | zcat | python2.7 annogw2justsent.py > $@

%.sentjson.gz: %.sentjson
	gzip $<

