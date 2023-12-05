from glob import glob
from pathlib import Path
from typing import List, Set, Tuple, Type

import pytest

from aaa import aaa_project_root
from aaa.parser.lib.exceptions import ParseError
from aaa.parser.models import (
    AaaParseModel,
    Argument,
    Arguments,
    Assignment,
    Boolean,
    Branch,
    CaseBlock,
    CaseLabel,
    CommaSeparatedTypeList,
    DefaultBlock,
    Enum,
    EnumDeclaration,
    EnumVariant,
    EnumVariantAssociatedData,
    EnumVariants,
    FlatTypeLiteral,
    FlatTypeParams,
    ForeachLoop,
    Function,
    FunctionBody,
    FunctionBodyBlock,
    FunctionBodyItem,
    FunctionCall,
    FunctionDeclaration,
    FunctionName,
    FunctionPointerTypeLiteral,
    GetFunctionPointer,
    Import,
    ImportItem,
    ImportItems,
    MatchBlock,
    ReturnTypes,
    SourceFile,
    Struct,
    StructDeclaration,
    StructField,
    StructFieldQuery,
    StructFields,
    StructFieldUpdate,
    TypeLiteral,
    TypeOrFunctionPointerLiteral,
    TypeParams,
    UseBlock,
    Variables,
    WhileLoop,
)
from aaa.parser.parser import NODE_TYPE_TO_MODEL, AaaParser, unescape_string

MODEL_TO_NODE_TYPE = {
    model_type: node_type for (node_type, model_type) in NODE_TYPE_TO_MODEL.items()
}


PARSE_MODEL_TEST_VALUES: List[Tuple[Type[AaaParseModel], str, bool]] = [
    (Argument, "", False),
    (Argument, "3", False),
    (Argument, "foo as bar", True),
    (Argument, "foo as bar[", False),
    (Argument, "foo as bar[]", False),
    (Argument, "foo as bar[A,]", True),
    (Argument, "foo as bar[A,B,]", True),
    (Argument, "foo as bar[A,B]", True),
    (Argument, "foo as bar[A", False),
    (Argument, "foo as bar[A]", True),
    (Argument, "foo as", False),
    (Argument, "foo", False),
    (Arguments, "", False),
    (Arguments, "3", False),
    (Arguments, "args foo as bar", True),
    (Arguments, "args foo as bar[A,B],", True),
    (Arguments, "args foo as bar[A,B],foo as bar[A,B],", True),
    (Arguments, "args foo as bar[A,B],foo as bar[A,B]", True),
    (Arguments, "args foo as bar[A,B]", True),
    (Arguments, "args foo as bar[A]", True),
    (Arguments, "args foo as", False),
    (Arguments, "args foo", False),
    (Arguments, "args", False),
    (Assignment, "<- { nop } ", False),
    (Assignment, "3", False),
    (Assignment, "a <- { nop } ", True),
    (Assignment, "a, <- { nop } ", True),
    (Assignment, "a,b <- { nop } ", True),
    (Assignment, "a,b, <- { nop } ", True),
    (Assignment, "a,b,c <- { nop } ", True),
    (Assignment, "a,b,c, <- { nop } ", True),
    (Boolean, "", False),
    (Boolean, "3", False),
    (Boolean, "false", True),
    (Boolean, "true", True),
    (Branch, 'if true { "x" ? }', True),
    (Branch, 'if true { "x" { nop } ! }', True),
    (Branch, 'if true { "x" }', True),
    (Branch, 'if true { "x" 3 }', True),
    (Branch, "", False),
    (Branch, "3", False),
    (Branch, "if true { if true { nop } else { nop } }", True),
    (Branch, "if true { nop } else ", False),
    (Branch, "if true { nop } else { nop }", True),
    (Branch, "if true { nop } else { nop", False),
    (Branch, "if true { nop } else {", False),
    (Branch, "if true { nop }", True),
    (Branch, "if true { nop", False),
    (Branch, "if true { while true { nop } }", True),
    (Branch, "if true {", False),
    (Branch, "if true", False),
    (Branch, "if", False),
    (CaseBlock, "", False),
    (CaseBlock, "3", False),
    (CaseBlock, "case a:b { nop }", True),
    (CaseBlock, "case a:b as c { nop }", True),
    (CaseBlock, "case a:b as c,d { nop }", True),
    (CaseLabel, "", False),
    (CaseLabel, "3", False),
    (CaseLabel, "a:", False),
    (CaseLabel, "a:b as c,", True),
    (CaseLabel, "a:b as c,d,", True),
    (CaseLabel, "a:b as c,d", True),
    (CaseLabel, "a:b as c", True),
    (CaseLabel, "a:b as", False),
    (CaseLabel, "a:b", True),
    (CaseLabel, "a", False),
    (CommaSeparatedTypeList, "", False),
    (CommaSeparatedTypeList, "3", False),
    (CommaSeparatedTypeList, "fn[][],", True),
    (CommaSeparatedTypeList, "fn[][]", True),
    (CommaSeparatedTypeList, "fn[int][vec[str]], fn[int][vec[str]]", True),
    (CommaSeparatedTypeList, "int, bool", True),
    (CommaSeparatedTypeList, "int,", True),
    (CommaSeparatedTypeList, "int", True),
    (CommaSeparatedTypeList, "vec[str], vec[str]", True),
    (CommaSeparatedTypeList, "vec[str]", True),
    (DefaultBlock, "", False),
    (DefaultBlock, "3", False),
    (DefaultBlock, "default { nop ", False),
    (DefaultBlock, "default { nop }", True),
    (DefaultBlock, "default {", False),
    (DefaultBlock, "default", False),
    (Enum, "", False),
    (Enum, "3", False),
    (Enum, "enum foo { a }", True),
    (Enum, "enum foo { a as { int } }", True),
    (Enum, "enum foo { a as { int, } }", True),
    (Enum, "enum foo { a as { int, str } }", True),
    (Enum, "enum foo { a as { vec[str], map[int, bool] } }", True),
    (Enum, "enum foo { a as int }", True),
    (Enum, "enum foo { a as int, }", True),
    (Enum, "enum foo {", False),
    (Enum, "enum foo {}", False),
    (EnumDeclaration, "", False),
    (EnumDeclaration, "3", False),
    (EnumDeclaration, "enum foo", True),
    (EnumDeclaration, "enum", False),
    (EnumVariant, "", False),
    (EnumVariant, "3", False),
    (EnumVariant, "a as { int }", True),
    (EnumVariant, "a as { int, }", True),
    (EnumVariant, "a as { int, str }", True),
    (EnumVariant, "a as { int, str, }", True),
    (EnumVariant, "a as { vec[str], map[int, set[str]] }", True),
    (EnumVariant, "a as {", False),
    (EnumVariant, "a as {}", False),
    (EnumVariant, "a as int", True),
    (EnumVariant, "a as map[str, set[int]]", True),
    (EnumVariant, "a as", False),
    (EnumVariant, "a", True),
    (EnumVariantAssociatedData, "{ int }", True),
    (EnumVariantAssociatedData, "{ int, }", True),
    (EnumVariantAssociatedData, "{ int, str }", True),
    (EnumVariantAssociatedData, "{ int, str, }", True),
    (EnumVariantAssociatedData, "{ int", False),
    (EnumVariantAssociatedData, "{ vec[str], map[int, set[str]] }", True),
    (EnumVariantAssociatedData, "{", False),
    (EnumVariantAssociatedData, "{}", False),
    (EnumVariantAssociatedData, "3", False),
    (EnumVariantAssociatedData, "int", True),
    (EnumVariantAssociatedData, "map[str, set[int]]", True),
    (EnumVariants, "", False),
    (EnumVariants, "3", False),
    (EnumVariants, "a as int,", True),
    (EnumVariants, "a as int,b as str,", True),
    (EnumVariants, "a as int", True),
    (EnumVariants, "a,", True),
    (EnumVariants, "a,b", True),
    (EnumVariants, "a", True),
    (FlatTypeLiteral, "", False),
    (FlatTypeLiteral, "3", False),
    (FlatTypeLiteral, "foo", True),
    (FlatTypeLiteral, "foo[", False),
    (FlatTypeLiteral, "foo[]", False),
    (FlatTypeLiteral, "foo[A,", False),
    (FlatTypeLiteral, "foo[A,]", True),
    (FlatTypeLiteral, "foo[A,B,]", True),
    (FlatTypeLiteral, "foo[A,B,C,]", True),
    (FlatTypeLiteral, "foo[A,B,C", False),
    (FlatTypeLiteral, "foo[A,B,C]", True),
    (FlatTypeLiteral, "foo[A,B", False),
    (FlatTypeLiteral, "foo[A,B]", True),
    (FlatTypeLiteral, "foo[A", False),
    (FlatTypeLiteral, "foo[A[B]]", False),
    (FlatTypeLiteral, "foo[A]", True),
    (FlatTypeParams, "", False),
    (FlatTypeParams, "[,A]", False),
    (FlatTypeParams, "[", False),
    (FlatTypeParams, "[]", False),
    (FlatTypeParams, "[A,", False),
    (FlatTypeParams, "[A,]", True),
    (FlatTypeParams, "[A,B,]", True),
    (FlatTypeParams, "[A,B,C,]", True),
    (FlatTypeParams, "[A,B,C]", True),
    (FlatTypeParams, "[A,B", False),
    (FlatTypeParams, "[A,B]", True),
    (FlatTypeParams, "[A", False),
    (FlatTypeParams, "[A]", True),
    (FlatTypeParams, "3", False),
    (ForeachLoop, "", False),
    (ForeachLoop, "3", False),
    (ForeachLoop, "foreach { nop ", False),
    (ForeachLoop, "foreach { nop }", True),
    (ForeachLoop, "foreach {", False),
    (ForeachLoop, "foreach", False),
    (Function, "3", False),
    (Function, "fn foo { nop }", True),
    (Function, "fn foo { nop", False),
    (Function, "fn foo {", False),
    (Function, "fn foo args a as b { while true { nop } }", True),
    (Function, "fn foo args a as int { nop }", True),
    (Function, "fn foo args a as vec[map[int,str]] { nop }", True),
    (Function, "fn foo", False),
    (Function, "fn", False),
    (FunctionBody, '"foo" ?', True),
    (FunctionBody, '"foo" { nop } !', True),
    (FunctionBody, '"foo"', True),
    (FunctionBody, 'if true { nop } "foo" ?', True),
    (FunctionBody, 'if true { nop } "foo" { nop } !', True),
    (FunctionBody, 'if true { nop } "foo"', True),
    (FunctionBody, "", False),
    (FunctionBody, "3", True),
    (FunctionBody, "case", False),
    (FunctionBody, "false", True),
    (FunctionBody, "foo:bar", True),
    (FunctionBody, "foo", True),
    (FunctionBody, "foo[A,]", True),
    (FunctionBody, "foo[A,B,]", True),
    (FunctionBody, "foo[A,B]", True),
    (FunctionBody, "foo[A]", True),
    (FunctionBody, "if true { nop } 3", True),
    (FunctionBody, "if true { nop } else { nop }", True),
    (FunctionBody, "if true { nop } false", True),
    (FunctionBody, "if true { nop } foo:bar", True),
    (FunctionBody, "if true { nop } foo", True),
    (FunctionBody, "if true { nop } foo[A,]", True),
    (FunctionBody, "if true { nop } foo[A,B,]", True),
    (FunctionBody, "if true { nop } foo[A,B]", True),
    (FunctionBody, "if true { nop } foo[A]", True),
    (FunctionBody, "if true { nop } if true { nop } else { nop }", True),
    (FunctionBody, "if true { nop } if true { nop }", True),
    (FunctionBody, "if true { nop } while true { nop }", True),
    (FunctionBody, "if true { nop }", True),
    (FunctionBody, "while true { nop }", True),
    (FunctionBodyBlock, "", False),
    (FunctionBodyBlock, "{ nop }", True),
    (FunctionBodyBlock, "{ nop", False),
    (FunctionBodyBlock, "{", False),
    (FunctionBodyBlock, "3", False),
    (FunctionBodyItem, '"foo" ?', True),
    (FunctionBodyItem, '"foo" { nop } !', True),
    (FunctionBodyItem, '"foo"', True),
    (FunctionBodyItem, "", False),
    (FunctionBodyItem, "3", True),
    (FunctionBodyItem, "case", False),
    (FunctionBodyItem, "false", True),
    (FunctionBodyItem, "foo:bar", True),
    (FunctionBodyItem, "foo", True),
    (FunctionBodyItem, "foo[A,]", True),
    (FunctionBodyItem, "foo[A,B,]", True),
    (FunctionBodyItem, "foo[A,B]", True),
    (FunctionBodyItem, "foo[A]", True),
    (FunctionBodyItem, "if true { nop } else { nop }", True),
    (FunctionBodyItem, "if true { nop }", True),
    (FunctionBodyItem, "while true { nop }", True),
    (FunctionCall, "", False),
    (FunctionCall, "fn", False),
    (FunctionCall, "foo:bar", True),
    (FunctionCall, "foo", True),
    (FunctionCall, "foo[A,]", True),
    (FunctionCall, "foo[A,B,]", True),
    (FunctionCall, "foo[A,B]", True),
    (FunctionCall, "foo[A]", True),
    (FunctionDeclaration, "", False),
    (FunctionDeclaration, "3", False),
    (FunctionDeclaration, "fn a args b as int, c as int,", True),
    (FunctionDeclaration, "fn a args b as int, c as int", True),
    (FunctionDeclaration, "fn a args b as int,", True),
    (FunctionDeclaration, "fn a args b as int", True),
    (FunctionDeclaration, "fn a args b as vec[int,], c as vec[int,],", True),
    (FunctionDeclaration, "fn a args b as vec[int], c as vec[int],", True),
    (FunctionDeclaration, "fn a args", False),
    (FunctionDeclaration, "fn a return int,", True),
    (FunctionDeclaration, "fn a return int", True),
    (FunctionDeclaration, "fn a return vec[", False),
    (FunctionDeclaration, "fn a return vec[int],map[int,int],", True),
    (FunctionDeclaration, "fn a return vec[int],map[int,int]", True),
    (FunctionDeclaration, "fn a return vec[int],map[int,vec[int]],", True),
    (FunctionDeclaration, "fn a return vec[int]", True),
    (FunctionDeclaration, "fn a return", False),
    (FunctionDeclaration, "fn a return", False),
    (FunctionDeclaration, "fn a,", False),
    (FunctionDeclaration, "fn a", True),
    (FunctionName, "", False),
    (FunctionName, "3", False),
    (FunctionName, "foo:", False),
    (FunctionName, "foo:bar", True),
    (FunctionName, "foo", True),
    (FunctionName, "foo[", False),
    (FunctionName, "foo[]:", False),
    (FunctionName, "foo[]", False),
    (FunctionName, "foo[A,]:bar", True),
    (FunctionName, "foo[A,]", True),
    (FunctionName, "foo[A,B,]:bar", True),
    (FunctionName, "foo[A,B,]", True),
    (FunctionName, "foo[A,B,C,]:bar", True),
    (FunctionName, "foo[A,B,C,]", True),
    (FunctionName, "foo[A,B,C]:bar", True),
    (FunctionName, "foo[A,B,C]", True),
    (FunctionName, "foo[A,B]:bar", True),
    (FunctionName, "foo[A,B]", True),
    (FunctionName, "foo[A]:bar", True),
    (FunctionName, "foo[A]", True),
    (FunctionPointerTypeLiteral, "fn [][]", True),
    (FunctionPointerTypeLiteral, "fn[ ][]", True),
    (FunctionPointerTypeLiteral, "fn[,][]", False),
    (FunctionPointerTypeLiteral, "fn[] []", True),
    (FunctionPointerTypeLiteral, "fn[][ ]", True),
    (FunctionPointerTypeLiteral, "fn[][,]", False),
    (FunctionPointerTypeLiteral, "fn[][]", True),
    (FunctionPointerTypeLiteral, "fn[][int,int,]", True),
    (FunctionPointerTypeLiteral, "fn[][int,int]", True),
    (FunctionPointerTypeLiteral, "fn[][int]", True),
    (FunctionPointerTypeLiteral, "fn[fn[][]][]", True),
    (FunctionPointerTypeLiteral, "fn[int,][]", True),
    (FunctionPointerTypeLiteral, "fn[int,int,][]", True),
    (FunctionPointerTypeLiteral, "fn[int,int][]", True),
    (FunctionPointerTypeLiteral, "fn[int][]", True),
    (FunctionPointerTypeLiteral, "fn[vec[int]][]", True),
    (GetFunctionPointer, '"foo" fn', True),
    (GetFunctionPointer, '"foo"', False),
    (GetFunctionPointer, "", False),
    (GetFunctionPointer, "3", False),
    (Import, 'from "a" import b as c,', True),
    (Import, 'from "a" import b as c,d as e,', True),
    (Import, 'from "a" import b as c,d as e', True),
    (Import, 'from "a" import b as c,d,', True),
    (Import, 'from "a" import b as c,d,', True),
    (Import, 'from "a" import b as c,d', True),
    (Import, 'from "a" import b as c', True),
    (Import, 'from "a" import b,', True),
    (Import, 'from "a" import b,d as e,', True),
    (Import, 'from "a" import b,d,', True),
    (Import, 'from "a" import b', True),
    (Import, 'from "a" import', False),
    (Import, 'from "a"', False),
    (Import, "", False),
    (Import, "3", False),
    (Import, "from a import b", False),
    (Import, "from", False),
    (ImportItem, "", False),
    (ImportItem, "3", False),
    (ImportItem, "foo as bar", True),
    (ImportItem, "foo as", False),
    (ImportItem, "foo", True),
    (ImportItems, "", False),
    (ImportItems, "3", False),
    (ImportItems, "foo as bar,", True),
    (ImportItems, "foo as bar,foo as bar,", True),
    (ImportItems, "foo as bar,foo as bar", True),
    (ImportItems, "foo as bar,foo as", False),
    (ImportItems, "foo as bar,foo,", True),
    (ImportItems, "foo as bar,foo", True),
    (ImportItems, "foo as bar,foo", True),
    (ImportItems, "foo as bar", True),
    (ImportItems, "foo as", False),
    (ImportItems, "foo,", True),
    (ImportItems, "foo,bar,", True),
    (ImportItems, "foo,bar", True),
    (ImportItems, "foo,foo as bar,", True),
    (ImportItems, "foo,foo as bar", True),
    (ImportItems, "foo", True),
    (MatchBlock, "", False),
    (MatchBlock, "3", False),
    (MatchBlock, "match { }", True),
    (MatchBlock, "match { case a:b { nop } }", True),
    (MatchBlock, "match { case a:b { nop } default { nop } }", True),
    (MatchBlock, "match { default { nop } }", True),
    (MatchBlock, "match {", False),
    (MatchBlock, "match", False),
    (ReturnTypes, "", False),
    (ReturnTypes, "3", False),
    (ReturnTypes, "return foo,", True),
    (ReturnTypes, "return foo", True),
    (ReturnTypes, "return foo[A,B],", True),
    (ReturnTypes, "return foo[A,B],foo[A,B],", True),
    (ReturnTypes, "return foo[A,B],foo[A,B]", True),
    (ReturnTypes, "return foo[A,B]", True),
    (ReturnTypes, "return foo[A],", True),
    (ReturnTypes, "return foo[A]", True),
    (ReturnTypes, "return", False),
    (SourceFile, 'from "foo" import bar', True),
    (SourceFile, "", True),
    (SourceFile, "3", False),
    (SourceFile, "builtin fn a builtin fn b", True),
    (SourceFile, "builtin fn a", True),
    (SourceFile, "builtin struct a builtin struct b", True),
    (SourceFile, "builtin struct a", True),
    (SourceFile, "builtin struct a", True),
    (SourceFile, "builtin struct a[A,B] builtin fn a args b as map[int,int]", True),
    (SourceFile, "enum foo { x as int }", True),
    (SourceFile, "fn a { nop }", True),
    (SourceFile, "fn a", False),
    (SourceFile, "struct a", False),
    (SourceFile, "struct foo { x as int }", True),
    (Struct, "", False),
    (Struct, "3", False),
    (Struct, "struct a { b as int }", True),
    (Struct, "struct a { b as int, }", True),
    (Struct, "struct a { b as int, }", True),
    (Struct, "struct a { b as int, c as int }", True),
    (Struct, "struct a { b as int, c as int, }", True),
    (Struct, "struct a { b as map[int,vec[int]] }", True),
    (Struct, "struct a { b as map[int,vec[int]], }", True),
    (Struct, "struct a {", False),
    (Struct, "struct a {}", True),
    (Struct, "struct a", False),
    (StructDeclaration, "", False),
    (StructDeclaration, "3", False),
    (StructDeclaration, "struct foo", True),
    (StructDeclaration, "struct foo[", False),
    (StructDeclaration, "struct foo[]", False),
    (StructDeclaration, "struct foo[A,", False),
    (StructDeclaration, "struct foo[A,]", True),
    (StructDeclaration, "struct foo[A,B,]", True),
    (StructDeclaration, "struct foo[A,B,C,]", True),
    (StructDeclaration, "struct foo[A,B,C", False),
    (StructDeclaration, "struct foo[A,B,C]", True),
    (StructDeclaration, "struct foo[A,B", False),
    (StructDeclaration, "struct foo[A,B]", True),
    (StructDeclaration, "struct foo[A", False),
    (StructDeclaration, "struct foo[A]", True),
    (StructField, "", False),
    (StructField, "3", False),
    (StructField, "x as fn[vec[int]][set[str]]", True),
    (StructField, "x as int", True),
    (StructField, "x as", False),
    (StructField, "x", False),
    (StructFieldQuery, '"foo" ?', True),
    (StructFieldQuery, '"foo"', False),
    (StructFieldQuery, "", False),
    (StructFieldQuery, "3", False),
    (StructFields, "", False),
    (StructFields, "3", False),
    (StructFields, "x as int, y as str,", True),
    (StructFields, "x as int, y as str", True),
    (StructFields, "x as int,", True),
    (StructFields, "x as int", True),
    (StructFields, "x as vec[int], y as map[str, set[int]]", True),
    (StructFieldUpdate, '"foo" { "x" ? } !', True),
    (StructFieldUpdate, '"foo" { "x" { nop } !', False),
    (StructFieldUpdate, '"foo" { "x" } !', True),
    (StructFieldUpdate, '"foo" { "x" 3 } !', True),
    (StructFieldUpdate, '"foo" { nop } !', True),
    (StructFieldUpdate, '"foo" { nop }', False),
    (StructFieldUpdate, '"foo" { nop', False),
    (StructFieldUpdate, '"foo" { while true { nop } } !', True),
    (StructFieldUpdate, '"foo" { while True { nop } } !', True),
    (StructFieldUpdate, '"foo" {', False),
    (StructFieldUpdate, '"foo"', False),
    (StructFieldUpdate, "", False),
    (StructFieldUpdate, "3", False),
    (TypeLiteral, "", False),
    (TypeLiteral, "[A]", False),
    (TypeLiteral, "3", False),
    (TypeLiteral, "const foo", True),
    (TypeLiteral, "const foo[A]", True),
    (TypeLiteral, "foo", True),
    (TypeLiteral, "foo[,", False),
    (TypeLiteral, "foo[[A]B]", False),
    (TypeLiteral, "foo[]", False),
    (TypeLiteral, "foo[A,", False),
    (TypeLiteral, "foo[A,]", True),
    (TypeLiteral, "foo[A,B,]", True),
    (TypeLiteral, "foo[A,B]", True),
    (TypeLiteral, "foo[A", False),
    (TypeLiteral, "foo[A[B,],]", True),
    (TypeLiteral, "foo[A[B,]]", True),
    (TypeLiteral, "foo[A[B[C]],D]", True),
    (TypeLiteral, "foo[A[B],C]", True),
    (TypeLiteral, "foo[A[B]]", True),
    (TypeLiteral, "foo[A]", True),
    (TypeLiteral, "foo[const A,B]", True),
    (TypeLiteral, "foo[const A]", True),
    (TypeOrFunctionPointerLiteral, "", False),
    (TypeOrFunctionPointerLiteral, "3", False),
    (TypeOrFunctionPointerLiteral, "fn[str][vec[int]]", True),
    (TypeOrFunctionPointerLiteral, "int", True),
    (TypeOrFunctionPointerLiteral, "vec[str]", True),
    (TypeParams, "", False),
    (TypeParams, "[,", False),
    (TypeParams, "[[A]B]", False),
    (TypeParams, "[]", False),
    (TypeParams, "[A,", False),
    (TypeParams, "[A,]", True),
    (TypeParams, "[A,B,]", True),
    (TypeParams, "[A,B]", True),
    (TypeParams, "[A", False),
    (TypeParams, "[A[B,]]", True),
    (TypeParams, "[A[B[C]],D]", True),
    (TypeParams, "[A[B],C]", True),
    (TypeParams, "[A[B]]", True),
    (TypeParams, "[A]", True),
    (TypeParams, "3", False),
    (UseBlock, "3", False),
    (UseBlock, "use { nop } ", False),
    (UseBlock, "use a { nop } ", True),
    (UseBlock, "use a, { nop } ", True),
    (UseBlock, "use a,b { nop } ", True),
    (UseBlock, "use a,b, { nop } ", True),
    (UseBlock, "use a,b,c { nop } ", True),
    (UseBlock, "use a,b,c, { nop } ", True),
    (Variables, "3", False),
    (Variables, "a,", True),
    (Variables, "a,b,", True),
    (Variables, "a,b,c,", True),
    (Variables, "a,b,c", True),
    (Variables, "a,b", True),
    (Variables, "a", True),
    (WhileLoop, 'while true { "x" ? }', True),
    (WhileLoop, 'while true { "x" { nop } ! }', True),
    (WhileLoop, 'while true { "x" }', True),
    (WhileLoop, 'while true { "x" 3 }', True),
    (WhileLoop, "", False),
    (WhileLoop, "3", False),
    (WhileLoop, "while true { if true { nop } else { nop } }", True),
    (WhileLoop, "while true { nop }", True),
    (WhileLoop, "while true { nop", False),
    (WhileLoop, "while true { while true { nop } }", True),
    (WhileLoop, "while true {", False),
    (WhileLoop, "while true", False),
    (WhileLoop, "while", False),
]


@pytest.mark.parametrize(
    ["model_type", "text", "should_parse"],
    [
        pytest.param(
            model_type, text, should_parse, id=f"{model_type.__name__}-{repr(text)}"
        )
        for model_type, text, should_parse in PARSE_MODEL_TEST_VALUES
    ],
)
def test_parser(model_type: Type[AaaParseModel], text: str, should_parse: bool) -> None:
    node_type = MODEL_TO_NODE_TYPE[model_type]

    try:
        model = AaaParser(False).parse_text(text, node_type)
    except ParseError:
        assert not should_parse
    else:
        assert should_parse
        assert isinstance(model, model_type)


def test_all_models_are_tested() -> None:
    all_models = set(NODE_TYPE_TO_MODEL.values())
    tested_models = {item[0] for item in PARSE_MODEL_TEST_VALUES}

    untested_models = all_models - tested_models

    if untested_models:
        raise Exception(
            "Found untested models: "
            + ", ".join(sorted(model.__name__ for model in untested_models)),
        )


def get_source_files() -> List[Path]:
    aaa_files: Set[Path] = {
        Path(file).resolve()
        for file in glob("**/*.aaa", root_dir=aaa_project_root(), recursive=True)
    }
    return sorted(aaa_files)


@pytest.mark.parametrize(
    ["file"],
    [pytest.param(file, id=str(file)) for file in get_source_files()],
)
def test_parse__all_source_files(file: Path) -> None:
    AaaParser(False).parse_file(file)


@pytest.mark.parametrize(
    ["escaped", "expected_unescaped"],
    [
        ("", ""),
        ("abc", "abc"),
        ("\\\\", "\\"),
        ("a\\\\b", "a\\b"),
        ("\\\\b", "\\b"),
        ("a\\\\", "a\\"),
        ('a\\"b', 'a"b'),
        ("a\\'b", "a'b"),
        ("a\\/b", "a/b"),
        ("a\\0b", "a\0b"),
        ("a\\bb", "a\bb"),
        ("a\\eb", "a\x1bb"),
        ("a\\fb", "a\fb"),
        ("a\\nb", "a\nb"),
        ("a\\rb", "a\rb"),
        ("a\\tb", "a\tb"),
        ("a\\u0000b", "a\u0000b"),
        ("a\\u9999b", "a\u9999b"),
        ("a\\uaaaab", "a\uaaaab"),
        ("a\\uffffb", "a\uffffb"),
        ("a\\uAAAAb", "a\uaaaab"),
        ("a\\uFFFFb", "a\uffffb"),
        ("a\\U00000000b", "a\U00000000b"),
        ("a\\U0001F600b", "a\U0001F600b"),
    ],
)
def test_unescape_string(escaped: str, expected_unescaped: str) -> None:
    assert expected_unescaped == unescape_string(escaped)
