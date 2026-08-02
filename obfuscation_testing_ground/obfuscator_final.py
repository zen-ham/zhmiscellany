"""
Rewritten obfuscate_python.

Same concept as the original (a code *diluter*: it strips prints/comments and
injects plausible-but-dead decoy statements around your real code so the logic
is buried in junk -- it does NOT rename your real identifiers), but the
hand-rolled string parsing that decided *where* a decoy could go has been
replaced with a real `ast` + `tokenize` pass. That makes it handle all valid
Python (multi-line literals with/without trailing commas, dict/set/comprehension
literals, triple-quoted strings, f-strings, `#` inside strings, backslash
continuations, decorators, else/elif/except/finally, match/case, semicolons,
docstrings, __future__ imports, ...), and it now also emits decoy *classes*, not
just decoy functions.

Drop-in: same signature as the original plus an optional `seed=`.
Deterministic by default (same input -> same output); pass `seed=<int>` for a
different-but-reproducible result.
"""


def obfuscate_python(python_code_string,
                     do_not_obfuscate_indent_block_comment='# DNO',
                     remove_prints=True,
                     remove_comments=True,
                     add_lines=True,
                     new_line_ratio=10,
                     new_lines_target=0,
                     entangle=False,
                     seed=None):
    """
    Rewritten obfuscate_python.

    Same concept as the original (a code *diluter*: it strips prints/comments and
    injects plausible-but-dead decoy statements around your real code so the logic
    is buried in junk -- it does NOT rename your real identifiers), but the
    hand-rolled string parsing that decided *where* a decoy could go has been
    replaced with a real `ast` + `tokenize` pass. That makes it handle all valid
    Python (multi-line literals with/without trailing commas, dict/set/comprehension
    literals, triple-quoted strings, f-strings, `#` inside strings, backslash
    continuations, decorators, else/elif/except/finally, match/case, semicolons,
    docstrings, __future__ imports, ...), and it now also emits decoy *classes*, not
    just decoy functions.

    Drop-in: same signature as the original plus an optional `seed=`.
    Deterministic by default (same input -> same output); pass `seed=<int>` for a
    different-but-reproducible result.
    """

    import ast
    import tokenize
    import io
    import re
    import keyword
    import builtins
    import random


    # match-statement pattern node types (absent on Python < 3.10) -> isinstance-safe.
    _MATCH_AS = getattr(ast, 'MatchAs', ())
    _MATCH_STAR = getattr(ast, 'MatchStar', ())
    _MATCH_MAPPING = getattr(ast, 'MatchMapping', ())

    # Calls that observe a scope's namespace; injecting decoys into such a scope
    # would change what they return, so we never inject there.
    _INTROSPECT_CALLS = {'locals', 'globals', 'vars', 'dir'}

    _ELIF_RE = re.compile(r'elif\b')

    # "Zero cores": integer expressions that are GENUINELY 0 for every int v (so any
    # dead code behind them never executes -> behavior preserved), but each requires a
    # number-theoretic fact to fold. opaque_cond() composes these with 0-preserving
    # operations (0*x, 0&x, 0+0, 0|0) over several fresh vars, so the resulting
    # predicates span a huge structural space and CANNOT be recognized by a fixed
    # template matcher (unlike a small fixed set). Validated for all ints; {v} is a
    # fresh int-literal decoy var.
    # Families of expressions that are GENUINELY 0 for every integer value of the
    # vars, drawn from a WIDE, non-fixed space so no small fixed-modulus regex
    # (`% (2|6|12|24|30|42)|& 1`) can recognize -- and strip -- the dead code.
    # Cheap families (multiple-of-k / parity / bitwise) dominate so the guards stay
    # fast on the obfuscated program's hot path; Fermat adds prime moduli and the
    # consecutive-product family adds factorial moduli, spreading `%` literals over
    # dozens of values. Every form holds for negatives, 0, and huge ints
    # (validated exhaustively by opaque_proof.py). See _zero_core below.
    _OPAQUE_PRIMES = [5, 7, 11, 13, 17]                   # Fermat: (b**p - b) % p == 0 for all int b
    _CONSEC_FACT = {2: 2, 3: 6, 4: 24, 5: 120, 6: 720}    # product of m consecutive ints divisible by m!
    _PARITY_CORES = [
        '({v}*{v} + {v}) % 2', '({v}*{v} - {v}) % 2',
        '({v}*({v} + 1)) % 2', '({v}*({v} - 1)) % 2',
        '({v}*{v}*{v} - {v}) % 6', '({v}*({v} + 1)*({v} - 1)) % 6',
        '({v}*{v}*{v}*{v} - {v}*{v}) % 12',
        '({v}*{v}*{v}*{v}*{v} - {v}) % 30',
    ]
    _BIT_CORES = [                                        # no `%` literal at all -> breaks the "% is always there" heuristic
        '(({v} & 1) * (({v} + 1) & 1))',                  # consecutive low bits -> one is 0
        '(({v} & 1) & ((~{v}) & 1))',                     # a bit AND its complement -> 0
        '(({v} | 0) - {v})',                              # x|0 == x  -> 0  (looks like real bit-or)
        '(({v} & {v}) - {v})',                            # x&x == x  -> 0
    ]


    # Mixed Boolean-Arithmetic (MBA) identities that equal 0 for EVERY integer value
    # of the vars -- valid over Python's unbounded two's-complement ints (verified for
    # negatives/0/huge by opaque_proof.py). Deeply nested, these are provably constant
    # but blow up general symbolic simplifiers/SMT solvers, so the static "prove this
    # is dead / prove this cancels, then strip it" step becomes computationally brutal.
    # The 2-var carry identities are the hard ones; 1-var forms are cheap fallbacks.
    _MBA_ZERO_2 = [
        '(({x} + {y}) - ({x} ^ {y}) - 2*({x} & {y}))',     # carry identity
        '(({x} | {y}) + ({x} & {y}) - {x} - {y})',
        '(({x} ^ {y}) - ({x} | {y}) + ({x} & {y}))',
        '(({x} + {y}) - ({x} | {y}) - ({x} & {y}))',
    ]
    _MBA_ZERO_1 = [
        '((~{x} + 1) + {x})',                              # -x + x
        '(({x} ^ {x}))',
        '(({x} | {x}) - {x})',
        '(({x} & {x}) - {x})',
        '(({x} ^ 0) - {x})',
    ]


    def _mba_zero(rng, vnames, number_pool, depth=None):
        """A Mixed Boolean-Arithmetic expression string that is 0 for every integer
        assignment of the vars. Nested to `depth` so simplifying it is expensive."""
        if depth is None:
            depth = rng.randint(1, 3)
        x = rng.choice(vnames)
        if len(vnames) >= 2 and rng.random() < 0.75:
            y = rng.choice([v for v in vnames if v != x] or vnames)
            e = rng.choice(_MBA_ZERO_2).format(x=x, y=y)
        else:
            e = rng.choice(_MBA_ZERO_1).format(x=x)
        for _ in range(depth):                             # zero-preserving nesting: 0^0, 0+0, 0&k
            r = rng.random()
            if r < 0.5:
                e = '({e} ^ ({z}))'.format(e=e, z=_mba_zero(rng, vnames, number_pool, 0))
            elif r < 0.8:
                e = '({e} + ({z}))'.format(e=e, z=_mba_zero(rng, vnames, number_pool, 0))
            else:
                kv = rng.choice(number_pool)
                k = abs(int(kv)) if kv.lstrip('-').isdigit() else 255
                e = '(({e}) & {k})'.format(e=e, k=k)
        return e


    def _zero_core(rng, vnames, number_pool):
        """One expression string that is 0 for EVERY integer assignment of the vars,
        picked from families with a wide modulus spread. Pure/deterministic."""
        if rng.random() < 0.30:                            # deep MBA: the solver-hostile family
            return _mba_zero(rng, vnames, number_pool)
        v = rng.choice(vnames)
        r = rng.random()
        if r < 0.46:                                      # dominant + cheap: multiple-of-k mod k, ARBITRARY k
            ks = [n for n in number_pool if n.lstrip('-').isdigit() and abs(int(n)) >= 2]
            k = rng.choice(ks) if ks and rng.random() < 0.6 else str(rng.choice([50, 64, 97, 128, 251, 999]))
            k = str(abs(int(k)))
            x = '({v} % {b})'.format(v=v, b=rng.choice([50, 64, 97, 128]))
            return rng.choice([
                '(({k} * {x}) % {k})'.format(k=k, x=x),
                '(({x} * {k}) % {k})'.format(k=k, x=x),
                '(({k} * {x} + {k}) % {k})'.format(k=k, x=x),
                '(({k} + {k} * {x}) % {k})'.format(k=k, x=x),
            ])
        if r < 0.70:                                      # parity / low-degree polynomial (number-theoretic)
            return _PARITY_CORES[rng.randrange(len(_PARITY_CORES))].format(v=v)
        if r < 0.82:                                      # Fermat little theorem, PRIME modulus
            p = rng.choice(_OPAQUE_PRIMES)
            return '(({v} % {p})**{p} - ({v} % {p})) % {p}'.format(v=v, p=p)
        if r < 0.92:                                      # consecutive product, FACTORIAL modulus
            m = rng.choice(list(_CONSEC_FACT))
            b = '({v} % {r})'.format(v=v, r=rng.choice([13, 17, 19, 23, 29]))
            terms = '*'.join('({b} + {i})'.format(b=b, i=i) if i else b for i in range(m))
            return '(({t}) % {f})'.format(t=terms, f=_CONSEC_FACT[m])
        return _BIT_CORES[rng.randrange(len(_BIT_CORES))].format(v=v)      # bitwise, breaks "% is always there"


    def _opaque_guard(rng, vnames, number_pool, truth):
        """Build an opaque predicate string over the already-assigned int vars `vnames`.
        Genuinely constant at runtime (falsy if truth=False, truthy if truth=True) but
        drawn from a large compositional space. Pure/deterministic; unit-tested directly."""
        core = _zero_core(rng, vnames, number_pool)                     # == 0 at runtime
        for _ in range(rng.randint(0, 2)):
            r = rng.random()
            if r < 0.4:                                                 # 0 + 0, 0 | 0, 0 ^ 0
                core = f"({core}) {rng.choice(['+', '|', '^'])} ({_zero_core(rng, vnames, number_pool)})"
            elif r < 0.7:                                               # 0 * junk
                core = f"(({core}) * ({rng.choice(vnames)} {rng.choice(['+', '-', '*'])} {rng.choice(number_pool)}))"
            else:                                                       # 0 & junk
                core = f"(({core}) & ({rng.choice(vnames)} {rng.choice(['+', '-'])} {rng.choice(number_pool)}))"
        if not truth:
            return f"({core})"
        f = rng.random()
        if f < 0.3:
            return f"(({core}) == 0)"
        if f < 0.55:
            return f"(not ({core}))"
        if f < 0.8:
            return f"(({core}) + 1)"
        return f"(({core}) | 1)"


    # A generic vocabulary of natural-looking identifier words. Decoy names are
    # built from the program's own harvested identifiers PLUS this list, so names
    # look real even for tiny inputs and never degenerate into `var_var_var...`.
    _VOCAB = [
        'data', 'value', 'result', 'tmp', 'temp', 'item', 'items', 'index', 'count',
        'total', 'buffer', 'node', 'state', 'config', 'params', 'cache', 'queue',
        'stack', 'offset', 'length', 'size', 'flag', 'token', 'chunk', 'batch',
        'target', 'source', 'output', 'payload', 'handler', 'context', 'factor',
        'ratio', 'delta', 'acc', 'cursor', 'record', 'entry', 'element', 'content',
        'status', 'mode', 'level', 'depth', 'width', 'height', 'start', 'limit',
        'bound', 'scale', 'weight', 'score', 'frame', 'segment', 'matrix', 'vector',
        'window', 'sample', 'metric', 'bucket', 'field', 'row', 'col', 'cell',
    ]

    _DEFAULT_SEED = 0.26900750624933856  # original hard-coded seed; deterministic default


    def _leading_ws(line):
        return line[:len(line) - len(line.lstrip())]


    def _is_docstring(stmt):
        return (isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str))


    def _is_future_import(stmt):
        return isinstance(stmt, ast.ImportFrom) and stmt.module == '__future__'


    # Statements we must NOT re-nest (move into an injected wrapper):
    #   compound stmts -> their own suite would have to move too (skip; we re-nest
    #     only self-contained simple statements);
    #   break/continue -> would rebind to an injected loop instead of the real one;
    #   global/nonlocal -> declarations, keep at their scope;
    #   __future__ -> must stay at module top.
    _COMPOUND_STMT = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.AsyncFor,
                      ast.While, ast.If, ast.With, ast.AsyncWith, ast.Try)
    _COMPOUND_STMT += tuple(t for t in (getattr(ast, 'TryStar', None), getattr(ast, 'Match', None)) if t)
    _NOWRAP_STMT = (ast.Break, ast.Continue, ast.Global, ast.Nonlocal)


    def _wrappable(stmt):
        """True if `stmt` is a self-contained simple statement we can move verbatim into
        an injected always-true wrapper without changing behavior (order/scope preserved)."""
        return (not isinstance(stmt, _COMPOUND_STMT)
                and not isinstance(stmt, _NOWRAP_STMT)
                and not _is_future_import(stmt))


    def _eff_start_line(stmt):
        """First physical line of a statement, accounting for decorators."""
        lo = stmt.lineno
        for d in getattr(stmt, 'decorator_list', []) or []:
            lo = min(lo, d.lineno)
        return lo


    def _harvest(tree):
        """Collect real identifiers, int literals, and word-ish strings from the AST."""
        names = set()
        ints = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.keyword) and node.arg:
                names.add(node.arg)
            elif isinstance(node, ast.alias):
                names.add((node.asname or node.name).split('.')[0])
            elif isinstance(node, ast.ExceptHandler):
                if node.name:
                    names.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                names.update(node.names)
            elif _MATCH_AS and isinstance(node, _MATCH_AS):
                if node.name:
                    names.add(node.name)
            elif _MATCH_STAR and isinstance(node, _MATCH_STAR):
                if node.name:
                    names.add(node.name)
            elif _MATCH_MAPPING and isinstance(node, _MATCH_MAPPING):
                if node.rest:
                    names.add(node.rest)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, bool):
                    continue
                if isinstance(node.value, int):
                    if 0 <= node.value < 10 ** 9:
                        ints.add(str(node.value))
        return names, ints


    _BINOP_SYM = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.FloorDiv: '//',
                  ast.Mod: '%', ast.Pow: '**', ast.BitXor: '^', ast.BitAnd: '&', ast.BitOr: '|',
                  ast.LShift: '<<', ast.RShift: '>>'}
    _CMP_SYM = {ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>',
                ast.GtE: '>=', ast.Is: 'is', ast.IsNot: 'is not', ast.In: 'in', ast.NotIn: 'not in'}


    def _harvest_constructs(tree):
        """Extract the *grammar* the source actually uses -- which builtins/functions
        it calls, which methods it invokes, which operators/comparisons/slices/
        comprehensions/imports appear -- so decoys can reproduce those same constructs
        and shape-based grepping can no longer isolate the real lines."""
        calls, methods, binops, cmpops, imports = set(), set(), set(), set(), set()
        slice_ = subscript = comp = unpack_for = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    methods.add(node.func.attr)
            elif isinstance(node, ast.BinOp):
                binops.add(_BINOP_SYM.get(type(node.op)))
            elif isinstance(node, ast.AugAssign):
                binops.add(_BINOP_SYM.get(type(node.op)))
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    cmpops.add(_CMP_SYM.get(type(op)))
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Slice):
                    slice_ = True
                else:
                    subscript = True
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                comp = True
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                if isinstance(node.target, (ast.Tuple, ast.List)):
                    unpack_for = True
            elif isinstance(node, ast.Import):
                for a in node.names:
                    imports.add(a.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    imports.add(node.module.split('.')[0])
        imports.discard('__future__')  # future imports must be first + use real feature names
        binops.discard(None); cmpops.discard(None)
        return {'calls': sorted(calls), 'methods': sorted(methods), 'binops': sorted(binops),
                'cmpops': sorted(cmpops), 'imports': sorted(imports),
                'slice': slice_, 'subscript': subscript, 'comp': comp, 'unpack_for': unpack_for}


    def _scope_introspects(scope):
        """True if `scope`'s own code calls locals()/globals()/vars()/dir() (i.e.
        observes its namespace). Does not descend into nested scopes."""
        found = [False]

        def walk(n, top):
            if found[0]:
                return
            if not top and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.ClassDef, ast.Lambda)):
                return
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in _INTROSPECT_CALLS):
                found[0] = True
                return
            for ch in ast.iter_child_nodes(n):
                walk(ch, False)

        walk(scope, True)
        return found[0]


    def _assigned_names(target):
        """Names bound by an assignment target (recursing tuple/list/starred)."""
        out = []
        if isinstance(target, ast.Name):
            out.append(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                out.extend(_assigned_names(e))
        elif isinstance(target, ast.Starred):
            out.extend(_assigned_names(target.value))
        return out


    def _scope_bindings(scope):
        """(name, bind_line) for parameters + top-level simple assignments in `scope`.
        These names are definitely bound and genuinely local, so they're the only ones
        safe to entangle (reassign to themselves). Names declared global/nonlocal are
        excluded to avoid changing a name's scope."""
        binds = []
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = scope.args
            for arg in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs):
                binds.append((arg.arg, -1))
            if a.vararg:
                binds.append((a.vararg.arg, -1))
            if a.kwarg:
                binds.append((a.kwarg.arg, -1))
        declared = set()
        for st in scope.body:
            if isinstance(st, (ast.Global, ast.Nonlocal)):
                declared.update(st.names)
        # A `del name` unbinds it, so reassigning it later (entanglement) would read a
        # deleted name -> NameError. Exclude any name deleted anywhere in the scope.
        for node in ast.walk(scope):
            if isinstance(node, ast.Delete):
                for t in node.targets:
                    declared.update(_assigned_names(t))  # only Name targets yield names
        for st in scope.body:
            targets = []
            if isinstance(st, ast.Assign):
                targets = st.targets
            elif isinstance(st, ast.AnnAssign) and st.value is not None:
                targets = [st.target]
            for t in targets:
                for nm in _assigned_names(t):
                    if nm not in declared:
                        binds.append((nm, getattr(st, 'end_lineno', st.lineno)))
        return binds


    src = python_code_string
    dno_sig = do_not_obfuscate_indent_block_comment

    # Parse up front. This both validates the input and gives us the real
    # statement structure used for safe decoy placement.
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise ValueError(f"obfuscate_python: input is not valid Python "
                         f"(line {e.lineno}: {e.msg}). Fix the source first.") from e

    lines = src.split('\n')

    # ---- DNO detection (on ORIGINAL lines, before comments are stripped) ----
    dno_line_nums = {i + 1 for i, ln in enumerate(lines)
                     if ln.rstrip().endswith(dno_sig)}

    # All statement spans (start incl. decorators, end inclusive).
    stmt_spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            stmt_spans.append((_eff_start_line(node),
                               getattr(node, 'end_lineno', node.lineno)))

    dno_protected = set()
    for d in dno_line_nums:
        containing = [(s, e) for (s, e) in stmt_spans if s <= d <= e]
        if containing:
            # marker on/inside a statement -> protect that whole statement + block
            s, e = min(containing, key=lambda se: se[1] - se[0])  # innermost
            dno_protected.update(range(s, e + 1))
        else:
            # marker on its own comment line -> protect the next statement + block
            following = [(s, e) for (s, e) in stmt_spans if s > d]
            if following:
                nxt = min(s for s, e in following)
                s, e = max((se for se in following if se[0] == nxt),
                           key=lambda se: se[1] - se[0])  # outermost at that line
                dno_protected.update(range(s, e + 1))
            else:
                dno_protected.add(d)

    # ---- comment / print stripping (string-aware) ----
    if remove_comments:
        try:
            toks = tokenize.generate_tokens(io.StringIO(src).readline)
            comment_cols = {}  # row -> col of comment start
            for tok in toks:
                if tok.type == tokenize.COMMENT:
                    row, col = tok.start
                    # keep the earliest comment col on a line (there is only one)
                    comment_cols.setdefault(row, col)
        except tokenize.TokenError:
            comment_cols = {}
        for row, col in comment_cols.items():
            lines[row - 1] = lines[row - 1][:col].rstrip()

    if remove_prints:
        for node in ast.walk(tree):
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == 'print'):
                ln, end = node.lineno, node.end_lineno
                first = lines[ln - 1]
                ws = _leading_ws(first)
                # Only replace if the print occupies its physical lines alone
                # (col == indent, and nothing trailing after the call) so we
                # never clobber a sibling like `x = 1; print(2)`.
                if node.col_offset != len(ws):
                    continue
                tail = lines[end - 1][node.value.end_col_offset:]
                if tail.strip() not in ('', dno_sig):
                    continue
                lines[ln - 1] = ws + 'pass'
                for k in range(ln, end):
                    lines[k] = ''

    if not add_lines:
        return '\n'.join(lines)

    # ---- gather reserved names + decoy material ----
    reserved = set(keyword.kwlist)
    reserved.update(dir(builtins))
    reserved.update(['match', 'case', 'type', '_'])  # soft keywords
    reserved.update([n for n in dir(object) if n.startswith('__') and n.endswith('__')])

    real_names, int_pool = _harvest(tree)

    # NOTE: sorted() is load-bearing -- building this from a set leaves iteration
    # order at the mercy of PYTHONHASHSEED, which would make rng.choice() (and
    # thus the whole output) differ between processes despite the fixed seed.
    name_pool = sorted(t for t in (real_names | set(_VOCAB))
                       if t.isidentifier() and not t.startswith('__') and t not in reserved)
    if not name_pool:
        name_pool = sorted(_VOCAB)
    word_pool = list(name_pool)  # for plausible string contents

    # Real string LITERALS from the source. Scattering verbatim copies of these as
    # decoys defeats the "grep the one distinctive status string" anchor -- the real
    # string now appears many times, so content no longer isolates it. Also used as
    # style templates so decoy strings match the program's own string distribution.
    real_strings = sorted({n.value for n in ast.walk(tree)
                           if isinstance(n, ast.Constant) and isinstance(n.value, str)
                           and 0 < len(n.value) <= 120})

    # First module-level statement index (after docstring + __future__): where we
    # inject the runtime-varying honeypot counter so it's bound before any real code.
    _pb = tree.body
    _psi = 0
    if _pb and _is_docstring(_pb[0]):
        _psi = 1
    while _psi < len(_pb) and _is_future_import(_pb[_psi]):
        _psi += 1
    _prepend_idx = (_pb[_psi].lineno - 1) if _psi < len(_pb) else len(lines)

    # real identifiers, safe to *reference* from dead (never-executed) decoy code,
    # so the decoy data-flow graph isn't a disconnected island a slicer can isolate.
    # Exclude global/nonlocal-declared names: referencing one inside its function
    # before that function's `global`/`nonlocal` line is a "used prior to
    # declaration" SyntaxError.
    _global_declared = set()
    for _n in ast.walk(tree):
        if isinstance(_n, (ast.Global, ast.Nonlocal)):
            _global_declared.update(_n.names)
    real_names_list = sorted(n for n in real_names
                             if n.isidentifier() and n not in reserved and n not in _global_declared)

    number_pool = sorted(int_pool, key=lambda s: (len(s), s))
    if not number_pool:
        number_pool = ['0', '1', '2', '3', '7', '10', '16', '32', '64', '100', '255', '1000']

    feats = _harvest_constructs(tree)  # the grammar the source uses, for decoys to mimic

    rng = random.Random(_DEFAULT_SEED if seed is None else seed)

    # ---- indent unit (match the file's style: tabs vs spaces) ----
    sample_indents = [_leading_ws(ln) for ln in lines if ln[:1] in (' ', '\t')]
    indent_unit = '\t' if any('\t' in s for s in sample_indents) else '    '

    # ---- decoy name pool: precomputed ONCE, so minting a name is an O(1)
    # rng.choice with no per-call uniqueness loop (the old loop degraded to O(N^2)
    # as the name space filled). Names can never collide with a real identifier or
    # reserved word, so a decoy can't shadow real code; repeats between decoys are
    # fine (every use is an assignment target or a dead reference). name_pool is
    # sorted -> deterministic order -> deterministic across processes.
    def _build_name_pool(cap=16000):
        pool, seen = [], set()

        def add(nm):
            if (nm and nm not in seen and nm not in real_names and nm not in reserved
                    and not nm[0].isdigit() and nm.isidentifier()):
                seen.add(nm); pool.append(nm)

        for w in name_pool:
            add(w)
        for a in name_pool:
            for b in name_pool:
                add(a + '_' + b)
                if len(pool) >= cap:
                    return pool
        d = 0
        while len(pool) < cap:
            for w in name_pool:
                add(w + str(d))
            d += 1
            if d > cap:            # name_pool tiny -> stop; what we have is enough
                break
        return pool or ['_v0']

    _NAME_POOL = _build_name_pool()

    def create_var_name():
        return rng.choice(_NAME_POOL)

    def create_var_names(k):        # k DISTINCT names, for param / member lists
        if k <= 0:
            return []
        if k >= len(_NAME_POOL):
            return [rng.choice(_NAME_POOL) for _ in range(k)]
        return rng.sample(_NAME_POOL, k)

    def pick(seq, fallback):
        return rng.choice(seq) if seq else fallback

    _HEXD = '0123456789abcdef'

    def _rand_hex(n):
        return ''.join(rng.choice(_HEXD) for _ in range(n))

    def _flag_literal():
        inner = '_'.join(rng.choice(word_pool) if rng.random() < 0.5 else _rand_hex(rng.randint(2, 6))
                         for _ in range(rng.randint(1, 3)))
        tag = rng.choice(['X', 'FLAG', 'CTF', 'KEY', 'TOKEN', rng.choice(word_pool).upper()])
        return repr('{}{{{}}}'.format(tag, inner))

    def make_rich_string():
        # A feature-bearing decoy string LITERAL: colons, braces, hex, no-spaces, or
        # a verbatim copy of a REAL source string. Kills the cheap static anchors
        # (`grep ':'`, `grep '{'`, hex-grep, "the one distinctive string") by making
        # every one of those return a swamp. Returns a valid Python str literal.
        r = rng.random()
        if real_strings and r < 0.22:
            return repr(rng.choice(real_strings))          # verbatim real string -> anchor defeat
        if r < 0.40:                                       # flag-shaped  TAG{...}
            return _flag_literal()
        if r < 0.58:                                       # hash / hex-digest shaped
            return repr(_rand_hex(rng.choice([16, 32, 40, 64])))
        if r < 0.72:                                       # key: value (colon)
            return repr('{}: {}'.format(rng.choice(word_pool), rng.choice(word_pool)))
        if r < 0.85:                                       # no-space token / snake / path
            parts = [rng.choice(word_pool) for _ in range(rng.randint(2, 3))]
            sep = rng.choice(['_', '-', '.', '/', ':', ''])
            return repr(sep.join(parts) + (('_' + _rand_hex(4)) if rng.random() < 0.5 else ''))
        parts = [rng.choice(word_pool) for _ in range(rng.randint(2, 3))]   # camelCase-ish
        return repr(parts[0] + ''.join(p.capitalize() for p in parts[1:]))

    def make_string():
        if rng.random() < 0.5:
            return make_rich_string()
        parts = [rng.choice(word_pool) for _ in range(rng.randint(1, 4))]
        q = rng.choice(["'", '"'])
        return q + ' '.join(parts) + q

    def make_list(vrs, will_run):
        elems = []
        kinds = [1, 2] if will_run else [1, 2, 3]  # 3 = reference an existing decoy var
        while rng.random() > 1 / 6:
            k = rng.choice(kinds)
            if k == 1:
                elems.append(make_string())
            elif k == 2:
                elems.append(rng.choice(number_pool))
            else:
                elems.append(pick(vrs['all'], rng.choice(number_pool)))
        return '[' + ', '.join(elems) + ']'

    # ---- generation context ----
    ratio = max(0.0, float(new_line_ratio))  # decoy lines added per real code line
    R = max(1.0, ratio)                       # safe floor for probability denominators
    MAX_DEPTH = 2

    class Ctx:
        __slots__ = ('indent', 'out', 'depth', 'entangle', 'in_func')

        def __init__(self, indent, entangle_names=(), in_func=False):
            self.indent = indent
            self.out = []
            self.depth = 0
            self.entangle = entangle_names  # real locals safe to reassign at this point
            self.in_func = in_func          # True if this point is inside a function body

    # Shared decoy-var registry. BOUNDED to a sliding window (a decoy referencing
    # one of the last ~hundreds of decoy vars is as good as one of hundreds of
    # thousands) -- keeping these lists from growing unboundedly is what turns the
    # whole generator from O(N^2) back into O(N).
    vrs = {'all': [], 'num': [], 'str': [], 'lst': [], 'fun': [], 'cls': []}
    _VRS_CAP = 800

    def _push(key, v):
        lst = vrs[key]
        lst.append(v)
        if len(lst) > _VRS_CAP:
            del lst[:_VRS_CAP // 2]   # sliding window; amortized O(1) per push

    def emit(ctx, text):
        ctx.out.append(ctx.indent + text)

    def gen_num_var(ctx):
        if vrs['num'] and rng.random() < 1 / 4:
            return rng.choice(vrs['num'])
        v = create_var_name()
        _push('num', v); _push('all', v)
        return v

    def _reuse_nonnum():
        s, l = vrs['str'], vrs['lst']
        if s and l:
            return rng.choice(s if rng.random() < 0.5 else l)
        return rng.choice(s or l)

    def gen_str_var(ctx):
        if (vrs['str'] or vrs['lst']) and rng.random() < 1 / 4:
            return _reuse_nonnum()
        v = create_var_name()
        _push('str', v); _push('all', v)
        return v

    def gen_lst_var(ctx):
        if (vrs['str'] or vrs['lst']) and rng.random() < 1 / 4:
            return _reuse_nonnum()
        v = create_var_name()
        _push('lst', v); _push('all', v)
        return v

    def gen_other_var():
        v = create_var_name()
        _push('all', v)
        return v

    def opaque_cond(ctx, truth):
        # Mint 1-3 fresh int vars, then build a parametric opaque predicate over
        # them (see module-level _opaque_guard, which is unit-tested directly).
        vs = []
        for _ in range(rng.randint(1, 3)):
            v = create_var_name()
            emit(ctx, f"{v} = {rng.choice(number_pool)}")
            vs.append(v)
        return _opaque_guard(rng, vs, number_pool, truth)

    def dead_ref():
        # Operand usable ONLY in dead code: may be a real identifier (the line
        # never executes, so referencing an out-of-scope/real name is harmless),
        # which entangles the decoy graph with the real one.
        r = rng.random()
        if r < 0.5 and vrs['all']:
            return rng.choice(vrs['all'])
        if r < 0.75 and real_names_list:
            return rng.choice(real_names_list)
        return rng.choice(number_pool)

    def dead_name():
        # like dead_ref but NEVER a bare number, so it's valid as a method
        # receiver (`2.method()` is a parse error; `name.method()` is not).
        if vrs['all'] and (not real_names_list or rng.random() < 0.6):
            return rng.choice(vrs['all'])
        if real_names_list:
            return rng.choice(real_names_list)
        return rng.choice(vrs['all']) if vrs['all'] else create_var_name()

    # ---- decoy statement generators -------------------------------------
    def rand_num(ctx, will_run=True):
        v = gen_num_var(ctx)
        emit(ctx, f"{v} = {rng.choice(number_pool)}")
        return v

    def rand_num_add(ctx, will_run=True):
        v = gen_num_var(ctx)
        a = int(rng.choice(number_pool)); b = int(rng.choice(number_pool))
        op = rng.choice(['+', '-', '*'])
        emit(ctx, f"{v} = {a} {op} {b}")
        return v

    def rand_var_add(ctx, will_run=False):  # dead only
        v = gen_num_var(ctx)
        a = dead_ref() if rng.random() < 1 / 2 else rng.choice(number_pool)
        b = dead_ref() if rng.random() < 1 / 2 else rng.choice(number_pool)
        op = rng.choice(['+', '-', '/', '//', '%', '*', '**'])
        emit(ctx, f"{v} = {a} {op} {b}")
        return v

    def rand_str(ctx, will_run=True):
        v = gen_str_var(ctx)
        emit(ctx, f"{v} = {make_string()}")
        return v

    def rand_lst(ctx, will_run=True):
        v = gen_lst_var(ctx)
        emit(ctx, f"{v} = {make_list(vrs, will_run)}")
        return v

    def rand_var(ctx, will_run=False):  # dead only
        ev = dead_ref()
        if ev in vrs['num']:
            v = gen_num_var(ctx)
        elif ev in vrs['str']:
            v = gen_str_var(ctx)
        elif ev in vrs['lst']:
            v = gen_lst_var(ctx)
        else:
            v = gen_other_var()
        emit(ctx, f"{v} = {ev}")
        return v

    def rand_print(ctx, will_run=False):  # dead only
        c = rng.randint(1, 4)
        if c == 1:
            ev = dead_ref()
        elif c == 2:
            ev = make_string()
        elif c == 3:
            ev = rng.choice(number_pool)
        else:
            ev = make_list(vrs, False)
        emit(ctx, f"print({ev})")

    def add_pass(ctx, will_run=True):
        emit(ctx, "pass")

    def rand_comprehension(ctx, will_run=True):
        v = gen_lst_var(ctx)
        it = create_var_name()  # comprehension-local loop var
        body = rng.choice([it, f"{it} * {rng.choice(number_pool)}",
                           f"{it} + {rng.choice(number_pool)}", make_string()])
        emit(ctx, f"{v} = [{body} for {it} in range(0, {rng.randint(2, 6)})]")
        return v

    def rand_ternary(ctx, will_run=True):
        v = gen_num_var(ctx)
        cond = opaque_cond(ctx, truth=bool(rng.randint(0, 1)))
        emit(ctx, f"{v} = {rng.choice(number_pool)} if {cond} else {rng.choice(number_pool)}")
        return v

    def rand_dict(ctx, will_run=True):
        v = gen_lst_var(ctx)
        items = ', '.join(f"{make_string()}: {rng.choice(number_pool)}"
                          for _ in range(rng.randint(1, 3)))
        emit(ctx, f"{v} = {{{items}}}")
        return v

    def rand_fstring(ctx, will_run=True):
        v = gen_str_var(ctx)
        w1 = rng.choice(word_pool); w2 = rng.choice(word_pool)
        emit(ctx, f'{v} = f"{w1} {{{rng.choice(number_pool)}}} {w2}"')
        return v

    def rand_tuple(ctx, will_run=True):
        a, b = create_var_names(2)
        _push('all', a); _push('all', b)
        emit(ctx, f"{a}, {b} = {rng.choice(number_pool)}, {make_string()}")
        return a

    def dead_expr():
        # A larger expression referencing several decoy/real names. Only ever placed
        # in a never-taken branch (so it can reference anything and can't error),
        # its job is to drag many decoy vars into a real var's backward slice.
        parts = [dead_ref()]
        for _ in range(rng.randint(1, 3)):
            parts.append(f"{rng.choice(_binops)} {dead_ref()}")
        return ' '.join(parts)

    def _noop_rebind(ctx, tgt):
        # rebind tgt to ITSELF (no-op for ANY type) with a decoy woven into the
        # never-taken branch, so tgt's backward slice can't shed the decoy. The
        # opaque guard is often deep MBA, so pruning the branch needs a solver;
        # shape 4 drags a WIDE cone of decoy+real refs into tgt's slice.
        shape = rng.randint(0, 4)
        if shape == 0:
            emit(ctx, f"{tgt} = {tgt} if {opaque_cond(ctx, True)} else {dead_expr()}")
        elif shape == 1:
            emit(ctx, f"{tgt} = {dead_expr()} if {opaque_cond(ctx, False)} else {tgt}")
        elif shape == 2:
            emit(ctx, f"{tgt} = ({tgt}, {rich_expr_safe()})[{opaque_cond(ctx, False)}]")
        elif shape == 3:
            emit(ctx, f"{tgt} = {{0: {tgt}, 1: {rich_expr_safe()}}}[{opaque_cond(ctx, False)}]")
        else:
            cone = ' '.join([dead_ref()] + [f"{rng.choice(_binops)} {dead_ref()}"
                                            for _ in range(rng.randint(4, 8))])
            emit(ctx, f"{tgt} = {tgt} if {opaque_cond(ctx, True)} else ({cone})")

    def rand_entangle(ctx, will_run=True):
        # Tangle real and decoy data flow so a backward slice from the output can't
        # separate them. Three modes, all runtime no-ops for the real values:
        #   backward: a real var rebinds to itself, decoy pulled into its slice
        #   forward:  a real var's VALUE flows into a fresh decoy var
        #   hide:     a decoy var gets the same shape, so the pattern doesn't leak
        #             which vars are real.
        real = ctx.entangle
        m = rng.random()
        if real and m < 0.4:
            _noop_rebind(ctx, rng.choice(real))
        elif real and m < 0.65:
            dv = gen_other_var()
            emit(ctx, f"{dv} = ({rng.choice(real)}, {rich_expr_safe()})[{opaque_cond(ctx, False)}]")
        else:
            tgt = gen_other_var()
            emit(ctx, f"{tgt} = {rich_expr_safe()}")
            _noop_rebind(ctx, tgt)
        return None

    def rand_dead_block(ctx, will_run=True):
        # An opaque-dead loop: the guard is genuinely falsy at runtime (body never
        # runs -> behavior safe) but isn't statically foldable, so a DCE pass can't
        # remove the decoys inside it.
        if ctx.depth >= MAX_DEPTH:
            return add_random_line(ctx, will_run)
        cond = opaque_cond(ctx, truth=False)
        if rng.random() < 1 / 2:
            emit(ctx, f"while {cond}:")
        else:
            emit(ctx, f"for {gen_other_var()} in range(0, {cond}):")
        ctx.indent += indent_unit
        ctx.depth += 1
        for _ in range(rng.randint(1, 2)):  # dead body, kept short
            add_random_line(ctx, will_run=False)
        ctx.depth -= 1
        ctx.indent = ctx.indent[:-len(indent_unit)]

    def _fake_flag_expr():
        # A fake flag-shaped value built via the harvested primitives (never a
        # literal), so a dynamic tap on chr()/bytes() sees plausible candidates
        # mixed in with the real secret. Uses only builtins -> always safe to run.
        forms = ['literal']                                 # always available (a flag-shaped str literal)
        if 'chr' in _calls:
            forms.append('chr')
        if 'bytes' in _calls or 'bytearray' in _calls:
            forms.append('bytes')
        pick = rng.choice(forms) if len(forms) == 1 else rng.choice(forms[1:] + ['literal'])
        if pick == 'chr':
            # FIX 2: mix a runtime-varying term into some chars so the chr() stream
            # differs every call/iteration (real char no longer the lone variant).
            def _cc():
                if rng.random() < 0.5:
                    return f'chr(65 + ({_vary()}) % 26)'
                return f'chr({rng.randint(48, 122)})'
            pre = ' + '.join(_cc() for _ in range(rng.randint(2, 4)))
            body = ' + '.join(_cc() for _ in range(rng.randint(6, 16)))
            return f"{pre} + chr(123) + {body} + chr(125)"   # X..X{...}
        if pick == 'bytes':
            return f"bytes([{', '.join(str(rng.randint(33, 126)) for _ in range(rng.randint(8, 24)))}])"
        return _flag_literal()

    def rand_honeypot(ctx, will_run=True):
        # LIVE fake-flag pipeline: build a flag-shaped value via the same primitives
        # the real secret uses, then push it through MORE real primitives (encode/
        # bytes/hash) and drop a fake hash constant beside it. So an attacker who
        # hooks a primitive to catch the flag catches a swamp of candidates, and one
        # who filters "candidate that passes a hash check" also gets many hits.
        e = _fake_flag_expr()
        if e is None:
            return rand_rich(ctx, will_run)
        v = gen_str_var(ctx)
        emit(ctx, f"{v} = {e}")
        # FIX 1: push the fake flag through the SAME crypto/encoding primitives the
        # real code uses (hashlib/hmac/base64/ord/...), so hooking the real primitive
        # returns a swamp, not one clean hit. Emit 1-2 such live decoy calls.
        for _ in range(rng.randint(1, 2)):
            if rng.random() < 0.8:
                emit(ctx, f"{gen_str_var(ctx)} = {rng.choice(_LIVE_PRIMS)(v)}")
        if rng.random() < 0.45:           # fake embedded hash constant nearby -> floods hash-greps
            emit(ctx, f"{gen_str_var(ctx)} = {repr(_rand_hex(rng.choice([32, 40, 64])))}")
        return v

    def _fake_if_else(ctx, levels):
        # if <opaque_false>: <dead>  else: (nested if/else, or live decoys). Nested
        # (not elif) so opaque_cond's setup lines sit safely inside the else block.
        emit(ctx, f"if {opaque_cond(ctx, False)}:")
        ctx.indent += indent_unit; ctx.depth += 1
        _emit_dead_construct(ctx)
        ctx.depth -= 1; ctx.indent = ctx.indent[:-len(indent_unit)]
        emit(ctx, "else:")
        ctx.indent += indent_unit; ctx.depth += 1
        if levels > 1 and ctx.depth < MAX_DEPTH:
            _fake_if_else(ctx, levels - 1)              # deeper -> multi-branch look
        else:
            for _ in range(rng.randint(1, 2)):
                add_random_line(ctx, will_run=True)     # the one branch that runs -> safe
        ctx.depth -= 1; ctx.indent = ctx.indent[:-len(indent_unit)]

    def rand_fake_flow(ctx, will_run=True):
        # Bogus but real-looking control flow, so real decision points drown among
        # fake ones. All branches that fire are behavior-safe.
        if ctx.depth >= MAX_DEPTH:
            return add_random_line(ctx, will_run)
        if ctx.in_func and rng.random() < 0.4:
            emit(ctx, f"if {opaque_cond(ctx, False)}:")     # dead guard clause, never returns
            ctx.indent += indent_unit
            emit(ctx, f"return {dead_expr()}")
            ctx.indent = ctx.indent[:-len(indent_unit)]
            return
        _fake_if_else(ctx, rng.randint(1, 2))

    def _params(n):
        return ', '.join(create_var_names(n))  # k distinct names (no dup params)

    def rand_func(ctx, will_run=True):
        if ctx.depth >= MAX_DEPTH:
            return add_random_line(ctx, will_run)
        name = create_var_name()
        _push('fun', name); _push('all', name)
        emit(ctx, f"def {name}({_params(rng.randint(0, 3))}):")
        ctx.indent += indent_unit
        ctx.depth += 1
        body_vars = []
        for _ in range(rng.randint(1, 3)):
            v = add_random_line(ctx, will_run=True)
            if v:
                body_vars.append(v)
        if body_vars and rng.random() < 2 / 3:
            ret = ', '.join(rng.choice(body_vars) for _ in range(rng.randint(1, 2)))
            emit(ctx, f"return {ret}")
        ctx.depth -= 1
        ctx.indent = ctx.indent[:-len(indent_unit)]
        return name

    def rand_class(ctx, will_run=True):
        if ctx.depth >= MAX_DEPTH:
            return add_random_line(ctx, will_run)
        name = create_var_name()
        _push('cls', name); _push('all', name)
        emit(ctx, f"class {name}:")
        ctx.indent += indent_unit
        ctx.depth += 1
        members = 0
        # class-level attributes (run at definition time -> must be safe literals)
        for _ in range(rng.randint(0, 3)):
            attr = create_var_name()
            kind = rng.randint(1, 3)
            if kind == 1:
                emit(ctx, f"{attr} = {rng.choice(number_pool)}")
            elif kind == 2:
                emit(ctx, f"{attr} = {make_string()}")
            else:
                emit(ctx, f"{attr} = {make_list(vrs, True)}")
            members += 1
        # decoy methods (defined, never called)
        for _ in range(rng.randint(1, 2)):
            mname = create_var_name()
            extra = _params(rng.randint(0, 2))
            sig = 'self' + (', ' + extra if extra else '')
            emit(ctx, f"def {mname}({sig}):")
            ctx.indent += indent_unit
            ctx.depth += 1
            mvars = []
            for _ in range(rng.randint(1, 2)):
                v = add_random_line(ctx, will_run=False)
                if v:
                    mvars.append(v)
            if mvars and rng.random() < 1 / 2:
                emit(ctx, f"return {rng.choice(mvars)}")
            ctx.depth -= 1
            ctx.indent = ctx.indent[:-len(indent_unit)]
            members += 1
        if members == 0:
            emit(ctx, "pass")
        ctx.depth -= 1
        ctx.indent = ctx.indent[:-len(indent_unit)]
        return name

    def rand_call_func(ctx, will_run=False):  # dead only
        if vrs['fun'] and (not real_names_list or rng.random() < 1 / 2):
            callee = rng.choice(vrs['fun'])
        elif real_names_list:
            callee = rng.choice(real_names_list)  # "call" real code (never executes)
        else:
            return add_random_line(ctx, will_run)
        args = ', '.join(dead_ref() for _ in range(rng.randint(0, 2)))
        emit(ctx, f"{callee}({args})")

    # ---- construct/grammar reproduction --------------------------------------
    # Decoys that use the SAME operations the source uses (its calls, methods,
    # operators, slices, subscripts, comprehensions, imports), so grepping for a
    # real construct (`ord(`, `.append(`, ` ^ `, `[::-1]`, `import X`) returns
    # thousands of decoy hits instead of isolating the ~6 real lines. Live variants
    # use ONLY literals (safe to execute); dead variants (inside opaque-false
    # blocks) use real names / arbitrary receivers -> never execute, can't error.
    _calls = feats['calls']
    _methods = feats['methods']
    _binops = feats['binops'] or ['+', '-', '*']
    _cmpops = feats['cmpops']
    _imports = feats['imports']

    # ---- FIX 1: primitive-coverage honeypots ----
    # Live decoy expressions that route a fake flag var through the SAME safe (pure,
    # side-effect-free) crypto/encoding primitives the real code uses, so an attacker
    # hooking hashlib/hmac/base64/ord catches a swamp of fakes, not one real hit.
    _hpc = create_var_name()   # module-level runtime-varying honeypot counter (a [int])
    _NAME_POOL[:] = [x for x in _NAME_POOL if x != _hpc]   # reserve it: no other decoy may reuse
    if not _NAME_POOL:
        _NAME_POOL.append('_v0')

    def _live_prim_forms():
        forms = [                                   # builtins: always bound, always safe
            lambda v: f"ord((str({v}) + 'x')[0])",
            lambda v: f"len(str({v}).encode())",
            lambda v: f"str({v}).encode().hex()",
            lambda v: f"hash(str({v}))",
        ]
        # Route through the SAME library primitives the real code imports, via
        # __import__('mod') -> position-safe (works even if emitted before the real
        # import line) and idempotent, and it returns the cached module object, so a
        # hook on `mod.func` still catches these decoy calls.
        for mod in _imports:
            if mod == 'hashlib':
                for fn in ('sha256', 'md5', 'sha1', 'sha512'):
                    forms.append(lambda v, f=fn: f"__import__('hashlib').{f}(str({v}).encode()).hexdigest()")
            elif mod == 'hmac':
                forms.append(lambda v: f"__import__('hmac').new(str({v}).encode(), str({v}).encode(), 'sha256').hexdigest()")
            elif mod == 'base64':
                forms.append(lambda v: f"__import__('base64').b64encode(str({v}).encode()).decode()")
            elif mod == 'binascii':
                forms.append(lambda v: f"__import__('binascii').hexlify(str({v}).encode()).decode()")
            elif mod == 'zlib':
                forms.append(lambda v: f"__import__('zlib').crc32(str({v}).encode())")
        return forms

    _LIVE_PRIMS = _live_prim_forms()

    def _vary():
        # a runtime-VARYING int expression (bumps the shared honeypot counter IN
        # PLACE, bounded), so honeypot values differ every call/iteration and the
        # real per-iteration datum is no longer the lone token that changes between
        # repeated blocks. __setitem__ returns None -> `or` yields the new value.
        return f"({_hpc}.__setitem__(0, ({_hpc}[0] + 1) & 8191) or {_hpc}[0])"

    def _charlit():
        return repr(chr(rng.randint(65, 90)))

    def _intlist(lo=1, hi=4):
        return '[' + ', '.join(rng.choice(number_pool) for _ in range(rng.randint(lo, hi))) + ']'

    def _bytelist():
        return '[' + ', '.join(str(rng.randint(0, 255)) for _ in range(rng.randint(1, 5))) + ']'

    def _strlist():
        return '[' + ', '.join(make_string() for _ in range(rng.randint(1, 3))) + ']'

    _SAFE_CALL = {
        'ord': _charlit, 'chr': (lambda: str(rng.randint(65, 122))),
        'len': make_string, 'int': (lambda: repr(rng.choice(number_pool))),
        'str': (lambda: rng.choice(number_pool)), 'hex': (lambda: rng.choice(number_pool)),
        'bin': (lambda: rng.choice(number_pool)), 'oct': (lambda: rng.choice(number_pool)),
        'abs': (lambda: '-' + rng.choice(number_pool)), 'bool': (lambda: rng.choice(number_pool)),
        'float': (lambda: rng.choice(number_pool)), 'bytes': _bytelist, 'bytearray': _bytelist,
        'sum': _intlist, 'min': _intlist, 'max': _intlist, 'sorted': _intlist,
        'list': _strlist, 'tuple': _intlist, 'set': _intlist, 'frozenset': _intlist,
        'repr': make_string, 'hash': (lambda: rng.choice(number_pool)),
        'reversed': _intlist, 'enumerate': _intlist, 'iter': _intlist,
    }
    _STR_SAFE_M = {'encode', 'split', 'rsplit', 'strip', 'lstrip', 'rstrip', 'upper', 'lower',
                   'title', 'capitalize', 'swapcase', 'isdigit', 'isalpha', 'isspace',
                   'startswith', 'endswith', 'count', 'find', 'rfind', 'replace', 'join',
                   'zfill', 'ljust', 'rjust', 'format'}
    _LIST_SAFE_M = {'append', 'count', 'copy', 'sort', 'reverse', 'clear', 'insert', 'extend', 'pop'}
    _BYTES_SAFE_M = {'hex', 'decode'}

    def _safe_method_expr(m):
        if m in _STR_SAFE_M:
            recv = make_string()
            if m == 'format':
                # receiver must be a BRACE-FREE template (rich strings carry `{...}`
                # which .format() would read as fields -> KeyError). Extra arg is ignored.
                plain = repr(' '.join(rng.choice(word_pool) for _ in range(rng.randint(1, 3))))
                return f"{plain}.format({make_string()})"
            if m == 'join':
                return f"{recv}.join({_strlist()})"
            if m in ('startswith', 'endswith', 'count', 'find', 'rfind'):
                return f"{recv}.{m}({make_string()})"
            if m == 'replace':
                return f"{recv}.replace({make_string()}, {make_string()})"
            if m in ('zfill', 'ljust', 'rjust'):
                return f"{recv}.{m}({rng.randint(1, 12)})"
            return f"{recv}.{m}()"
        if m in _LIST_SAFE_M:
            recv = _intlist(2, 4)
            if m == 'insert':
                return f"{recv}.insert(0, {rng.choice(number_pool)})"
            if m in ('append', 'count'):
                return f"{recv}.{m}({rng.choice(number_pool)})"
            if m == 'extend':
                return f"{recv}.extend({_intlist()})"
            return f"{recv}.{m}()"
        if m in _BYTES_SAFE_M:
            if m == 'decode':
                return f"bytes({_bytelist()}).decode('latin1')"  # never raises
            return f"bytes({_bytelist()}).hex()"
        return None

    def _safe_binop():
        op = rng.choice(_binops)
        if op in ('/', '//', '%'):
            return f"{rng.choice(number_pool)} {op} {rng.randint(1, 99)}"
        if op == '**':
            return f"{rng.randint(0, 12)} ** {rng.randint(0, 4)}"
        if op in ('<<', '>>'):
            return f"{rng.choice(number_pool)} {op} {rng.randint(0, 8)}"
        return f"{rng.choice(number_pool)} {op} {rng.choice(number_pool)}"

    def rich_expr_safe():
        opts = ['bin']
        if _calls: opts.append('call')
        if _methods: opts.append('meth')
        if _cmpops: opts.append('cmp')
        if feats['slice']: opts.append('slice')
        if feats['subscript']: opts.append('sub')
        if feats['comp']: opts.append('comp')
        kind = rng.choice(opts)
        if kind == 'call':
            safe = [c for c in _calls if c in _SAFE_CALL]
            if safe:
                c = rng.choice(safe)
                return f"{c}({_SAFE_CALL[c]()})"
        elif kind == 'meth':
            for _ in range(3):
                e = _safe_method_expr(rng.choice(_methods))
                if e:
                    return e
        elif kind == 'cmp':
            op = rng.choice(_cmpops)
            if op in ('in', 'not in'):
                return f"{make_string()} {op} {_strlist()}"
            if op in ('is', 'is not'):   # name receiver: `5 is None` warns, `len is None` doesn't
                return f"{rng.choice(['len', 'str', 'list', 'dict', 'type', 'object', 'set'])} {op} None"
            return f"{rng.choice(number_pool)} {op} {rng.choice(number_pool)}"
        elif kind == 'slice':
            recv = make_string() if rng.random() < 0.5 else _intlist(3, 6)
            return f"{recv}[{rng.choice(['::-1', '1:', '::2', ':3', '1:3'])}]"
        elif kind == 'sub':
            return f"{_intlist(2, 5)}[0]"
        elif kind == 'comp':
            it = create_var_name()  # ops safe for ANY operand (no %, //, / -> no div-by-zero)
            op = rng.choice([o for o in _binops if o in ('+', '-', '*', '^', '&', '|')] or ['+'])
            return f"[{it} {op} {rng.choice(number_pool)} for {it} in range(0, {rng.randint(2, 6)})]"
        return _safe_binop()

    def rand_rich(ctx, will_run=True):            # live: runs, literal operands only
        v = gen_other_var()
        emit(ctx, f"{v} = {rich_expr_safe()}")
        return v

    def _emit_dead_construct(ctx):
        r = rng.random()
        if _methods and r < 0.28:
            args = ', '.join(dead_ref() for _ in range(rng.randint(0, 2)))
            emit(ctx, f"{dead_name()}.{rng.choice(_methods)}({args})")
        elif _calls and r < 0.5:
            args = ', '.join(dead_ref() for _ in range(rng.randint(0, 2)))
            emit(ctx, f"{gen_other_var()} = {rng.choice(_calls)}({args})")
        elif feats['subscript'] and r < 0.62:
            emit(ctx, f"{gen_other_var()} = {dead_name()}[{dead_ref()}]")  # name receiver: no int-subscript warning
        elif feats['unpack_for'] and r < 0.74 and ctx.depth < MAX_DEPTH:
            a, b = create_var_names(2)
            emit(ctx, f"for {a}, {b} in {dead_ref()}:")
            ctx.indent += indent_unit
            emit(ctx, f"{gen_other_var()} = {a} {rng.choice(_binops)} {b}")
            ctx.indent = ctx.indent[:-len(indent_unit)]
        elif r < 0.88:
            emit(ctx, f"{gen_other_var()} = {dead_ref()} {rng.choice(_binops)} {dead_ref()}")
        else:
            emit(ctx, f"{gen_other_var()} = {rich_expr_safe()}")

    def rich_stmt_dead(ctx, will_run=True):       # opaque-dead block of real-name constructs
        if ctx.depth >= MAX_DEPTH:
            v = gen_other_var()
            emit(ctx, f"{v} = {rich_expr_safe()}")
            return v
        emit(ctx, f"if {opaque_cond(ctx, truth=False)}:")
        ctx.indent += indent_unit
        ctx.depth += 1
        for _ in range(rng.randint(2, 4)):
            _emit_dead_construct(ctx)
        ctx.depth -= 1
        ctx.indent = ctx.indent[:-len(indent_unit)]

    def rand_import(ctx, will_run=True):          # dead import (reproduces import fingerprints)
        if not _imports:
            return add_random_line(ctx, will_run)
        # ALWAYS alias to a decoy name: a bare `import asyncio` (even in dead code)
        # makes `asyncio` a local of the enclosing function and shadows the real
        # module -> UnboundLocalError. `import X as <decoy>` binds only the decoy.
        m = rng.choice(_imports)
        emit(ctx, f"if {opaque_cond(ctx, truth=False)}:")
        ctx.indent += indent_unit
        if rng.random() < 0.5:
            emit(ctx, f"import {m} as {create_var_name()}")
        else:
            emit(ctx, f"from {m} import {rng.choice(name_pool)} as {create_var_name()}")
        ctx.indent = ctx.indent[:-len(indent_unit)]

    def rand_str_flood(ctx, will_run=True):
        # LIVE: emit feature-bearing decoy strings (colons/braces/hex/no-spaces/real
        # copies), single or as a list, so static string-greps drown in hits.
        v = gen_str_var(ctx)
        if rng.random() < 0.4:
            elems = ', '.join(make_rich_string() for _ in range(rng.randint(2, 5)))
            emit(ctx, f"{v} = [{elems}]")
        else:
            emit(ctx, f"{v} = {make_rich_string()}")
        return v

    def rand_hot_loop(ctx, will_run=True):
        # FIX 3: a LIVE decoy loop that iterates many times doing honeypot primitive
        # work, so an attacker profiling by execution frequency finds MANY hot loops,
        # not just the real one. Bounded iterations -> hot but cheap. The body must
        # NOT depend on the loop var surviving (a decoy in the body may reuse its
        # name -> a decoy loop var isn't reserved the way real names are), so we do
        # only self-contained honeypot/decoy work per iteration.
        if ctx.depth >= MAX_DEPTH:
            return add_random_line(ctx, will_run)
        emit(ctx, f"for {gen_other_var()} in range({rng.randint(6, 28)}):")
        ctx.indent += indent_unit
        ctx.depth += 1
        for _ in range(rng.randint(1, 3)):
            if rng.random() < 0.6:
                rand_honeypot(ctx, will_run=True)      # hot honeypot primitive work
            else:
                add_random_line(ctx, will_run=True)
        ctx.depth -= 1
        ctx.indent = ctx.indent[:-len(indent_unit)]

    # live (will_run=True) generators: safe to actually execute (no reads of
    # possibly-out-of-scope decoy vars, no side effects, dead loops never iterate).
    _live = [rand_num, rand_num_add, rand_str, rand_lst, add_pass, rand_func, rand_class,
             rand_dead_block, rand_comprehension, rand_ternary, rand_dict, rand_fstring, rand_tuple,
             rand_rich, rich_stmt_dead, rand_import, rand_honeypot, rand_fake_flow, rand_str_flood,
             rand_hot_loop]
    _live_w = [4, 4, 4, 3, 2, 2, 2, 3, 3, 3, 3, 3, 2, 6, 7, 2, 10, 7, 8, 4]
    # single-line live generators (used at max nesting depth; no blocks)
    _live_flat = [rand_num, rand_num_add, rand_str, rand_lst, add_pass,
                  rand_comprehension, rand_ternary, rand_dict, rand_fstring, rand_tuple, rand_rich,
                  rand_honeypot, rand_str_flood]
    _live_flat_w = [4, 4, 4, 3, 2, 3, 3, 3, 3, 2, 8, 10, 8]
    # dead (will_run=False) generators: only ever placed inside never-executed
    # blocks, so they may reference real names / out-of-scope decoys freely.
    _dead = _live + [rand_var, rand_print, rand_var_add, rand_call_func]
    _dead_w = _live_w + [4, 3, 3, 2]
    _dead_flat = _live_flat + [rand_var, rand_print, rand_var_add]
    _dead_flat_w = _live_flat_w + [4, 3, 3]

    if entangle:
        _live = _live + [rand_entangle]; _live_w = _live_w + [10]
        _live_flat = _live_flat + [rand_entangle]; _live_flat_w = _live_flat_w + [10]

    # Expand the weighted pools ONCE into flat lists, so per-call dispatch is a
    # single rng.choice instead of random.choices re-accumulating the weight table
    # every call.
    def _expand(pool, weights):
        out = []
        for gen, wt in zip(pool, weights):
            out.extend([gen] * wt)
        return out

    _live_x = _expand(_live, _live_w)
    _live_flat_x = _expand(_live_flat, _live_flat_w)
    _dead_x = _expand(_dead, _dead_w)
    _dead_flat_x = _expand(_dead_flat, _dead_flat_w)

    def add_random_line(ctx, will_run=True):
        if ctx.depth >= MAX_DEPTH:
            pool = _live_flat_x if will_run else _dead_flat_x
        else:
            pool = _live_x if will_run else _dead_x
        return rng.choice(pool)(ctx, will_run)

    # ---- compute safe insertion points from the AST ----
    # Walk scope-aware so we can refuse to inject where it would change behavior:
    #   * class scope (incl. class-level loops/ifs): added names become class
    #     attributes -> corrupts Enum/Flag members, metaclass ns, vars()/__dict__.
    #   * any scope that calls locals()/globals()/vars()/dir(): added names show up
    #     in what it returns.
    # And never inject before an `elif` line (an elif is a nested ast.If in the
    # parent's orelse; a decoy there would split the if/elif chain).
    points = []  # (zero-based line index, indent string)
    wrappables = []  # (start_idx0, end_idx0, base_ws) of real stmts safe to re-nest
    seen = set()

    def add_body_points(owner, field, body, scope_binds, in_func):
        start_idx = 0
        if _is_docstring(body[0]):
            start_idx = 1
        if isinstance(owner, ast.Module) and field == 'body':
            while start_idx < len(body) and _is_future_import(body[start_idx]):
                start_idx += 1
        for idx in range(start_idx, len(body)):
            stmt = body[idx]
            L = _eff_start_line(stmt)
            line = lines[L - 1]
            stripped = line.lstrip()
            ws = _leading_ws(line)
            if getattr(stmt, 'decorator_list', None):
                if not stripped.startswith('@'):
                    continue
            elif stmt.col_offset != len(ws):
                continue
            if _ELIF_RE.match(stripped):       # never split an if/elif chain
                continue
            if L in dno_protected or (L - 1) in seen:
                continue
            seen.add(L - 1)
            # real locals definitely bound before this line -> safe to entangle
            ent = tuple(sorted({nm for nm, bl in scope_binds if bl < L})) if scope_binds else ()
            points.append((L - 1, ws, ent, in_func))
            # can this real statement be re-nested into an injected wrapper? Only
            # single-physical-line statements: re-indenting a multi-line statement
            # would prepend whitespace INSIDE a multi-line string literal and change
            # its content (triple-quoted strings, etc.).
            if _wrappable(stmt):
                e = getattr(stmt, 'end_lineno', None) or L
                if e == L and L not in dno_protected:
                    wrappables.append((L - 1, e - 1, ws))

    def visit(node, scope_ok, in_class, scope_binds, in_func):
        is_class = isinstance(node, ast.ClassDef)
        for field, value in ast.iter_fields(node):
            if (isinstance(value, list) and value
                    and all(isinstance(x, ast.stmt) for x in value)):
                if scope_ok and not in_class and not (is_class and field == 'body'):
                    add_body_points(node, field, value, scope_binds, in_func)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, not _scope_introspects(child), False,
                      _scope_bindings(child) if entangle else (), True)
            elif isinstance(child, ast.ClassDef):
                visit(child, scope_ok, True, (), False)
            else:
                visit(child, scope_ok, in_class, scope_binds, in_func)

    visit(tree, not _scope_introspects(tree), False,
          _scope_bindings(tree) if entangle else (), False)

    # Module-end fallback: appending decoys AFTER every real statement is always
    # safe (any in-module locals()/globals()/vars()/dir() call already ran, and
    # module-level names never become class attributes), so even all-class or
    # namespace-introspecting modules -- which otherwise have no injectable scope
    # -- can still be diluted and reach a new_lines_target. Indexed one past the
    # last physical line so the splice appends it at the very end.
    ment = tuple(sorted({nm for nm, _ in _scope_bindings(tree)})) if entangle else ()
    points.append((len(lines), '', ment, False))  # module-end (always available)
    points.sort(key=lambda p: p[0])

    # ---- generate decoys against a global line budget ----
    # Two ways to size the output:
    #   new_lines_target > 0 : pad the FINAL file to ~this many lines (a floor --
    #       files already bigger than the target are left as-is, since we never
    #       remove real code). One pass, exact, deterministic; good for making a
    #       whole project's files a uniform length so the "main" file doesn't stand
    #       out. Overrides new_line_ratio.
    #   otherwise            : add ~new_line_ratio decoy lines per real code line.
    n_code_lines = sum(1 for ln in lines if ln.strip())
    if new_lines_target and new_lines_target > 0:
        budget = max(0, int(new_lines_target) - len(lines))  # decoys needed to reach target
    else:
        budget = round(ratio * n_code_lines)
    inserts = {}
    if points and budget > 0:
        ctxs = {idx: Ctx(ind, ent, infn) for idx, ind, ent, infn in points}
        keys = [idx for idx, _, _, _ in points]
        produced = 0
        safety = budget * 4 + 100
        while produced < budget and safety > 0:
            safety -= 1
            ctx = ctxs[rng.choice(keys)]
            before = len(ctx.out)
            add_random_line(ctx, will_run=True)
            produced += len(ctx.out) - before
        inserts = {idx: ctx.out for idx, ctx in ctxs.items() if ctx.out}

    # ---- re-nest a fraction of real statements into injected always-true wrappers.
    # Same bytes, same execution order, same scope -> still imports and runs, but the
    # real code stops reading as a flat top-level spine: each wrapped statement sits
    # several levels deep inside opaque `if` / single-run `for` / `try..finally`
    # scaffolding, so reconstructing the real control flow is itself a proving
    # problem. Injected names can't collide with real ones (see _build_name_pool). ----
    def _mint_ints(ws, k):
        vs, setup = [], []
        for _ in range(k):
            v = create_var_name()
            setup.append(ws + f"{v} = {rng.choice(number_pool)}")
            vs.append(v)
        return vs, setup

    def _wrap_statement(start0, end0, base_ws, levels):
        body = [(indent_unit * levels) + lines[k] for k in range(start0, end0 + 1)]
        for i in range(levels - 1, -1, -1):
            hdr_ws = base_ws + indent_unit * i
            kind = rng.choice(('if', 'if', 'for', 'try'))       # bias to the cheapest/safest
            if kind == 'if':
                vs, setup = _mint_ints(hdr_ws, rng.randint(1, 2))
                body = setup + [hdr_ws + f"if {_opaque_guard(rng, vs, number_pool, True)}:"] + body
            elif kind == 'for':
                vs, setup = _mint_ints(hdr_ws, rng.randint(1, 2))
                once = '(' + _mba_zero(rng, vs, number_pool) + ') + 1'   # == 1 -> runs exactly once
                body = setup + [hdr_ws + f"for {create_var_name()} in range({once}):"] + body
            else:                                                # try/finally: finally runs a harmless decoy
                body = ([hdr_ws + "try:"] + body
                        + [hdr_ws + "finally:",
                           hdr_ws + indent_unit + f"{create_var_name()} = {rng.choice(number_pool)}"])
        return body

    wrapped = {}
    for (s0, e0, bws) in wrappables:
        if rng.random() < 0.7:                    # ~70% of eligible real statements get re-nested
            wrapped[s0] = (e0, _wrap_statement(s0, e0, bws, rng.randint(1, 3)))

    # ---- splice: decoys before each line; a re-nested statement replaces its span.
    # `_hpc = [0]` (the runtime-varying honeypot counter) is injected once, as the
    # first line after any docstring/__future__, so every live decoy can bump it. ----
    out_lines = []
    n = len(lines)
    i = 0
    hpc_done = False
    while i < n:
        if i == _prepend_idx and not hpc_done:
            out_lines.append(f"{_hpc} = [0]"); hpc_done = True
        if i in inserts:
            out_lines.extend(inserts[i])
        if i in wrapped:
            e0, wlines = wrapped[i]
            out_lines.extend(wlines)
            i = e0 + 1
            continue
        out_lines.append(lines[i])
        i += 1
    if not hpc_done:                    # empty/only-docstring body: still bind it before module-end decoys
        out_lines.append(f"{_hpc} = [0]")
    if n in inserts:                    # module-end fallback decoys
        out_lines.extend(inserts[n])
    return '\n'.join(out_lines)


if __name__ == '__main__':
    demo = (
        "import math\n"
        "def area(r):\n"
        "    return math.pi * r ** 2\n"
        "vals = [1,\n"
        "    2,\n"
        "    3\n"
        "]\n"
        "for v in vals:\n"
        "    print(area(v))\n"
    )
    print(obfuscate_python(demo, remove_prints=False))
