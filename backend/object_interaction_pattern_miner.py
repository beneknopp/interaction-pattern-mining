from PATTERNS import EAVAL, EAVAL_GEQ, E2O_R, O2O_R, O2O_R_COMPLETE


class ObjectInteractionPatternMiner():

    def __init__(self, ocel):
        self.ocel = ocel
        #p = EAVAL_GEQ(ocel, "price", 500.0)
        #p = E2O_R(ocel, "order")
        #p = O2O_R(ocel, "comprises")
        p = O2O_R_COMPLETE(ocel, "comprises")
        events = list(ocel.events["ocel:eid"].values)
        p.apply(events[0], ["o-990001"])

    def load_default_patterns(self):
        o2o_relations = self.ocel.relations

    def entropy_based_pattern_detection(self):
        detected_patterns = []
        detected_patterns.append(EAVAL_GEQ(self.ocel, "price", 500.0))
        self.detected_patterns = detected_patterns

    def load_detected(self):
        self.patterns = list(set(self.patterns + self.detected_patterns))

    def mine(self):
        pass