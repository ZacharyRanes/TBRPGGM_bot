#Author: Sergey Ivanov

from lxml import etree
import json
import re

#to use for parsing stuff
subst_vars = [r'(\w+)::(\w+)',r'self.states["\1"]["\2"]']
misc_substs = [r'true',r'True']

class adventureGame:
    def __init__(self):
        self.title   = None
        self.states  = {}    #save game-related states
        self.data    = None  #the description of the game
        self.pos     = None  #ptr to current place in game
        self.choices = []    #current valid choices and their mappings to original choices
        self.text    = ''    #current text after processing

    def start(self):
        self.title = self.data['title']
        self.pos = self.data['start_state']
        start_node = self.data['states'][self.pos]
        self.pruneChoices(start_node)
        self.processText(start_node)
        self.states = self.data['gamevars']

    def choose(self, c):
        #translate choice c to og choices
        c = self.choices[c][0]
        c = self.data['states'][self.pos]['options'][c]
        #TODO: Implement random transition check&choice here

        #input choice c and progress game
        pos = c[-2] #nextNode(string)
        nextNode = self.data['states'][pos]        #nextNode(var)
        #get parts of the node

        #==== main transition steps ====
        self.execStmt(c[1])          # execute transition function
        self.pruneChoices(nextNode)  # prune the choices the user can pick
        self.processText(nextNode)   # process text based on env states
        self.pos = pos               # finally, set our position string

    def state(self):
        #show current state, return current state text
        return self.text

    def getChoices(self):
        return [c[-1] for c in self.choices]

    def pruneChoices(self, node):
        ch = node['options']
        self.choices = []
        for i in range(0,len(ch)):
            c = ch[i]
            if (c[0] == '' or self.evalStmt(c[0])):  #is choice valid?
                flavorText = c[-1]
                self.choices.append([i,flavorText])

    def processText(self,node):
        #parse string to display
        #n = self.data['states'][node] #im now passing this directly
        text = '<base>' + node['text'] + '</base>'
        root = etree.fromstring(text)
        self.text = self.parseXML(root)

    def parseXML(self, root):
        strng = ''
        strng += root.text
        for i in root.getchildren():  #this is where we define the tag types, could use dict for switch/case logic here
            if (i.tag == 'cond' and self.evalStmt(i.attrib['expr'])):
                strng += self.parseXML(i)
            strng += i.tail
        return strng

    def isEnd(self):
        if (len(self.data['states'][self.pos]['options']) == 0):
            return True
        else:
            return False

    def isWin(self):
        return self.pos in self.data['win_states']

    def execStmt(self, expr):
        try:
            exec(self.substPythonString(expr))
        except:
            return False

    def evalStmt(self, expr):
        try:
            return eval(self.substPythonString(expr))
        except:
            return 0

    def substPythonString(self, expr):
        expr = re.sub(subst_vars[0], subst_vars[1], expr)
        expr = re.sub(misc_substs[0], misc_substs[1], expr)
        return expr

    def adventureTitle(self):
        return self.title


#turn string s into AGF 
def parseAGF(s):
    ag = adventureGame()
    ag.data = json.loads(s)
    ag.start()
    return ag

#load a .agf file
def loadAGF(f):
    with open(f) as fd:
        ag = parseAGF(fd.read())
    return ag

#Saves string to file
def saveAGF(ag, fn):
    with open(fn,'w') as fd:
        fd.write(serialize(ag))

#turn adventureGame object into string
def serialize(ag):
   return json.dumps(ag.data)