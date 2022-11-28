# Exceptions module
from authomato.errors import *
from collections import deque


class DFA:
    def __init__(self, is_file: bool, **kwargs):
        self.Q = set()
        self.sigma = set()
        self.delta = dict()
        self.initialState = ''
        self.F = set()

        if is_file:
            with open(kwargs['path'], 'r', encoding='utf-8') as file:
                self.sigma = set(file.readline().split(','))
                states = file.readline().split(',')
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
                    self.delta[state] = {value.split(' ')[0]: value.split(' ')[1] for value in values.split('; ')}
        else:
            self.Q = kwargs['Q']
            self.sigma = kwargs['sigma']
            self.delta = kwargs['delta']
            self.initialState = kwargs['initialState']
            self.F = kwargs['F']

    def accept(self, S: str) -> bool:
        ## Basic Idea: Search through states (delta) in the DFA, since the initial state to the final states

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
                # self.delta = { 'q0': { 'a': 'q1', 'b': 'q3', 'c': 'q6' }, ... }
                ## Search through states
                for transition in self.delta[state].items():
                    ## transition = ('1', 'q0')
                    if S[idx] == transition[0]:
                        q.append([idx + 1, transition[1]])
                        print(f"Символ:{S[idx]}, переход: {frontQ[1]} -> {transition[1]}")

        if S == "":
            ans = True

        return ans

    def isValid(self) -> bool:
        # Validate if the initial state is in the set Q
        if self.initialState not in self.Q:
            raise SigmaError(self.initialState, 'Is not declared in Q')

        # Validate if the delta transitions are in the set Q
        for d in self.delta:
            if d not in self.Q:
                raise SigmaError(d, 'Is not declared in Q')

            # Validate if the d transitions are valid
            for s in self.delta[d]:
                if s not in self.sigma:
                    raise SigmaError(s, 'Is not declared in sigma')
                elif self.delta[d][s] not in self.Q:
                    raise SigmaError(self.delta[d][s], 'Is not declared Q')

        # Validate if the final state are in Q
        for f in self.F:
            if f not in self.Q:
                raise SigmaError(f, 'Is not declared in Q')

        # None of the above cases failed then this DFA is valid
        return True

    def complement(self):
        Q = self.Q
        sigma = self.sigma
        delta = self.delta
        initialState = self.initialState
        F = {state for state in self.Q if state not in self.F}

        return DFA(is_file=False, Q=Q, sigma=sigma, delta=delta, initialState=initialState, F=F)

    def getNFA(self):
        from authomato.nfa import NFA
        Q = self.Q.copy()
        delta = dict()
        initialState = self.initialState
        F = self.F.copy()
        sigma = self.sigma

        for state, transition in self.delta.items():
            ## state : str, transition : dict(sigma, Q)
            tmp = dict()
            for s, q in transition.items():
                ## s : sigma
                tmp[s] = [''.join(q)]

            delta[state] = tmp

        return NFA(is_file=False, Q=Q, sigma=sigma, delta=delta, initialState=initialState, F=F)

    def product(self, M):
        """Given a DFA M returns the product automaton"""
        delta = dict()
        Q = set()
        F = set()
        sigma = self.sigma.intersection(M.sigma)

        for state, transition in self.delta.items():
            ## i : str, j : dict(sigma, Q)
            for stateM, transitionM in M.delta.items():
                ## stateM : str, transitionM : dict(sigma, Q)
                for s in transition:
                    if s in transitionM:
                        ## sigma value in common
                        sigma.add(s)

                        tmp = str([state, stateM])
                        tmp1 = str([transition[s], transitionM[s]])
                        aux = dict()
                        aux[s] = tmp1

                        Q.add(tmp)
                        Q.add(tmp1)

                        if state in self.F and stateM in M.F:
                            F.add(tmp)

                        if transition[s] in self.F and transitionM[s] in M.F:
                            F.add(tmp1)

                        if tmp in delta:
                            delta[tmp].update(aux)
                        else:
                            delta[tmp] = aux

        return DFA(is_file=False, Q=Q, sigma=sigma, delta=delta, initialState=([self.initialState, M.initialState]), F=F)

    def show_data(self):
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
