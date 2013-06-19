# intended to be symlinked whereever the data is...
# i dont know how to persuade Make to understand it should use other directories

DATADIR = /cab1/corpora/gigaword_5_anno/data

INPUTS := $(wildcard $(DATADIR)/*.xml.gz)
OUTPUTS := $(INPUTS:.xml.gz=.sentjson)

all: $(OUTPUTS)

%.sentjson: %.xml.gz
	time cat $< | zcat | python2.7 annogw2justsent.py > $@
