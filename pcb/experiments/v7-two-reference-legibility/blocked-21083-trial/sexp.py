"""New read-only S-expression utility for the recovered source; no historical-byte claim."""
import re
TOKEN=re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()]+))')
def parse(text):
 stack=[];roots=[];pos=0;text=text.rstrip()
 while pos<len(text):
  m=TOKEN.match(text,pos)
  if m is None:raise ValueError('Bad S-expression')
  pos=m.end()
  if m.group(1):
   node=[];(stack[-1]if stack else roots).append(node);stack.append(node)
  elif m.group(2):
   if not stack:raise ValueError('Extra close')
   stack.pop()
  else:
   atom=m.group(4)
   if atom is None:atom=re.sub(r'\\(["\\])',r'\1',m.group(3))
   (stack[-1]if stack else roots).append(atom)
 if stack or len(roots)!=1:raise ValueError('Unbalanced structure')
 return roots[0]
def all(node,name):return [x for x in node if isinstance(x,list)and x and x[0]==name]
def get(node,name):return next(iter(all(node,name)),None)
def fields(tree):return {f[2]:f for fp in all(tree,'footprint')for f in all(fp,'property')if f[1]=='Reference'}
