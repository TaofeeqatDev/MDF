import sys

from MDF import *
from neuromllite.utils import evaluate as evaluate_params
    
def params_info(parameters):    
    pi='['
    for p in parameters:
        if not p=='__builtins__':
            pi+='%s=%s,'%(p,parameters[p])
    pi=pi[:-1]
    pi+=']'    
    return pi

class EvaluableFunction():
    
    def __init__(self, function, verbose=False):
        self.verbose = verbose
        self.function = function
        
    def evaluate(self, parameters):
        
        if self.function.function=='linear':
            expr = 'variable1*slope'
        elif self.function.function=='logistic':
            expr = '1/(1 + math.exp(-1*gain * (variable1)))'
        else:
            raise 'Unknown function: %s'%self.function.function
        
        func_params = {}
        func_params.update(parameters)
        if self.verbose: print('    ---  Evaluating %s with %s, i.e. %s'%(self.function,params_info(func_params),expr))
        for arg in self.function.args:
            func_params[arg] = evaluate_params(self.function.args[arg], func_params, verbose=False)
            if self.verbose: print('      Arg %s became %s'%(arg, func_params[arg]))
        self.curr_value = evaluate_params(expr, func_params, verbose=False)
        if self.verbose: print('    Evaluated %s with %s =\t%s'%(self.function, params_info(func_params), self.curr_value))
        return self.curr_value
        
        
class EvaluableOutput():
    
    def __init__(self, output_port, verbose=False):
        self.verbose = verbose
        self.output_port = output_port
        
    def evaluate(self, parameters):
        if self.verbose: print('    Evaluating %s with %s '%(self.output_port, params_info(parameters)))
        self.curr_value = evaluate_params(self.output_port.value, parameters, verbose=False)
        print('    Evaluated %s with %s =\t%s'%(self.output_port, params_info(parameters), self.curr_value))
        return self.curr_value
        
class EvaluableInput():
    
    def __init__(self, input_port, verbose=False):
        self.verbose = verbose
        self.input_port = input_port
        self.curr_value = 0
        
    def set_input_value(self, value):
        if self.verbose: print('    Input value in %s set to %s'%(self.input_port.id, value))
        self.curr_value = value
        
    def evaluate(self, parameters):
        print('    Evaluated %s with %s =\t%s'%(self.input_port, params_info(parameters), self.curr_value))
        return self.curr_value
        
        

class EvaluableNode():
    
    
    def __init__(self, node, verbose=False):
        self.verbose = verbose
        self.node = node
        self.evaluable_inputs = {}
        self.evaluable_functions = {}
        self.evaluable_outputs = {}
        
        for ip in node.input_ports:
            rip = EvaluableInput(ip, self.verbose)
            self.evaluable_inputs[ip.id] = rip
        for f in node.functions:
            rf = EvaluableFunction(f, self.verbose)
            self.evaluable_functions[f.id] = rf
        for op in node.output_ports:
            rop = EvaluableOutput(op, self.verbose)
            self.evaluable_outputs[op.id] = rop
        
    def initialize(self):
        pass
        
    def evaluate_next(self):
        
        print('  Evaluating Node: %s with %s'%(self.node.id, params_info(self.node.parameters)))
        curr_params = {}
        curr_params.update(self.node.parameters)
        
        for rip in self.evaluable_inputs:
        
            i = self.evaluable_inputs[rip].evaluate(curr_params)
            curr_params[rip] = i
        for rf in self.evaluable_functions:
            curr_params[rf] = self.evaluable_functions[rf].evaluate(curr_params)
        for rop in self.evaluable_outputs:
            self.evaluable_outputs[rop].evaluate(curr_params)
        
    def get_output(self, id):
        for rop in self.evaluable_outputs:
            if rop == id:
                return self.evaluable_outputs[rop].curr_value
        

class EvaluableGraph():
    
    
    def __init__(self, graph, verbose=False):
        self.verbose = verbose
        print('\nInit graph: %s'%graph.id)
        self.graph = graph
        self.enodes = {}
        self.root_nodes = []
        
        for node in graph.nodes:
            if self.verbose: print('\n  Init node: %s'%node.id)
            en = EvaluableNode(node, self.verbose)
            self.enodes[node.id] = en
            self.root_nodes.append(node.id)
            
        
        for edge in graph.edges:
            self.root_nodes.remove(edge.receiver)
    
    def evaluate(self):
        print('\nEvaluating graph: %s, root nodes: %s'%(self.graph.id, self.root_nodes))
        for rn in self.root_nodes:
            self.enodes[rn].evaluate_next()
        
        for edge in self.graph.edges:
            pre_node = self.enodes[edge.sender]
            post_node = self.enodes[edge.receiver]
            value = pre_node.evaluable_outputs[edge.sender_port].curr_value
            print('  Edge %s connects %s to %s, passing %s'%(edge.id, pre_node.node.id, post_node.node.id, value))
            post_node.evaluable_inputs[edge.receiver_port].set_input_value(value)
            post_node.evaluate_next()
        

def evaluate(graph):
    pass
    
if __name__ == "__main__":
    
    from utils import load_mdf_json, print_summary
    
    example = 'Simple.json'
    verbose = True
    if len(sys.argv)==2:
        example = sys.argv[1]
        verbose = False
        
    mod_graph = load_mdf_json(example).graphs[0]
    
    print('Loaded Graph:')
    print_summary(mod_graph)
    
    print('------------------')
    eg = EvaluableGraph(mod_graph, verbose)
    eg.evaluate()
        
    
    