from dfa import DFA
from nfa import NFA

d = DFA(isFile=True, path='TextFile1.txt')
#print(d.accept('aaabc'))
d.ShowData()

n = NFA(isFile=True, path='TextFile2.txt')
#print(n.accept("bbaa"))
n.ShowData()

d1 = n.getDFA()
d1.ShowData()

n1 = d.getNFA()
n1.ShowData()
