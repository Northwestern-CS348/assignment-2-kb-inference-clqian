import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[]):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

    def _get_fact(self, fact):
        """INTERNAL USE ONLY
        Get the fact in the KB that is the same as the fact argument

        Args:
            fact (Fact): Fact we're searching for

        Returns:
            Fact: matching fact
        """
        for kbfact in self.facts:
            if fact == kbfact:
                return kbfact

    def _get_rule(self, rule):
        """INTERNAL USE ONLY
        Get the rule in the KB that is the same as the rule argument

        Args:
            rule (Rule): Rule we're searching for

        Returns:
            Rule: matching rule
        """
        for kbrule in self.rules:
            if rule == kbrule:
                return kbrule

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB
        Args:
            fact_rule (Fact|Rule) - the fact or rule to be added
        Returns:
            None
        """
        printv("Adding {!r}", 1, verbose, [fact_rule])
        if isinstance(fact_rule, Fact):
            if fact_rule not in self.facts:
                self.facts.append(fact_rule)
                for rule in self.rules:
                    self.ie.fc_infer(fact_rule, rule, self)
            else:
                if fact_rule.supported_by:
                    #adding fact rule again but might have more things to support it
                    ind = self.facts.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.facts[ind].supported_by.append(f)
                else:
                    #adding fact_rule again but this time, it it not supported by anything, so it is asserted
                    ind = self.facts.index(fact_rule)
                    self.facts[ind].asserted = True
        elif isinstance(fact_rule, Rule):
            if fact_rule not in self.rules:
                self.rules.append(fact_rule)
                for fact in self.facts:
                    self.ie.fc_infer(fact, fact_rule, self)
            else:
                if fact_rule.supported_by:
                    ind = self.rules.index(fact_rule)
                    for f in fact_rule.supported_by:
                        self.rules[ind].supported_by.append(f)
                else:
                    ind = self.rules.index(fact_rule)
                    self.rules[ind].asserted = True

    def kb_assert(self, fact_rule):
        """Assert a fact or rule into the KB

        Args:
            fact_rule (Fact or Rule): Fact or Rule we're asserting
        """
        printv("Asserting {!r}", 0, verbose, [fact_rule])
        self.kb_add(fact_rule)

    def kb_ask(self, fact):
        """Ask if a fact is in the KB

        Args:
            fact (Fact) - Statement to be asked (will be converted into a Fact)

        Returns:
            listof Bindings|False - list of Bindings if result found, False otherwise
        """
        print("Asking {!r}".format(fact))
        if factq(fact):
            f = Fact(fact.statement)
            bindings_lst = ListOfBindings()
            # ask matched facts
            for fact in self.facts:
                binding = match(f.statement, fact.statement)
                if binding:
                    bindings_lst.add_bindings(binding, [fact])

            return bindings_lst if bindings_lst.list_of_bindings else []

        else:
            print("Invalid ask:", fact.statement)
            return []

    def _kb_remove_facts(self, fact_or_rule):
        for f in fact_or_rule.supports_facts:
            f_idx = self.facts.index(f)
            kb_f = self.facts[f_idx]
            for pair in kb_f.supported_by:
                if fact_or_rule in pair:
                    kb_f.supported_by.remove(pair)
            if not kb_f.supported_by and not kb_f.asserted:
                self.kb_retract(kb_f)

    def _kb_remove_rules(self, fact_or_rule):
        for r in fact_or_rule.supports_rules:
            r_idx = self.rules.index(r)
            kb_r = self.rules[r_idx]
            for pair in kb_r.supported_by:
                if fact_or_rule in pair:
                    kb_r.supported_by.remove(pair)
            if not kb_r.supported_by and not kb_r.asserted:
                self.kb_retract(kb_r)

    def kb_retract(self, fact_or_rule):
        """Retract a fact from the KB

        Args:
            fact (Fact) - Fact to be retracted

        Returns:
            None
        """
        printv("Retracting {!r}", 0, verbose, [fact_or_rule])
        ####################################################
        if isinstance(fact_or_rule, Rule) and fact_or_rule in self.rules:
            rule_idx = self.rules.index(fact_or_rule)
            kb_rule = self.rules[rule_idx]
            if kb_rule.asserted or kb_rule.supported_by:
                return
            self._kb_remove_facts(kb_rule)
            self._kb_remove_rules(kb_rule)
            self.rules.pop(rule_idx)
        elif isinstance(fact_or_rule, Fact) and fact_or_rule in self.facts:
            fact_idx = self.facts.index(fact_or_rule)
            kb_fact = self.facts[fact_idx]
            if kb_fact.supported_by:
                kb_fact.asserted = False
                return
            self._kb_remove_facts(kb_fact)
            self._kb_remove_rules(kb_fact)
            self.facts.pop(fact_idx)

        

class InferenceEngine(object):
    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing            
        """
        printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            [fact.statement, rule.lhs, rule.rhs])
        ####################################################
        # Student code goes here
        b = match(rule.lhs[0], fact.statement)
        if b:
            s_by = [(fact, rule)]
            st = instantiate(rule.lhs[0], b)
            new_rhs = instantiate(rule.rhs, b)
            if len(rule.lhs) == 1 and st == fact.statement: #create new fact with rule.rhs
                new_f = Fact(new_rhs, s_by)
                kb.kb_assert(new_f)
                fact.supports_facts.append(new_f)
                rule.supports_facts.append(new_f)
            else:
                new_lhs = []
                if st != fact.statement: #create new rule with new rule.lhs[0]
                    new_lhs.append(st)
                for old_lhs in rule.lhs[1:]:
                    new_lhs.append(instantiate(old_lhs, b))
                new_rule = Rule([new_lhs, new_rhs], s_by)
                kb.kb_assert(new_rule)
                fact.supports_rules.append(new_rule)
                rule.supports_rules.append(new_rule)




