# Exceptions module
from authomato.errors import *
from collections import deque
from authomato.dfa import DFA


class NFA:
    def __init__(self, is_file: bool, **kwargs):
        self.Q = set()
        self.sigma = set()
        self.delta = dict()
        self.initialState = ''
        self.F = set()

        if is_file:
            with open(kwargs['path'], 'r', encoding='utf-8') as file:
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
                    state, values = line.split(' -')[0], line.split(' -')[1]
                    self.delta[state] = dict()
                    for value in values.split():
                        cur = value.split(',')
                        if cur[0] in self.delta[state]:
                            self.delta[state][cur[0]].append(cur[1])
                        else:
                            self.delta[state][cur[0]] = [cur[1]]
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
        ## Basic Idea: Search through states (delta) in the NFA, since the initial state to the final states

        ## BFS states

        q = deque()  ## queue -> states from i to last character in S | (index, state)
        q.append([0, self.initialState])  ## Starts from 0
        ans = False  ## Flag

        while q and not ans:
            frontQ = q.popleft()
            idx = frontQ[0]
            state = frontQ[1]

            if idx == len(S):
                if state in self.F:
                    ans = True
            elif S[idx] not in self.sigma:
                raise InputError(S[idx], 'Is not declared in sigma')
            elif state in self.delta:
                ## Search through states
                for transition in self.delta[state].items():
                    d = transition[0]
                    states = transition[1]

                    if d == "_":
                        ## Is epsilon
                        for state in states:
                            # Do not consume character
                            q.append([idx, state])
                            print(f"Слово:_, индекс символа: {idx}, переход: {frontQ[1]} -> {state}")
                    elif S[idx] == d:
                        for state in states:
                            # Consume character
                            q.append([idx + 1, state])
                            print(f"Слово:{S[idx]}, индекс символа: {idx}, переход: {frontQ[1]} -> {state}")

        if S == "":
            ans = True

        return ans

    def isValid(self) -> bool:
        # Validate if the initial state is in the set Q
        if self.initialState not in self.Q:
            raise SigmaError(self.initialState, 'Is not declared in Q')

        # Validate if the delta transitions are in the set Q
        for d in self.delta:
            if d != "" and d not in self.Q:
                raise SigmaError(d, 'Is not declared in Q')

            # Validate if the d transitions are valid
            for s in self.delta[d]:
                if s != "" and s not in self.sigma:
                    raise SigmaError(s, 'Is not declared in sigma')
                for q in self.delta[d][s]:
                    if q not in self.Q:
                        raise SigmaError(self.delta[d][s], 'Is not declared Q')

        # Validate if the final state are in Q
        for f in self.F:
            if f not in self.Q:
                raise SigmaError(f, 'Is not declared in Q')

        # None of the above cases failed then this NFA is valid
        return True

    def complement(self):
        Q = self.Q
        sigma = self.sigma
        delta = self.delta
        initialState = self.initialState
        F = {state for state in self.Q if state not in self.F}

        return NFA(is_file=False, Q=Q, sigma=sigma, delta=delta, initialState=initialState, F=F)

    def getEClosure(self, q, visited=None):
        ans = [q]
        if visited is None:
            visited = [q]

        if q in self.delta:
            if '_' in self.delta[q]:
                for st in self.delta[q]['_']:
                    if st not in visited:
                        visited.append(st)
                        ans.extend([k for k in self.getEClosure(st, visited) if k not in ans])
        return ans

    def containsEpsilonTransitions(self):
        for q in self.delta:
            if '_' in self.delta[q]:
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

                    ##Get the transitions from sigma in each epsilon closure
                    for closureState in closureStates:
                        if closureState in self.F:
                            deltaF.append(q)
                        if closureState in self.delta and sigma in self.delta[closureState]:
                            toEpsiClosure.extend(self.delta[closureState][sigma])

                    ##Get the new transitions from the epsilon closure
                    for epsiClosure in toEpsiClosure:
                        newTransitions.extend(self.getEClosure(epsiClosure))

                    if q not in deltaPrime:
                        deltaPrime[q] = dict()

                    if sigma != '_':
                        deltaPrime[q][sigma] = list(set(newTransitions))

        return NFA(is_file=False, Q=Qprime, sigma=self.sigma, delta=deltaPrime, initialState=deltaInitState, F=deltaF)

    def getDFA(self):
        localNFA = NFA(is_file=False, Q=self.Q, sigma=self.sigma, delta=self.delta, initialState=self.initialState, F=self.F)
        localNFA = localNFA.removeEpsilonTransitions()

        Qprime = []
        deltaPrime = dict()

        queue = deque()
        visited = [[localNFA.initialState]]
        queue.append([localNFA.initialState])

        while queue:
            qs = queue.pop()  ## state Q

            T = dict()  ## {str : list}

            for q in qs:
                if q in localNFA.delta:
                    for s in localNFA.delta[q]:
                        tmp = localNFA.delta[q][s].copy()
                        if tmp:
                            if s in T:
                                ## avoid add repeated values
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

        return DFA(is_file=False, Q=Qprime, sigma=localNFA.sigma, delta=deltaPrime, initialState=str([localNFA.initialState]), F=Fprime)

    def minimize(self):
        localDFA = self.getDFA()
        localNFA = localDFA.getNFA()
        localNFA.renumber()
        return localNFA

    def renumber(self):
        idx = 0
        newTags = dict()

        # New values
        initialState = None
        Q = set()
        delta = dict()
        F = set()

        # Setting the new label for each state
        tmpQ = list(self.Q)
        tmpQ.sort()

        for q in tmpQ:
            newTags[q] = str(idx)
            Q.add(str(idx))
            idx += 1

        initialState = newTags[self.initialState]

        # Changing the labels for the final states
        for f in self.F:
            F.add(newTags[f])

        for q in self.delta:
            delta[newTags[q]] = dict()
            for s in self.delta[q]:
                nxtStates = list()
                for nxtState in self.delta[q][s]:
                    nxtStates.append(newTags[nxtState])

                delta[newTags[q]][s] = set(nxtStates)

        self.Q, self.F, self.delta, self.initialState = Q, F, delta, initialState

    def union(self, M):
        sigma = self.sigma.union(M.sigma)
        Q = set()
        F = set()
        initialState = "q0"
        Q.add(initialState)
        realValueSelf = dict()
        realValueM = dict()
        selfDelta = dict()
        mDelta = dict()
        ## Fix possible errors when using the dictionaries with the name of the states
        for i, q in enumerate(self.Q, 1):
            realValueSelf[q] = "q{}".format(i)
            Q.add(realValueSelf[q])

        for i, s in enumerate(M.Q):
            realValueM[s] = "s{}".format(i)
            Q.add(realValueM[s])

        for q in self.F:
            F.add(realValueSelf[q])

        for q in M.F:
            F.add(realValueM[q])

        # Replace the values
        for q, transition in self.delta.items():
            ## q : string, transition : {string -> list(string)}
            tmpDict = dict()
            for s, states in transition.items():
                tmpStates = []
                for state in states:
                    tmpStates.append(realValueSelf[state])

                tmpDict[s] = set(tmpStates.copy())
            selfDelta[realValueSelf[q]] = tmpDict.copy()

        for q, transition in M.delta.items():
            ## q : string, transition : {string -> list(string)}
            tmpDict = dict()
            for s, states in transition.items():
                tmpStates = []
                for state in states:
                    tmpStates.append(realValueM[state])

                tmpDict[s] = set(tmpStates.copy())
            mDelta[realValueM[q]] = tmpDict.copy()

        delta = {**selfDelta, **mDelta, initialState: {
            '': {realValueSelf[self.initialState], realValueM[M.initialState]}}}

        return NFA(Q, sigma, delta, initialState, F)

    def product(self, M):
        ##Using DFA conversion
        a = self.getDFA()
        b = M.getDFA()

        nfa = a.product(b).getNFA()

        return nfa

    def show_data(self):
        sigma = "\t".join(self.sigma)
        sigma = f"\t\t{sigma}"
        print(sigma)
        alphabet = sorted(set(self.sigma.copy()))
        alphabet.append('_')
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