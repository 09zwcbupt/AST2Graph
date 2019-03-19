from unparser import Unparser
import traceback
import keyword
import utils
import json
import sys
import pdb
import ast
import os

NON_VAR = [ 'object', 'self', 'kw', '_', 'kwargs', 'str', 'len', 'int', 'enumerate',
           'min', 'max', 'list', 'dict', 'range', 'print', 'float', 'type', 'hasattr',
           'np', 'tf', 'map', 'getattr', 'setattr', 'isinstance', 'char', 'set',
           'super', 'callable', 'sorted' ]

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
      # var name to AST node list mapping
      self.varDict = {}
      self.nonVarList = keyword.kwlist + NON_VAR
      self.varContext = {}
      self.varOccur = {}

      # process edges
      self.genParentChildEdge()
      self.genIdToNodeNameList()
      self.tokenList = Unparser( self.tree ).tokenList
      self.genNextToken()
      # generate var context
      self.findAllVars()
      print( "variable:", self.varDict.keys() )
      self.genVarContext()
   
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
               if child in self.nodeToId:
                  childId = self.nodeToId[ child ]
               else:
                  # only register new node when we haven't walk over it
                  self.nodeCount += 1
                  childId = self.nodeCount
                  self.idToNode[ self.nodeCount ] = child
                  setattr( child, 'nodeId', childId )
                  self.nodeToId[ child ] = self.nodeCount
                  self.queue.append( child )
               self.childTree[ node ].append( child )

               # generate parent -> child edge
               self.edges.append( [ parentId, childId ] )
         else:
            assert not self.childCount( node ), "node should be in childTree"
   
   # TODO: name should be consistant
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
            name += " " + str( node.s )

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

   # TODO: walk is using BFS, which is not the right way
   # to recursively walk through AST trees
   def findAllVars( self ):
      for node in ast.walk( self.tree ):
         if isinstance( node, ast.Name ):
            if node.id not in self.nonVarList:
               if (node.id[0]).isupper() or \
                  (len(node.id)>2 and node.id.startswith("__")):
                  self.nonVarList.append( node.id )
               else:
                  # id is the var name
                  if node.id in self.varDict:
                     self.varDict[ node.id ].append( node )
                     #print( node.id, len(self.varDict[ node.id ]))
                  else:
                     self.varDict[ node.id ] = [ node ]

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
            pass

   # this function depends on self.findAllVars
   def genVarContext( self ):
      for idx, node in enumerate( self.tokenList ):
          if isinstance( node.key, ast.Name ) and \
             node.key.id in self.varDict and \
             ( idx > 10 and idx < len( self.tokenList ) - 11 ):
             #print( idx, node.key.id, node.key.id in self.varDict)
             left = self.tokenList[ idx-10: idx ]
             right = self.tokenList[ idx+1: idx +11 ]
             if node.key.id in self.varContext:
                self.varContext[ node.key.id ] += [ [ node.key, left, right ] ]
             else:
                self.varContext[ node.key.id ] = [ [ node.key, left, right ] ]

   def getJsonVarOccurence( self ):
      data = {}
      for name in self.varDict:
          #print( len( self.varDict[ name ] ) )
          if len( self.varDict[ name ] ) == 1:
             # if it only occured once, ignore
             continue
          # we only consider when we are reading variable
          useCase = []
          for node in self.varDict[ name ]:
              if isinstance( node.ctx, ast.Load ):
                  useCase.append( node.nodeId )
          if len( useCase ):
             #print( name )
             data[ name ] = useCase
      return data

   def genJsonNodeLabels( self ):
      data = {}
      for name in self.nodeNames:
         data[ str( name[ 0 ] ) ] = name[ 1 ]
      return data

   def genJsonContext( self ):
      data = []
      for name in self.varContext:
          occurs = self.varContext[ name ]
          varData = {}
          varData[ "NodeId" ] = occurs[0][0].nodeId
          varData[ "Name" ] = name
          varData[ "TokenContexts" ] = []
          for occur in occurs:
             occurList = [ [], [] ]
             for token in occur[ 1 ]: # left
                occurList[ 0 ].append( [ token.text, str( type( token.key ) ) ] )
             for token in occur[ 2 ]: # right
                occurList[ 1 ].append( [ token.text, str( type( token.key ) ) ] )
             varData[ "TokenContexts" ].append( occurList )
          data.append( varData )
      return data

   def genJsonData( self ):
      data = {
         "Filename" : "dummyFile.py",
         "HoleSpan" : "",
         "HoleLineSpan" : "",
         "ContextGraph" : {
            "Edges" : {
               "Child" : self.edges,
               "NextToken" : self.nextNode,
               #"LastUse" : [],
               #"LastWrite" : [],
               #"LastLexicalUse" : []
            },
            "EdgeValues" : {
               #"LastUse" : [],
               #"LastWrite" : [],
               #"LastLexicalUse" : [],
            },
            "NodeLabels" : self.genJsonNodeLabels(),
            "NodeTypes" : {
            }
         },
         "HoleNode" : 0,
         "LastTokenBeforeHole" : 0,
         "LastUseOfVariablesInScope" : {
            "j": 35,
            "i": 36
         },
         "Productions" : {
            "1": [ 2, 4, 5 ],
            "2": [ 3 ],
            "5": [ 6 ]
         },
         "SymbolKinds" : {
            "1": "Expression",
            "2": "Expression",
            "4": "Token",
            "5": "Expression",
            "3": "Variable",
            "6": "Variable"
         },
         "SymbolLabels" : {
            "4": "+",
            "3": "i",
            "6": "j"
         },
         "HoleTokensBefore" : [],
         "HoleTokensAfter" : [],
         "VariableUsageContexts" : self.genJsonContext(),
         "VariableOccurence" : self.getJsonVarOccurence()
      }
      return data

   def writeFile( self, path ):
      with open( path, 'w' ) as jsonFile:
         data = self.genJsonData()
         json.dump( data, jsonFile )

if __name__ == "__main__":
   #path = "../data/keras-example/AST/AST-bin-dump-keras-example_keras_tests_test_multiprocessing.py.ast"
   # minimal file
   #path = "../data/keras-example/AST/AST-bin-dump-keras-example_keras_keras_preprocessing_text.py.ast"
   #path = "../data/keras-example/AST/AST-bin-dump-keras-example_keras_tests_keras_test_callbacks.py.ast"
   directory = "../data/keras-example/AST/"
   for filename in os.listdir( directory ):
      if filename.endswith(".ast"):
        print( "handling: ", directory + filename )
        edges = EdgeGenerator( directory + filename )
        edges.writeFile( './json/' + filename + '.jsonl' )
   pdb.set_trace()
