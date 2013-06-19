# -*- encoding: utf8 -*-
"""
Utilities for parse trees, Brendan O'Connor Nov 2011
Represents s-expressions simply as lists of lists and strings.
TODO should break out console visualization stuff into a new file?
TODO would be nice to add trace stripping in here

Console print example:
% echo '(ROOT (S (N bob) (VP (V is) (V running) )))' | python parsetools.py dump

bob is running 
N   V  V       
    VP-------- 
S------------- 
"""
import sys
from collections import namedtuple

def parse_sexpr(s, add_root=True):
  """Parse an s-expression into a nested list-of-lists-and-strings."""
  first_paren = s.find('(')
  if first_paren == -1:
    raise BadSexpr("no paren")
  s = s[first_paren:]
  tree = []
  stack = []  # top of stack (index -1) points to current node in tree
  stack.append(tree)
  curtok = ""
  depth = 0
  for c in s:
    if c=='(':
      new = []
      stack[-1].append(new)
      stack.append(new)
      curtok = ""
      depth += 1
    elif c==')':
      if curtok:
        stack[-1].append(curtok)
        curtok = ""
      stack.pop()
      curtok = ""
      depth -= 1
    #elif c.isspace():
    elif c in (' ','\t','\r','\n'):  ## dont want funny unicode ones?
      if curtok:
        stack[-1].append(curtok)
        curtok = ""
    else:
      curtok += c
    if depth<0: raise BadSexpr("Too many closing parens")
  if depth>0: raise BadSexpr("Didn't close all parens, depth %d" % depth)
  root = tree[0]
  # weird, treebank parses have an extra, unlabeled node on top
  if isinstance(root[0], list) and add_root:
    root = ["ROOT"] + root
  return root

class BadSexpr(Exception): pass

def is_balanced(s):
  if '(' not in s: return False
  d = 0
  for c in s:
    if c=='(': d += 1
    if c==')': d -= 1
    if d<0: return False
  return d==0

def node_is_leaf(node):
  return isinstance(node, (unicode,str))

def node_is_preterminal(node):
  return len(node)==2 and node_is_leaf(node[1]) ## e.g.  ['N', 'car']

def iter_parses(line_iter=sys.stdin, raw=False, parsed=False, both=False):
  """Yield parses from a file of possibly multiline parses."""
  assert raw or parsed or both, "Need to supply output mode"
  def result(cur):
    s = ''.join(cur)
    if raw:  return s
    if parsed: return parse_sexpr(s)
    if both: return s, parse_sexpr(s)
  paren_count = 0
  cur = []
  for line in line_iter:
    if not line.strip(): continue
    cur.append(line)
    for c in line:
      if c=='(': paren_count += 1
      if c==')': paren_count -= 1
    if paren_count==0 and cur:
      yield result(cur)
      cur = []
  if cur:
    yield result(cur)

def terminals(tree):
  "The terminals (leaves) of the tree, in order."
  if node_is_leaf(tree):
    return [tree]
  leaves = []
  for child in tree[1:]:
    leaves += terminals(child)
  return leaves

def preterminals(tree):
  if node_is_leaf(tree):
    assert False, "shouldnt be here"
    return []
  # was len(tree)==2 but (CD 412 682 6878) violates .. encoding issue??
  if len(tree)>=2 and node_is_leaf(tree[1]):
    return [tree]
  ret = []
  for child in tree[1:]:
    ret += preterminals(child)
  return ret

def fix_preterminals(tree):
  preterms = preterminals(tree)
  for p in preterms:
    if len(p) > 2:
      assert False, "WTF"

def bfs_walk(tree):
  """Yields pointers to tree positions, so node_is_preterminal and node_is_leaf work.
  Need to take node[0] in most cases."""
  yield tree
  if node_is_leaf(tree): return
  for child in tree[1:]:
    for x in bfs_walk(child):
      yield x

def terminal_paths(tree, above_path=None):
  """
  Like terminals(), but instead of a list of terminals, there's
  one top-to-bottom path per terminal.  Loosely,
    (S (NP (N Fred) ) (VP (V runs) (A quickly)))
      ==>
    [ [S,NP,N,Fred], [S,VP,V,runs], [S,VP,A,quickly] ]
  Path elements are actually pointers to the tree nodes.  So printing a path is
  madness: the first element is actually the entire tree, and each element
  shows progressively smaller subtrees at that point.
  """
  above_path = above_path or []
  my_path = above_path + [tree]
  if node_is_leaf(tree):
    return [my_path]
  paths_for_terminals_below = []
  for child in tree[1:]:
    paths_for_terminals_below += terminal_paths(child, my_path)
  return paths_for_terminals_below

def which_is_identical(seq, x):
  """Like list.index(), but tests for object identity ("is"),
  not structural equality ("==")."""
  for i,y in enumerate(seq):
    if x is y: return i
  return -1

def console_tree(tree, min_width=3):
  """Show nesting structure for the console"""
  all_preterms = preterminals(tree)
  poses = [p[0] for p in all_preterms]
  N = len(all_preterms)

  # get spans
  spans = []
  for subtree in bfs_walk(tree):
    if node_is_leaf(subtree): continue
    if node_is_preterminal(subtree): continue
    preterms = preterminals(subtree)
    i = which_is_identical(all_preterms, preterms[0])
    n = len(preterms)
    spans.append( (i,i+n, subtree[0]) )
  #spans = [(i,j,t) for i,j,t in spans if j-i>1 and t!='ROOT'] # and (i,j) != (0,N)]
  spans = [(i,j,t) for i,j,t in spans if t!='ROOT']
  spans.sort(key=lambda (i,j,t): ((j-i),i))

  # greedy layout
  blocks = [[None]*N  for row in range(min(40,range(N)))]
  for span in spans:
    # find a row
    r = 0
    while r < len(blocks):
      cand = [blocks[r][i] for i in range(span[0],span[1])]
      if all(x is None for x in cand):
        for i in range(span[0], span[1]):
          blocks[r][i] = span
        break
      r += 1
  blocks = [row for row in blocks if any(x is not None for x in row)]

  toks = terminals(tree)
  sizes = [max(min_width,len(toks[i])+1,len(poses[i])+1) for i in range(N)]

  matrix = [[' '*sizes[i] for i in range(len(sizes))] for r in range(len(blocks))]
  for r in range(len(blocks)):
    row = blocks[r]
    i = 0
    while i < len(row):
      if row[i] is None:
        i += 1
        continue
      span = row[i]
      rng = range(span[0],span[1])
      pos = span[2]
      line = ['-']*sum(sizes[j] for j in rng)
      line[-1] = ' '
      #if len(line) >= len(pos):
      #  line[0:(0+len(pos))] = pos
      plen = min(len(pos), len(line))
      line[0:plen] = pos[:plen]
      for j in rng:
        matrix[r][j] = ''
      matrix[r][span[0]] = ''.join(line)
      i = span[1]

  # output
  for row in reversed(matrix):
    print ''.join(row)
  pos_str=  ''.join(poses[i].ljust(sizes[i]) for i in range(N))
  word_str =''.join(toks[i].ljust(sizes[i]) for i in range(N))
  import termcolor
  print termcolor.colored(pos_str, 'blue')
  print termcolor.colored(word_str, attrs=['bold'])

SimpleDep = namedtuple('SimpleDep', 'word di gi')


##########################################

def run_collapse():
  "Collapses trees from stdin to one line each"
  import sys,re
  r = re.compile(r'\s+', re.M)
  for sexpr in iter_parses(sys.stdin, raw=True):
    print r.sub(' ', sexpr)

def run_apply(fn):
  "Apply a function to parse trees on stdin; e.g. 'terminals'"
  fn = eval(fn)
  for parse in iter_parses(sys.stdin, parsed=True):
    print fn(parse)

def run_dump():
  for tree in iter_parses(sys.stdin, parsed=True):
    print "\n==="
    console_tree(tree)

if __name__=='__main__':
  import sys
  if len(sys.argv) < 2:
    print "Commands:"
    cs = [(s,f) for s,f in locals().items() if s.startswith('run_')]
    cs.sort()
    for s,f in cs:
      print '  %10s  %s' % (s.replace('run_',''), getattr(f,'__doc__','').split('\n')[0])
    sys.exit(1)
  f = eval('run_' + sys.argv[1])
  f(*sys.argv[2:])
