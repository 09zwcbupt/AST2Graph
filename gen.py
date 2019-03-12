from unparser import Unparser
import utils
import ast

def childCount( node ):
   count = 0
   for _ in ast.iter_child_nodes( node ):
      count += 1
   return count

# initial example
tree = utils.load('../data/keras-example/AST/AST-bin-dump-keras-example_keras_tests_test_multiprocessing.py.ast')
# node object to children mapping
childTree = {}
# node object to number ID mapping
nodeToId = { tree : 0 }
idToNode = { 0 : tree }
nodeCount = 0
queue = [ tree ]

edges = []

while queue:
   node = queue.pop( 0 )
   if node not in childTree:
      assert nodeCount in idToNode
      assert node in idToNode.values()
      parentId = nodeToId[ node ]
      childTree[ node ] = []
      # iterate all child nodes and add them in queue
      childGen = ast.iter_child_nodes( node )
      for child in childGen:
         # we are assuming each non-empty node is unique
         nodeCount += 1
         childId = nodeCount
         nodeToId[ child ] = nodeCount
         idToNode[ nodeCount ] = child
         childTree[ node ].append( child )
         queue.append( child )

         # generate parent -> child edge
         edges.append( [ parentId, childId ] )
   else:
      assert not childCount( node ), "node should be in childTree"

# generate id to node name list
nodeNames = []
for node in nodeToId:
   index = nodeToId[ node ]
   name = str( type( node ) )

   # Variables
   if isinstance( node, ast.Name ):
      name += " " + node.id
   elif isinstance( node, ast.Num ):
      name += " " + str( node.n )
   elif isinstance( node, ast.Str ) or \
        isinstance( node, ast.Bytes ):
      name += " " + node.s

   # Expressions
   elif isinstance( node, ast.UAdd ) or \
        isinstance( node, ast.Add ):
      name += " +"
   elif isinstance( node, ast.USub ) or \
        isinstance( node, ast.Sub ):
      name += " -"
   elif isinstance( node, ast.Mult ):
      name += " *"
   elif isinstance( node, ast.Div ):
      name += " /"
   elif isinstance( node, ast.FloorDiv ):
      name += " FloorDiv"
   elif isinstance( node, ast.Not ):
      name += " !"
   elif isinstance( node, ast.Invert ):
      name += " ~"
   nodeNames.append( [ index, name ] )
import pdb
import astunparse
source = astunparse.unparse(tree)
pdb.set_trace()

from six.moves import cStringIO
v = cStringIO()
Unparser( tree, file=v )
