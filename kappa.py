#!/usr/bin/env python3
"""Kappa interpreter - patched parse_code (one-parser-per-top-level-expr).
"""

import sys, re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

# --- Lexer ---
Token = Tuple[str, str, int, int]
spec = [
    ('NUMBER', r'\d+'),
    ('TRUE', r'true'),
    ('FALSE', r'false'),
    ('LET', r'let'),
    ('FN', r'fn'),
    ('IF', r'if'),
    ('THEN', r'then'),
    ('ELSE', r'else'),
    ('MATCH', r'match'),
    ('INL', r'inl'),
    ('INR', r'inr'),
    ('FIX', r'fix'),
    ('IMPORT', r'import'),
    ('IDENT', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('STRING', r'"(\\.|[^"\\])*"'),
    ('EQ', r'=='),
    ('ARROW', r'->'),
    ('COLON', r':'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('COMMA', r','),
    ('PIPE', r'\|'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('STAR', r'\*'),
    ('SLASH', r'/'),
    ('ASSIGN', r'='),
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t]+'),
    ('COMMENT', r'#.*'),
]
tok_re = '|'.join('(?P<%s>%s)' % pair for pair in spec)
get_token = re.compile(tok_re).match

def lex(code):
    pos = 0; line = 1; col = 1
    while True:
        m = get_token(code, pos)
        if not m:
            if pos >= len(code):
                break
            raise SyntaxError(f'Unexpected char at {line}:{col}')
        kind = m.lastgroup; text = m.group(kind)
        if kind == 'NEWLINE':
            line += 1; col = 1
        elif kind not in ('SKIP','COMMENT'):
            yield (kind, text, line, col)
        pos = m.end(); col += m.end() - m.start()

# --- AST ---
class Expr: pass
@dataclass
class EInt(Expr): value:int
@dataclass
class EBool(Expr): value:bool
@dataclass
class EVar(Expr): name:str
@dataclass
class ELet(Expr): name:str; expr:Expr; body:Expr
@dataclass
class EFn(Expr): param:str; ptype:any; rtype:any; body:Expr
@dataclass
class EApp(Expr): fn:Expr; arg:Expr
@dataclass
class EIf(Expr): cond:Expr; tbranch:Expr; fbranch:Expr
@dataclass
class EPair(Expr): left:Expr; right:Expr
@dataclass
class EList(Expr): items:List[Expr]
@dataclass
class EMatch(Expr): expr:Expr; branches:List[Tuple[Any,Expr]]
@dataclass
class EInl(Expr): expr:Expr
@dataclass
class EInr(Expr): expr:Expr
@dataclass
class EFix(Expr): expr:Expr
@dataclass
class EImport(Expr): path:str

# Patterns
class Pattern: pass
@dataclass
class PEmpty(Pattern): pass
@dataclass
class PCons(Pattern): head:str; tail:str
@dataclass
class PInl(Pattern): name:str
@dataclass
class PInr(Pattern): name:str
@dataclass
class PVar(Pattern): name:str
@dataclass
class PWildcard(Pattern): pass

# Types
class Type: pass
@dataclass(frozen=True)
class TInt(Type): pass
@dataclass(frozen=True)
class TBool(Type): pass
@dataclass(frozen=True)
class TFun(Type): arg:Type; ret:Type
@dataclass(frozen=True)
class TPair(Type): left:Type; right:Type
@dataclass(frozen=True)
class TList(Type): elem:Type
@dataclass(frozen=True)
class TSum(Type): left:Type; right:Type

# --- Parser ---
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else ("EOF","",0,0)
    def next(self):
        t = self.peek(); self.i += 1; return t
    def accept(self, kind):
        if self.peek()[0] == kind: return self.next()
        return None
    def expect(self, kind):
        t = self.next()
        if t[0] != kind:
            raise SyntaxError(f"Expected {kind} but got {t[0]} at {t[2]}:{t[3]}")
        return t

    def parse(self):
        return self.parse_expr()

    def parse_expr(self):
        if self.peek()[0] == "LET":
            self.next()
            t = self.expect("IDENT"); name = t[1]
            self.expect("ASSIGN")
            expr = self.parse_expr()
            return ELet(name, expr, EVar(name))
        if self.peek()[0] == "IMPORT":
            self.next(); t = self.expect("STRING"); path = t[1][1:-1]; return EImport(path)
        return self.parse_binop()

    _prec = { "EQ": 10, "PLUS": 20, "MINUS": 20, "STAR": 30, "SLASH": 30 }

    def parse_binop(self, min_prec=0):
        left = self.parse_atom()
        while True:
            tok = self.peek()[0]
            if tok not in self._prec: break
            prec = self._prec[tok]
            if prec < min_prec: break
            op = self.next()[0]
            right = self.parse_binop(prec + 1)
            if op == "PLUS": left = EApp(EApp(EVar("+"), left), right)
            elif op == "MINUS": left = EApp(EApp(EVar("-"), left), right)
            elif op == "STAR": left = EApp(EApp(EVar("*"), left), right)
            elif op == "SLASH": left = EApp(EApp(EVar("/"), left), right)
            elif op == "EQ": left = EApp(EApp(EVar("=="), left), right)
        return left

    def parse_atom(self):
        t = self.peek()
        if t[0] == "NUMBER":
            self.next(); return EInt(int(t[1]))
        if t[0] in ("TRUE","FALSE"):
            self.next(); return EBool(True if t[0]=="TRUE" else False)
        if t[0] == "IDENT":
            node = EVar(self.next()[1])
            while self.peek()[0] in ("NUMBER","IDENT","LPAREN","LBRACKET","TRUE","FALSE","INL","INR","FIX"):
                arg = self.parse_atom(); node = EApp(node, arg)
            return node
        if t[0] == "LPAREN":
            self.next()
            expr = self.parse_expr()
            self.expect("RPAREN")
            node = expr
            while self.peek()[0] in ("NUMBER","IDENT","LPAREN","LBRACKET","TRUE","FALSE","INL","INR","FIX"):
                arg = self.parse_atom(); node = EApp(node, arg)
            return node
        if t[0] == "LBRACKET":
            self.next(); items = []
            if self.peek()[0] != "RBRACKET":
                items.append(self.parse_expr())
                while self.accept("COMMA"): items.append(self.parse_expr())
            self.expect("RBRACKET"); return EList(items)
        if t[0] == "FN":
            self.next(); pname = self.expect("IDENT")[1]; self.expect("COLON")
            ptype = self.parse_type()
            # tolerate stray NEWLINE before arrow
            while self.peek()[0] == "NEWLINE": self.next()
            self.expect("ARROW")
            body = self.parse_expr()
            return EFn(pname, ptype, None, body)
        if t[0] == "IF":
            self.next(); cond = self.parse_expr(); self.expect("THEN")
            tbranch = self.parse_expr(); self.expect("ELSE")
            fbranch = self.parse_expr(); return EIf(cond, tbranch, fbranch)
        if t[0] == "MATCH":
            self.next(); expr = self.parse_expr(); self.expect("LBRACE")
            branches = []
            while self.peek()[0] != "RBRACE":
                pat = self.parse_pattern(); self.expect("ARROW"); body = self.parse_expr()
                branches.append((pat, body))
            self.expect("RBRACE"); return EMatch(expr, branches)
        if t[0] == "INL":
            self.next(); e = self.parse_atom(); return EInl(e)
        if t[0] == "INR":
            self.next(); e = self.parse_atom(); return EInr(e)
        if t[0] == "FIX":
            self.next(); e = self.parse_atom(); return EFix(e)
        raise SyntaxError(f"Unexpected token {t}")

    def parse_pattern(self):
        t = self.peek()
        if t[0] == "LBRACKET":
            self.next()
            if self.peek()[0] == "RBRACKET": self.next(); return PEmpty()
            head = self.expect("IDENT")[1]; self.expect("PIPE"); tail = self.expect("IDENT")[1]; self.expect("RBRACKET")
            return PCons(head, tail)
        if t[0] == "INL":
            self.next(); name = self.expect("IDENT")[1]; return PInl(name)
        if t[0] == "INR":
            self.next(); name = self.expect("IDENT")[1]; return PInr(name)
        if t[0] == "IDENT":
            return PVar(self.next()[1])
        return PWildcard()

    def parse_type(self):
        def parse_atomic():
            t = self.peek()
            if t[0] == "IDENT":
                name = self.next()[1]
                if name == "Int": return TInt()
                if name == "Bool": return TBool()
                raise SyntaxError(f"Unknown type {name}")
            if t[0] == "LBRACKET":
                self.next(); elem = self.parse_type(); self.expect("RBRACKET"); return TList(elem)
            if t[0] == "LPAREN":
                self.next(); inner = self.parse_type()
                if self.accept("COMMA"):
                    right = self.parse_type(); self.expect("RPAREN"); return TPair(inner, right)
                else:
                    self.expect("RPAREN"); return inner
            raise SyntaxError(f"Unexpected token in type: {t}")
        left = parse_atomic()
        while self.peek()[0] == "ARROW":
            if self.i + 1 < len(self.tokens):
                nxt = self.tokens[self.i + 1]
                if nxt[0] in ("LPAREN","LBRACKET") or (nxt[0] == "IDENT" and nxt[1] in ("Int","Bool")):
                    self.next()
                    right = self.parse_type()
                    left = TFun(left, right)
                    continue
            break
        return left

# --- Type checker ---
class TypeError(Exception): pass
def type_eq(a,b): return a==b

def typeof(expr, env: Dict[str, Type], context=""):
    try:
        if isinstance(expr, EInt): return TInt()
        if isinstance(expr, EBool): return TBool()
        if isinstance(expr, EVar):
            if expr.name in env: return env[expr.name]
            raise TypeError(f"Unbound variable {expr.name}")
        if isinstance(expr, ELet):
            t = typeof(expr.expr, env, context + f" in let {expr.name}")
            env2 = env.copy(); env2[expr.name]=t
            return typeof(expr.body, env2, context + f" in let {expr.name} body")
        if isinstance(expr, EFn):
            env2 = env.copy(); env2[expr.param]=expr.ptype
            body_t = typeof(expr.body, env2, context + f" in function body")
            annotated = getattr(expr, "rtype", None)
            if annotated is not None and not type_eq(body_t, annotated):
                raise TypeError(f"Function annotated return type {annotated} does not match body type {body_t}")
            return TFun(expr.ptype, body_t)
        if isinstance(expr, EApp):
            tf = typeof(expr.fn, env, context + f" in function application")
            ta = typeof(expr.arg, env, context + f" in function argument")
            if not isinstance(tf, TFun): 
                raise TypeError(f"Call of non-function: got {tf}")
            if not type_eq(ta, tf.arg): 
                raise TypeError(f"Function expects {tf.arg} got {ta}")
            return tf.ret
        if isinstance(expr, EIf):
            tc = typeof(expr.cond, env, context + f" in if condition")
            if not isinstance(tc, TBool): 
                raise TypeError("Condition in if-expression must be Bool")
            tt = typeof(expr.tbranch, env, context + f" in if then-branch")
            tf = typeof(expr.fbranch, env, context + f" in if else-branch")
            if not type_eq(tt, tf): 
                raise TypeError("Branches of if must have same type")
            return tt
        if isinstance(expr, EPair):
            l = typeof(expr.left, env, context + f" in pair left element")
            r = typeof(expr.right, env, context + f" in pair right element")
            return TPair(l, r)
        if isinstance(expr, EList):
            if not expr.items: 
                raise TypeError("Empty list literals require explicit annotation (not supported)")
            t0 = typeof(expr.items[0], env, context + f" in list element 0")
            for i, it in enumerate(expr.items[1:]):
                if not type_eq(typeof(it, env, context + f" in list element {i+1}"), t0): 
                    raise TypeError("List items must have the same type")
            return TList(t0)
        if isinstance(expr, EMatch):
            texpr = typeof(expr.expr, env, context + f" in match expression")
            result_type = None
            for pat, body in expr.branches:
                env2 = env.copy()
                if isinstance(pat, PEmpty):
                    if not isinstance(texpr, TList): 
                        raise TypeError("[] pattern requires list")
                elif isinstance(pat, PCons):
                    if not isinstance(texpr, TList): 
                        raise TypeError("[h|t] pattern requires list")
                    env2[pat.head] = texpr.elem
                    env2[pat.tail] = TList(texpr.elem)
                elif isinstance(pat, PInl):
                    if not isinstance(texpr, TSum): 
                        raise TypeError("inl pattern requires a sum type")
                    env2[pat.name] = texpr.left
                elif isinstance(pat, PInr):
                    if not isinstance(texpr, TSum): 
                        raise TypeError("inr pattern requires a sum type")
                    env2[pat.name] = texpr.right
                elif isinstance(pat, PVar):
                    env2[pat.name] = texpr
                body_t = typeof(body, env2, context + f" in match branch")
                if result_type is None: 
                    result_type = body_t
                else:
                    if not type_eq(result_type, body_t): 
                        raise TypeError("Match branches must have the same type")
            if result_type is None: 
                raise TypeError("Empty match")
            return result_type
        if isinstance(expr, EInl):
            t = typeof(expr.expr, env, context + f" in inl expression")
            return TSum(t, TInt())  # Default right type
        if isinstance(expr, EInr):
            t = typeof(expr.expr, env, context + f" in inr expression")
            return TSum(TInt(), t)  # Default left type
        if isinstance(expr, EFix):
            tf = typeof(expr.expr, env, context + f" in fix expression")
            if not isinstance(tf, TFun): 
                raise TypeError("fix expects a function")
            return tf.ret
        if isinstance(expr, EImport):
            return TInt()
        raise TypeError(f"Unhandled expression in typechecker: {expr}")
    except TypeError as e:
        # Enhance error with context
        if context:
            raise TypeError(f"{e}{context}")
        else:
            raise e

# --- Evaluator ---
class Closure:
    def __init__(self, param, body, env):
        self.param=param; self.body=body; self.env=env

def eval_expr(expr, env):
    if isinstance(expr, EInt): return expr.value
    if isinstance(expr, EBool): return expr.value
    if isinstance(expr, EVar):
        if expr.name in env: return env[expr.name]
        raise RuntimeError(f'unbound {expr.name}')
    if isinstance(expr, ELet):
        v = eval_expr(expr.expr, env); env2 = env.copy(); env2[expr.name]=v; return eval_expr(expr.body, env2)
    if isinstance(expr, EFn): return Closure(expr.param, expr.body, env.copy())
    if isinstance(expr, EApp):
        fval = eval_expr(expr.fn, env); aval = eval_expr(expr.arg, env)
        if isinstance(fval, Closure):
            newenv = fval.env.copy(); newenv[fval.param] = aval; return eval_expr(fval.body, newenv)
        if callable(fval): return fval(aval)
        raise RuntimeError('Call of non-function')
    if isinstance(expr, EIf):
        if eval_expr(expr.cond, env): return eval_expr(expr.tbranch, env)
        return eval_expr(expr.fbranch, env)
    if isinstance(expr, EPair):
        return (eval_expr(expr.left, env), eval_expr(expr.right, env))
    if isinstance(expr, EList):
        return [eval_expr(it, env) for it in expr.items]
    if isinstance(expr, EMatch):
        v = eval_expr(expr.expr, env)
        for pat, body in expr.branches:
            if isinstance(pat, PEmpty) and v==[]: return eval_expr(body, env)
            if isinstance(pat, PCons) and isinstance(v, list) and len(v)>=1:
                newenv = env.copy(); newenv[pat.head]=v[0]; newenv[pat.tail]=v[1:]; return eval_expr(body, newenv)
            if isinstance(pat, PInl) and isinstance(v, tuple) and v[0]=='INL':
                newenv = env.copy(); newenv[pat.name]=v[1]; return eval_expr(body, newenv)
            if isinstance(pat, PInr) and isinstance(v, tuple) and v[0]=='INR':
                newenv = env.copy(); newenv[pat.name]=v[1]; return eval_expr(body, newenv)
            if isinstance(pat, PVar):
                newenv = env.copy(); newenv[pat.name]=v; return eval_expr(body, newenv)
            if isinstance(pat, PWildcard):
                return eval_expr(body, env)
        raise RuntimeError('Match failed')
    if isinstance(expr, EInl): return ('INL', eval_expr(expr.expr, env))
    if isinstance(expr, EInr): return ('INR', eval_expr(expr.expr, env))
    if isinstance(expr, EFix):
        f = eval_expr(expr.expr, env)
        if not isinstance(f, Closure): raise RuntimeError('fix expects closure')
        temp_env = f.env.copy(); temp_env[f.param] = None
        result = eval_expr(f.body, temp_env)
        if isinstance(result, Closure):
            temp_env[f.param] = result; result.env = temp_env; return result
        raise RuntimeError('fix expects function-producing closure')
    if isinstance(expr, EImport):
        p = expr.path
        with open(p,'r') as fh: src = fh.read()
        return run_code(src, env)
    raise RuntimeError('Unhandled eval')

# --- Builtins ---
BUILTIN_RUNTIME = {
    "+": lambda x: (lambda y: x + y),
    "-": lambda x: (lambda y: x - y),
    "*": lambda x: (lambda y: x * y),
    "/": lambda x: (lambda y: x // y),
    "==": lambda x: (lambda y: x == y),
    "fst": lambda p: p[0],
    "snd": lambda p: p[1],
}
BUILTIN_TYPES = {
    "+": TFun(TInt(), TFun(TInt(), TInt())),
    "-": TFun(TInt(), TFun(TInt(), TInt())),
    "*": TFun(TInt(), TFun(TInt(), TInt())),
    "/": TFun(TInt(), TFun(TInt(), TInt())),
    "==": TFun(TInt(), TFun(TInt(), TBool())),
    "fst": TFun(TPair(TInt(), TBool()), TInt()),
    "snd": TFun(TPair(TInt(), TBool()), TBool()),
}

# --- Parser for files and runner ---
def parse_code(src):
    """
    Tokenize whole source, then repeatedly parse exactly one top-level expression
    from the remaining token slice by constructing a Parser over that slice.
    This prevents any accidental multi-expression consumption by a single parser.
    """
    toks = list(lex(src))
    exprs: List[Expr] = []
    idx = 0
    # skip leading NEWLINE tokens
    while idx < len(toks) and toks[idx][0] == "NEWLINE":
        idx += 1
    # repeatedly parse one expr from toks[idx:]
    while idx < len(toks) and toks[idx][0] != "EOF":
        # build a parser over the suffix starting at idx
        suffix = toks[idx:]
        p = Parser(suffix)
        expr = p.parse()
        exprs.append(expr)
        # advance idx by how many tokens that parser consumed (p.i)
        idx += p.i
        # consume trailing NEWLINE tokens between top-level forms
        while idx < len(toks) and toks[idx][0] == "NEWLINE":
            idx += 1
    return exprs

def run_code(source: str, env=None):
    source = source.replace('\r\n', '\n').replace('\r', '\n')
    if env is None:
        runtime_env = BUILTIN_RUNTIME.copy()
    else:
        runtime_env = BUILTIN_RUNTIME.copy(); runtime_env.update(env)
    type_env = BUILTIN_TYPES.copy()

    exprs = parse_code(source)

    last_val = None
    for expr in exprs:
        if isinstance(expr, ELet):
            try:
                bound_type = typeof(expr.expr, type_env.copy(), f" in let {expr.name}")
            except Exception as e:
                raise RuntimeError(f"Type error: {e}")
            bound_val = eval_expr(expr.expr, runtime_env)
            type_env[expr.name] = bound_type
            runtime_env[expr.name] = bound_val
            last_val = bound_val
            continue
        try:
            t = typeof(expr, type_env.copy(), " at top-level")
        except Exception as e:
            raise RuntimeError(f"Type error: {e}")
        val = eval_expr(expr, runtime_env)
        last_val = val
    return last_val

# --- REPL ---
def repl():
    print('Kappa REPL (type expressions).')
    print('Type "exit" or "quit" to exit, or use Ctrl-Z + Enter on Windows.')
    runtime_env = BUILTIN_RUNTIME.copy()
    type_env = BUILTIN_TYPES.copy()
    
    while True:
        try:
            line = input('kappa> ')
            if not line.strip():
                continue
            
            # Check for exit commands
            if line.strip().lower() in ('exit', 'quit', ':q'):
                print('Goodbye!')
                break
                
            try:
                exprs = parse_code(line)
                if not exprs:
                    continue
                    
                expr = exprs[0]
                
                try:
                    t = typeof(expr, type_env.copy(), " in REPL")
                except Exception as e:
                    print('Type error:', e)
                    continue
                    
                val = eval_expr(expr, runtime_env)
                if isinstance(expr, ELet):
                    bound_type = typeof(expr.expr, type_env.copy(), f" in let {expr.name}")
                    bound_val = eval_expr(expr.expr, runtime_env)
                    type_env[expr.name] = bound_type
                    runtime_env[expr.name] = bound_val
                    print('=>', bound_val)
                else:
                    print('=>', val)
                    
            except SyntaxError as e:
                print('Syntax error:', e)
            except Exception as e:
                print('Error:', e)
                
        except (KeyboardInterrupt):
            print('\nInterrupted. Type "exit" to quit.')
            continue
        except (EOFError):
            print('\nGoodbye!')
            break

# --- CLI ---
def main():
    if len(sys.argv) >= 2 and sys.argv[1] == 'repl':
        repl()
        return
    if len(sys.argv) >= 3 and sys.argv[1] == 'run':
        path = sys.argv[2]
        try:
            with open(path, 'r') as fh: 
                src = fh.read()
            env = BUILTIN_RUNTIME.copy()
            val = run_code(src, env)
            if val is not None:
                print(val)
        except FileNotFoundError:
            print(f'Error: File not found: {path}')
        except Exception as e:
            print('Error:', e)
        return
    print('Usage: kappa.py repl | run <file.kappa>')

if __name__ == '__main__':
    main()