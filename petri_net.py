class PetriNet:
    def __init__(self):
        #Initializing
        #set of places P as an hashset (id)
        self.places = set()

        #set of transitions T hashmap (name, id)
        self.transitions = dict()

        #flow relation is two adjacency maps (for pre and post)
        self.pre = dict()
        self.post = dict()

        #tokens is an hashmap (place, token quantity)
        self.tokens = dict()

    def add_place(self, name):
        self.places.add(name)
        self.tokens[name] = 0

    def add_transition(self, name, id):
        self.transitions[id] = name

    def add_edge(self, source, target):

        if target not in self.pre:
            self.pre[target] = set()
        if source not in self.post:
            self.post[source] = set()

        self.pre[target].add(source)
        self.post[source].add(target)

        return self

    def get_tokens(self, place):
        return self.tokens.get(place, 0)

    def is_enabled(self, transition):
        for source in self.pre.get(transition, set()):
            if self.tokens.get(source, 0) < 1:
                return False
        return True

    def add_marking(self, place):
        if place not in self.tokens:
            self.tokens[place] = set()

        self.tokens[place] = self.tokens.get(place, 0) + 1

    def fire_transition(self, transition):
        #If the transition is enabled, remove one token from each input place and add one token to each output place
        if self.is_enabled(transition):
            for source in self.pre.get(transition, set()):
                self.tokens[source] -= 1

            for target in self.post.get(transition, set()):
                self.tokens[target] = self.tokens.get(target, 0) + 1

