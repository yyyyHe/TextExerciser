# -*- coding: utf-8 -*-
from code.src import ALL_TYPES

# define the index of lex.
NAME_DICT = {"a": "Object", "b": "Number", "c": "Decoration", "d": "Special", "e": "Space", "f": "Letter", "g": "Digit",
             "h": "Bigger", "i": "Smaller", "j": "Equal", "k": "Or", "l": "And", "m": "Not", "n": "Transition",
             "o": "Upperbound", "p": "Lowerbound", "q": "End", "r": "Alert", "s": "Valid", "t": "Body",
             "u": "", "v": "", "w": "", "x": "", "y": "", "z": "Null"
             }

# a# :(Object)
OBJECT = ALL_TYPES

# t# :(Body)：[Number，Decoration+Letter，Special，Space]
BODY = ['Number', 'Special', 'Space', 'Letter']

# b# :(Number)：[number, code, digit],
NUMBER = ["number", "code", "digit", "value"]

# c# :(Decoration)：[uppercase, upper, capital,lowercase, lower],
DECORATION = ["uppercase", "upper", "capital", "lowercase", "lower", "alphabetical", "numerical"]

UPPER_CASE = ["uppercase", "upper", "capital", "upper case"]
LOWER_CASE = ["lowercase", "lower", "minuscule", "lower case"]

# d# :(Special)：[symbol, underscore, dash ],
SPECIAL = ["symbol", "underscore", "dash", "special", "point", "@", "_", "-", "\."]

# e# :(Space)：[blank space]，
SPACE = ["blank", "space", "blankspace", "whitespace"]

# f# :(Letter)：[letter, character]
LETTER = ["letter", "character", "^word", "alphabet", "alpha"]

# g# :(Digit)：[0-9]，NN
DIGIT = [r'taggedascd_([^\s\n\t]+)', r'[0-9]+',
         "^one", "^two", "^three", "^four", "^five", "^six", "^seven", "^eight", "^nine", "^ten", "^eleven", "^twelve",
         "^thirteen", "^fourteen",
         "^fifteen", "^sixteen", "^seventeen", "^eighteen", "^nineteen", "^twenty"
         ]

# h# :(Bigger)：more than, more, at least, min ,minimum , '+'
BIGGER = ["^more", "least", "^min", "minimum", "\+", "long"]

# i# :(Smaller)：less than, less, at most, max, maximum, within
SMALLER = ["^less", "most", "^max", "maximum", "within", "exceed", "short"]

# j# :(Equal)：only, equal ,
EQUAL = ["only", "equal", ","]

# k# :(Or)： or, '|'
OR = ["^or", "\|", "/", r'\\']

# l# :(And)：and
AND = ["^and"]

# m# :(Not)：not, no, don't, isn't
NOT = ["^not", "^no", "dont", "isnt", "cant", "doesnt"]

# n# :(Transition)：to, '-'
TRANSITION = ["^to$", "\-",
              "[\u002D\u058A\u05BE\u1400\u1806\u2010-\u2015\u2E17\u2E1A\u2E3A\u2E3B\u2E40\u301C\u3030\u30A0\uFE31\uFE32\uFE58\uFE63\uFF0D]"]

# o# :(Upperbound)：contain, between,(,:
UPPER_BOUND = ["^contain", "^between", "\(", ":", '^both', "include"]

# q# :(End)：'.' , ';' , '!' , '?'
END = ["\.", ";", "!", "\?", '\)']

# r# :(Alert)：too long, invalid, error, wrong,
ALERT = ["invalid", "error", "wrong", "incorrect", "unacceptable", "empty", "required", "limit", "fail", "failed"]

# s# :(Valid)
VALID = ["correct", "^valid", "recognize", "right", "verif", "acceptable", "match", "exist"]

# z# :(Null)
NULL = []

# p# :(Lowerbound)
LOWER_BOUND = [
    "End",
    # "Null",
]

ROOT_DOMAIN = ['com', 'net', 'org', 'gov', 'mil', 'aero', 'asia', 'biz', 'cat', 'coop', 'info', 'int', 'jobs', 'mobi',
               'museum',
               'name', 'post', 'pro', 'tel', 'travel', 'xxx', 'ac', 'ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'an',
               'ao',
               'aq', 'ar',
               'as', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bm', 'bn',
               'bo', 'br', 'bs', 'bt',
               'bv', 'bw', 'by', 'bz', 'ca', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'cr',
               'cs', 'cu', 'cv', 'cx',
               'cy', 'cz', 'dd', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'eu',
               'fi', 'fj', 'fk', 'fm',
               'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gp', 'gq', 'gr', 'gs',
               'gt', 'gu', 'gw', 'gy',
               'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'io', 'iq', 'ir', 'is', 'it', 'je',
               'jm', 'jo', 'jp', 'ke',
               'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls',
               'lt', 'lu', 'lv', 'ly',
               'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu',
               'mv', 'mw', 'mx', 'my',
               'mz', 'na', 'nc', 'ne', 'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf',
               'pg', 'ph', 'pk', 'pl',
               'pm', 'pn', 'pr', 'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd',
               'se', 'sg', 'sh', 'si',
               'sj', 'Ja', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss', 'st', 'su', 'sv', 'sx', 'sy', 'sz', 'tc', 'td',
               'tf', 'tg', 'th', 'tj',
               'tk', 'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'us', 'uy', 'uz',
               'va', 'vc', 've', 'vg',
               'vi', 'vn', 'vu', 'wf', 'ws', 'ye', 'yt', 'yu', 'za', 'zm', 'zw']

# URL Regex
URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
