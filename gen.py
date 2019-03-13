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
      setattr( self.tree, 'nodeId', 0 )
      # node object to children mapping
      self.childTree = {}
      # node object to number ID mapping
      self.nodeToId = { self.tree : 0 }
      self.idToNode = { 0 : self.tree }
      self.nodeCount = 0
      self.queue = [ self.tree ]
      self.nodeNames = []
      self.nextNode = []

      # parent<->child edges
      self.edges = []

      # var apperaed in code
      self.varDict = {}
      self.nonVarList = [ 'self', 'kw' ]

      # process edges
      self.genParentChildEdge()
      self.genIdToNodeNameList()
      self.tokenList = Unparser( self.tree ).tokenList
      self.genNextToken()
      self.findAllVars()
   
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

   def findAllVars( self ):
      tmp = {}
      for node in ast.walk( self.tree ):
         if isinstance( node, ast.Name ):
            if ( node.id not in self.varDict ) and \
               ( node.id not in self.nonVarList ):
               if (node.id[0]).isupper() or \
                  (len(node.id)>2 and node.id.startswith("__")):
                  self.nonVarList.append( node.id )
               else:
                  self.varDict[ node.id ] = getattr( self.varDict, node.id, [] ).append( node )

         elif isinstance( node, ast.Import ):
            for alias in node.names:
               self.nonVarList.append( alias.name )

         elif isinstance( node, ast.ImportFrom ):
            for alias in node.names:
               self.nonVarList.append( alias.name )

         # class name is not var
         # Instantiate a class could be treated as creating a new var
         elif isinstance( node, ast.ClassDef ):
            self.nonVarList.append( node.name )

         elif isinstance( node, ast.FunctionDef ):
            self.nonVarList.append( node.name )

         else:
            if type( node ) not in tmp:
               tmp[type(node)] = True
      print( tmp.keys() )

if __name__ == "__main__":
   path = "../data/keras-example/AST/AST-bin-dump-keras-example_keras_tests_test_multiprocessing.py.ast"
   edges = EdgeGenerator( path )
   pdb.set_trace()
