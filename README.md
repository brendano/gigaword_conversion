These are postprocessing scripts for Annotated English Gigaword v5 (which here we call "AGW").  It is [LDC2012T21](http://www.ldc.upenn.edu/Catalog/catalogEntry.jsp?catalogId=LDC2012T21), and the paper describing it is [Napoles, Gormley, van Durme, Proc. of AKBC-WEKEX 2012](https://akbcwekex2012.files.wordpress.com/2012/05/28_paper.pdf).  These scripts are by [Brendan O'Connor](http://brenocon.com), and please contact me with any concerns -- I'm trying to figure out the correct way to use this data.

AGW seems to have three possible fields for each article where text data can live:
  1. Headline
  2. Dateline
  3. Article body

Not every article has a headline, and most articles don't have datelines.

If you look at AGW's data, the article body has a full XML structure from
CoreNLP with all the annotation layers.  But the headline and dateline seem to
be more minimal, though always have constituent parses.  There's a funny thing
in that the constituent parse s-expressions are sometimes encoded a little
differently than other things -- I suspect this stems from the fact they use a
customized variant of CoreNLP in which they replace the Stanford Parser with a
different (faster) one.

Anyways I tried to normalize these things a little bit.

These scripts output a few different formats.

 - `jdoc`: a JSON formatting of the document with all annotations.  This is
 just a JSON translation of the XML, and is intended to preserve all
 information.  At least for me, I find it much faster to process (I've found
 the Python `ujson` and Java Jackson JSON libraries to be pretty quick).

 Format: one line per document.  Three tab-separated fields per line:

      DocID  \t  MetaInfo  \t  BodyFullInfo

 where 
 
   - DocID is just a string

   - MetaInfo is a JSON object with both metadata, as well as headline and/or
   dateline text data if they exist

   - BodyFullInfo contains info for all sentences, as well as coref-identified
   entities, in the document.


 - `justsent`: a JSON representation of just the sentences and raw word tokens
 from the body text.  Vastly smaller than `jdoc`.  One line per document, three
 tab-separated fields per line:

      DocID  \t  MetaInfo  \t  BodySentencesTokens

 - `sentxml`: an XML version of `justsent`.  This format adds a `pubdate`
 field, but that's derived just from a regex on the document ID.

 - various report-like data derviations, like `docid` (all document IDs for a
 month) or `meta` (just the meta data).

Everything is designed to take all the original `.xml.gz` files from the LDC
release in one big directory, and output dervived data with new suffixes.  Edit
the Makefile to point to it, then it can be used to process into the format you
want.  It takes hundreds of CPU-hours to convert the xml.gz files into anything
else.
