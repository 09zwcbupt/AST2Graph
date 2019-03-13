from unparser import Unparser
import utils
import pdb
import ast

class EdgeGenerator:
   def __init__( self, path="", source="" ):
      # initial example
      self.path = path
      self.source = source
      self.loadAst( path, source )
      # node object to children mapping
      self.childTree = {}
      # node object to number ID mapping
      self.nodeToId = { self.tree : 0 }
      self.idToNode = { 0 : self.tree }
      self.nodeCount = 0
      self.queue = [ self.tree ]
      self.edges = []
      self.nodeNames = []
      self.nextNode = []
      setattr( self.tree, 'nodeId', 0 )

      # process edges
      self.genParentChildEdge()
      self.genIdToNodeNameList()
      self.tokenList = Unparser( self.tree ).tokenList
      self.genNextToken()
   
   def loadAst( self, path, source ):
      if path:
         self.tree = utils.load( path )
      elif source:
         self.tree = ast.parse( source )
      else:
         assert False, "expecting source code or AST file"
      assert self.tree

   def childCount( self, node ):
      count = 0
      for _ in ast.iter_child_nodes( node ):
         count += 1
      return count

   def genParentChildEdge( self ):
      while self.queue:
         node = self.queue.pop( 0 )
         if node not in self.childTree:
            assert self.nodeCount in self.idToNode
            assert node in self.idToNode.values()
            parentId = self.nodeToId[ node ]
            self.childTree[ node ] = []
            # iterate all child nodes and add them in queue
            childGen = ast.iter_child_nodes( node )
            for child in childGen:
               # we are assuming each non-empty node is unique
               self.nodeCount += 1
               childId = self.nodeCount
               setattr( child, 'nodeId', childId )
               self.nodeToId[ child ] = self.nodeCount
               self.idToNode[ self.nodeCount ] = child
               self.childTree[ node ].append( child )
               self.queue.append( child )

               # generate parent -> child edge
               self.edges.append( [ parentId, childId ] )
         else:
            assert not self.childCount( node ), "node should be in childTree"

   def genIdToNodeNameList( self ):
      # generate id to node name list
      for node in self.nodeToId:
         index = self.nodeToId[ node ]
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
         self.nodeNames.append( [ index, name ] )
 
   def genNextToken( self ):
      cur = -1
      prev = -1
      for token in self.tokenList:
          prev = cur
          cur = token.key.nodeId
          if cur != -1 and prev != -1:
             self.nextNode.append( [ prev, cur ] )
         

if __name__ == "__main__":
   path = "../data/keras-example/AST/AST-bin-dump-keras-example_keras_tests_test_multiprocessing.py.ast"
   edges = EdgeGenerator( path )

   import pdb
   #import astunparse
   #source = astunparse.unparse(tree)
      
   pdb.set_trace()
   #tokens = Unparser( edges.tree )
   #pdb.set_trace()
