"""Minimal MSFS RPN interpreter for the subset used by the profile."""
import re
TOK = re.compile(r'\([^)]*\)|\S+')

def tokenize(code): return TOK.findall(code)

def run(code, lvars, max_steps=2000):
    t = tokenize(code); stack=[]; reg={}; out=[]; labels={}
    for i,x in enumerate(t):
        if re.fullmatch(r':\d+', x): labels[x[1:]] = i
    i=0; steps=0
    def skip_block(i):  # i points after '{'-token; return index after matching '}'
        depth=1
        while depth:
            x=t[i]
            if x.endswith('{'): depth+=1
            elif x=='}': depth-=1
            i+=1
        return i
    while i < len(t):
        steps+=1
        if steps>max_steps: raise RuntimeError("loop")
        x=t[i]; i+=1
        if re.fullmatch(r'-?\d+(\.\d+)?', x): stack.append(float(x)); continue
        if x.startswith('(>'):
            name=x[2:-1].split(',')[0]; v=stack.pop()
            if name.startswith('K:'): out.append((name[2:], int(v)))
            else: lvars[name]=v
            continue
        if x.startswith('('):
            name=x[1:-1].split(',')[0].strip(); stack.append(float(lvars.get(name,0))); continue
        if x in ('+','-','*','/','div','==','<','>','<=','>=','!=','and','or'):
            b=stack.pop(); a=stack.pop()
            ops={'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b,'div':lambda:a/b,'==':lambda:a==b,'<':lambda:a<b,'>':lambda:a>b,'<=':lambda:a<=b,'>=':lambda:a>=b,'!=':lambda:a!=b,'and':lambda:bool(a) and bool(b),'or':lambda:bool(a) or bool(b)}
            r=ops[x]()
            stack.append(float(r)); continue
        if x=='near': stack.append(float(round(stack.pop()))); continue
        if x=='++': stack.append(stack.pop()+1); continue
        if x=='--': stack.append(stack.pop()-1); continue
        if re.fullmatch(r's\d', x): reg[x[1]]=stack[-1]; continue
        if re.fullmatch(r'l\d', x): stack.append(reg[x[1]]); continue
        if re.fullmatch(r':\d+', x): continue
        if re.fullmatch(r'g\d+', x): i=labels[x[1:]]+1; continue
        if x=='if{':
            c=stack.pop()
            if c: continue
            i=skip_block(i)
            if i<len(t) and t[i]=='els{': i+=1
            continue
        if x=='}':
            if i<len(t) and t[i]=='els{': i=skip_block(i+1)
            continue
        if x=='els{': i=skip_block(i); continue
        raise ValueError("unknown token "+x)
    return out, stack
