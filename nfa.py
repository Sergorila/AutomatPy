from collections import deque


class NFA:

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
                    self.delta[state] = dict()
                    for value in values.split():
                        cur = value.split(',')
                        if cur[0] in self.delta[state]:
                            self.delta[state][cur[0]].append(cur[1])
                        else:
                            self.delta[state][cur[0]] = [cur[1]]
                    #self.delta[state] = {value.split(',')[0]: value.split(',')[1] for value in values.split()}
        else:
            self.Q = kwargs['Q']
            self.sigma = kwargs['sigma']
            self.delta = kwargs['delta']
            self.initialState = kwargs['initialState']
            self.F = kwargs['F']
        self.Q = set(sorted(self.Q))
        self.sigma = set(sorted(self.sigma))
        self.F = set(sorted(self.F))

    def accept(self, S: str) -> bool:

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
                    d = transition[0]
                    states = transition[1]

                    if d == "_":
                        for state in states:
                            q.append([idx, state])
                            print(f"Слово:{S[idx]}, переход: {frontQ[1]} -> {state}")
                    elif S[idx] == d:
                        for state in states:
                            q.append([idx + 1, state])
                            print(f"Слово:{S[idx]}, переход: {frontQ[1]} -> {state}")

        if S == "":
            ans = True

        return ans

    def getEClosure(self, q, visited=None):
        ans = [q]
        if visited is None:
            visited = list(q)

        if q in self.delta:
            if '_' in self.delta[q]:
                for st in self.delta[q]['_']:
                    if st not in visited:
                        visited.append(st)
                        ans.extend([k for k in self.getEClosure(st, visited) if k not in ans])
        return ans

    def containsEpsilonTransitions(self):
        for q in self.delta:
            if '' in self.delta[q]:
                return True
        return False

    def removeEpsilonTransitions(self):
        Qprime = self.Q.copy()
        deltaPrime = self.delta.copy()
        deltaInitState = self.initialState
        deltaF = self.F.copy()

        if self.containsEpsilonTransitions():
            deltaPrime = dict()
            for q in Qprime:
                closureStates = self.getEClosure(q)

                for sigma in self.sigma:
                    toEpsiClosure = list()
                    newTransitions = list()

                    for closureState in closureStates:
                        if closureState in self.F:
                            deltaF.add(q)
                        if closureState in self.delta and sigma in self.delta[closureState]:
                            toEpsiClosure.extend(self.delta[closureState][sigma])

                    for epsiClosure in toEpsiClosure:
                        newTransitions.extend(self.getEClosure(epsiClosure))

                    if q not in deltaPrime:
                        deltaPrime[q] = dict()

                    if sigma != '_':
                        deltaPrime[q][sigma] = set(newTransitions)

        return NFA(isFile=False, Q=Qprime, sigma=self.sigma, delta=deltaPrime, initialState=deltaInitState, F=deltaF)

    def getDFA(self):

        localNFA = NFA(isFile=False, Q=self.Q, sigma=self.sigma, delta=self.delta,
                       initialState=self.initialState, F=self.F)
        localNFA = localNFA.removeEpsilonTransitions()

        Qprime = []
        deltaPrime = dict()

        queue = deque()
        visited = [[localNFA.initialState]]
        queue.append([localNFA.initialState])

        while queue:
            qs = queue.pop()

            T = {}

            for q in qs:
                if q in localNFA.delta:
                    for s in localNFA.delta[q]:
                        tmp = localNFA.delta[q][s].copy()
                        if tmp:
                            if s in T:
                                T[s].extend([k for k in tmp if k not in T[s]])
                            else:
                                T[s] = list(tmp)

            for t in T:
                T[t].sort()
                tmp = T[t].copy()
                if tmp not in visited:
                    queue.append(tmp)
                    visited.append(tmp)
                T[t] = str(T[t])

            deltaPrime[str(qs)] = T
            Qprime.append(qs)

        Fprime = set()

        for qs in Qprime:
            for q in qs:
                if q in localNFA.F:
                    Fprime.add(str(qs))
                    break

        aux = set()

        for qs in Qprime:
            aux.add(str(qs))

        Qprime = aux

        from dfa import DFA
        return DFA(isFile=False, Q=Qprime, sigma=localNFA.sigma, delta=deltaPrime,
                   initialState=str([localNFA.initialState]), F=Fprime)

    def ShowData(self):
        sigma = "\t".join(self.sigma)
        sigma = f"\t\t{sigma}"
        print(sigma)
        alphabet = self.sigma.copy()
        alphabet.add('_')
        for state in self.Q:
            transitions = ''
            for s in alphabet:
                cur = []
                if s in self.delta[state]:
                    cur = self.delta[state][s]
                transitions = f"{transitions}{'| ' if s == '_' else ''}{cur}\t"
            if state == self.initialState:
                state = f"->{state}"
            if state in self.F:
                state = f"*{state}"
            line = f"{state}\t{transitions}"
            print(line)
