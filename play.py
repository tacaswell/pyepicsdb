# Build the lexer


victim = """
# a comment

record(waveform, "$(P)$(R)FilePath")
{
    field(PINI, "YES")
    field(DTYP, "asynOctetWrite")
# can not deal with () in side of template yet
#    field(INP,  "@asyn($(PORT),$(ADDR),$(TIMEOUT))FILE_PATH")
    field(FTVL, "CHAR")
    field(NELM, "256")
# can not deal with info yet
#    info(autosaveFields, "VAL")
}
record(subArray, "$(P)$(R)Dim1SA")
{
    field(INP,  "$(P)$(R)Dimensions_RBV NPP NMS")
    field(FTVL, "LONG")
    field(MALM, "10")
    field(NELM, "1")
    field(INDX, "1")
    field(FLNK, "$(P)$(R)ArraySize1_RBV")
}
"""

victim2 = 'record(waveform, "$(P)$(R)FilePath")'
victim3 = 'record(a, "foo$(b)bar$(baz)"){field(PINI, "YES")}'

reserved = {
    'record': 'RECORD',
    'field': 'FIELD',
    'info': 'INFO',
#    'include': 'INCLUDE'
    }

states = (
    ('quoted', 'inclusive'),
    )

tokens = [
    'WORD',
    'NL',
    'DOLLAR',
    'QUOTE',
    ] + list(reserved.values())

literals = ['{', '}', ',', '(', ')']
t_ignore = r' '
t_DOLLAR = r'\$'


def t_QUOTE(t):
    r'"'
    t.lexer.begin('quoted')
    return t

def t_quoted_QUOTE(t):
    r'"'
    t.lexer.begin('INITIAL')
    return t

def t_NL(t):
    r'\n'
    pass

def t_COMMENT(t):
    r'\#.*'
    pass
    # No return value. Token discarded


def t_WORD(t):
    r'[A-Za-z0-9@_]+'
    t.type = reserved.get(t.value, 'WORD')
    return t

def t_quoted_WORD(t):
    r'[A-Za-z0-9@_][A-Za-z0-9@_ ]+'
    t.type = reserved.get(t.value, 'WORD')
    return t


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

import ply.lex as lex
lex.lex()

records = set()

class record(object):
    def __init__(self, rec_type, name_template, fields):
        self.rec_type = rec_type
        self.template = name_template
        self.fields = fields

    def __repr__(self):
        out = '''
rec_type : {rtype!r}
pv_template : {template!r}
'''.format(rtype=self.rec_type, template=self.template)
        for f in self.fields:
            out += '\t{!r}\n'.format(f)
        return out

class template(object):
    def __init__(self, template, reqs):
        self.template = template
        self.reqs = reqs

    def __repr__(self):
        return self.template + ', ' + str(self.reqs)

class field(object):
    def __init__(self, ftype, val):
        self.ftype = ftype
        self.val = val

    def __repr__(self):
        return self.ftype + ', ' + str(self.val)

def p_rec_set(p):
    '''rec_set : rec
               | rec rec_set
    '''
    pass

def p_rec_words(p):
    '''rec : RECORD "(" WORD "," template ")" body'''
    records.add(record(p[3], p[5], p[7]))

def p_template(p):
    '''template : QUOTE composite QUOTE
    '''
    p[0] = p[2]

def p_composite(p):
    '''composite : target
                 | WORD
                 | composite composite
    '''
    if len(p) == 2:
        try:
            p[1].reqs
            p[0] = p[1]
        except AttributeError:
            p[0] = template(p[1], set())
    else:
        p[0] = template(p[1].template + p[2].template,
                        p[1].reqs | p[2].reqs)

def p_target(p):
    'target : DOLLAR "(" WORD ")"'
    p[0] = template('{' + p[3] + '}', set((p[3], )))

def p_body(p):
    '''
    body : "{" fields "}"
    '''
    p[0] = p[2]

def p_fields(p):
    '''
    fields : fld
           | fld fields
    '''
    p[0] = set((p[1], ))
    if len(p) > 2:
        for f in p[2]:
            p[0].add(f)


def p_fld(p):
    '''
    fld : FIELD "(" WORD "," template ")"
    '''
    p[0] = field(p[3], p[5])


def p_error(p):
    print("Syntax error at '%s'" % p.value)
    print(p)

import ply.yacc as yacc
p = yacc.yacc()
lexer = lex.lex()


p.parse(victim)
print(records)
