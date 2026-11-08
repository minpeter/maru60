import re

def children(s):
    """Return top-level child (start,end,text) spans without reformatting bytes."""
    depth=0; quoted=False; escaped=False; start=None; rows=[]
    for i,c in enumerate(s):
        if quoted:
            if escaped: escaped=False
            elif c=='\\': escaped=True
            elif c=='"': quoted=False
            continue
        if c=='"': quoted=True;continue
        if c=='(':
            depth+=1
            if depth==2:start=i
        elif c==')':
            if depth==2:rows.append((start,i+1,s[start:i+1]))
            depth-=1
    assert depth==0 and not quoted
    return rows

def head(s):return re.match(r'\(\s*([^\s()]+)',s).group(1)
def field(s,name):
    return next((t for _,_,t in children(s)if head(t)==name),None)
def replace_span(s,a,z,t):return s[:a]+t+s[z:]
def replace_child(s,name,new):
    a,z,t=next((a,z,t)for a,z,t in children(s)if head(t)==name)
    return replace_span(s,a,z,new)
