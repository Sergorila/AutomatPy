from collections import deque


class DFA:

    def __init__(self, isFile: bool, **kwargs):
        '''Q: set, sigma: set, delta: dict, initialState: str, F: set'''
        self.Q = set()
        self.sigma = set()
        self.delta = {}
        self.initialState = ""
        self.F = set()
        if isFile:
            with open(kwargs['path'], 'r', encoding="UTF-8-sig") as file:
                self.sigma = set(file.readline().split())
                states = file.readline().split()
                for state in states:
                    if '->' in state:
                        self.initialState = state[2::]
                        self.Q.add(state[2::])
                        continue
                    if '*' in state:
                        self.F.add(state[1::])
                        self.Q.add(state[1::])
                        continue
                    self.Q.add(state)
                for line in file:
                    state, values = line.split(':')[0], line.split(':')[1]
                    self.delta[state] = {value.split(',')[0]: value.split(',')[1] for value in values.split()}
        else:
            self.Q = kwargs['Q']
            self.sigma = kwargs['sigma']
            self.delta = kwargs['delta']
            self.initialState = kwargs['initialState']
            self.F = kwargs['F']
        self.Q = sorted(self.Q)
        self.sigma = sorted(self.sigma)
        self.F = sorted(self.F)

    def accept(self, S: str) -> bool:
        print(f"Цепочка: {S}")
        q = deque()
        q.append([0, self.initialState])
        ans = False

        while q and not ans:
            frontQ = q.popleft()
            idx = frontQ[0]
            state = frontQ[1]

            if idx == len(S):
                if state in self.F:
                    ans = True
            elif state in self.delta:
                for transition in self.delta[state].items():
                    if S[idx] == transition[0]:
                        q.append([idx + 1, transition[1]])
                        print(f"Слово:{S[idx]}, переход: {frontQ[1]} -> {transition[1]}")

        if S == "":
            ans = True

        return ans

    def getNFA(self):

        Q = self.Q.copy()
        delta = dict()
        initialState = self.initialState
        F = self.F.copy()
        sigma = self.sigma

        for state, transition in self.delta.items():
            tmp = dict()
            for s, q in transition.items():
                tmp[s] = [''.join(q)]

            delta[state] = tmp

        from nfa import NFA
        return NFA(isFile=False, Q=Q, sigma=sigma, delta=delta, initialState=initialState, F=F)

    def ShowData(self):
        sigma = "\t".join(self.sigma)
        sigma = f"\t\t{sigma}"
        print(sigma)
        for state in self.Q:
            transitions = '\t'.join([str((s, self.delta[state][s])) for s in self.delta[state]])
            if state == self.initialState:
                state = f"->{state}"
            if state in self.F:
                state = f"*{state}"
            line = f"{state}\t{transitions}"
            print(line)
