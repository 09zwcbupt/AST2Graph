from six.moves import cStringIO
from unparser import Unparser
from gen import EdgeGenerator
import pdb
import ast

testProgs = []
testProgs.append( """
import os
os.system('echo "hello"')
""" )
testProgs.append( """
for i in range(10):
    print(i + 'test prog')
    if i == 5:
        continue
""" )
testProgs.append( """
class Test:
    def __init__(self, testArg):
        self.testArg = testArg
testObj = Test(1)
""" )

def unparsingTest( prog ):
    gen = EdgeGenerator( source=prog )
    v = cStringIO()
    unparser = Unparser( gen.tree, file=v )
    text = ""
    for item in unparser.tokenList:
        if item.startOfLine:
            text += "\n" + " " * item.identLevel
        text += item.text
    # matching the last new line char from input
    text += "\n"
    #pdb.set_trace()
    assert prog == text
    #print(text)

if __name__ == "__main__":
   for prog in testProgs:
      unparsingTest( prog )
