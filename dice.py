# Handles dice roll expression parsing
import random
import re
from typing import List, Callable
from discord.ext import commands
from inspect import signature
import util


# Preparse items


# Actual expression tree items
class Expression:
    def as_int(self):
        raise NotImplementedError()


class Operation(Expression):
    def __init__(self, sym):
        self.sym = sym


class Value(Expression):
    pass


class PrefixOp(Operation):
    """ Prefix op goes before its arguments """

    def __init__(self, sym: str, func: Callable, args):
        super().__init__(sym)
        exp_arg_count = len(signature(func).parameters)
        if exp_arg_count != len(args):
            raise ParseErr("{} expects {} arguments, but only {} were given.")
        self.func = func
        self.args = args

    def as_int(self):
        return self.func(*self.args)


class BinOp(Operation):
    """ Binary op goes betwixt two items """

    def __init__(self, sym: str, l: Expression, r: Expression):
        super().__init__(sym)
        self.l = l
        self.r = r

    def func(self, l: int, r: int) -> int:
        raise NotImplementedError()

    def as_int(self):
        return self.func(self.l.as_int(), self.r.as_int())

    def __str__(self):
        return "{} {} {}".format(self.l, self.sym, self.r)


class Add(BinOp):
    def func(self, l: int, r: int) -> int:
        return l + r

    def __init__(self, l: Expression, r: Expression):
        super().__init__("+", l, r)

    def __str__(self):
        return "+"


class Sub(BinOp):
    def func(self, l: int, r: int) -> int:
        return l - r

    def __init__(self, l: Expression, r: Expression):
        super().__init__("-", l, r)

    def __str__(self):
        return "-"


class SubExpr(Value):
    def __init__(self, sub_expr_toks: List[Expression]):
        self.sub_expr_toks = sub_expr_toks

    def __str__(self):
        return "({})".format(" ".join(str(et) for et in self.sub_expr_toks))


class Num(Value):
    def __init__(self, val: int):
        self.val = val

    def __str__(self):
        return str(self.val)


class Dice(Value):
    def __init__(self, max_val: int):
        self.max_val = max_val
        self.rolled_val = -1
        self.reroll()

    def reroll(self):
        self.rolled_val = random.randrange(1, self.max_val + 1)

    def __str__(self):
        return str(self.rolled_val)


class Negated(Value):
    def __init__(self, wraps: Value):
        self.wrapped = wraps

    def __str__(self):
        return "-{}".format(self.wrapped)


class ParseErr(Exception):
    def __init__(self, message: str):
        self.message = message


def eval_parsed_expression(token: Value) -> int:
    # If it's a simple constant just do that, haha
    if isinstance(token, Num):
        return token.val
    elif isinstance(token, Dice):
        return token.rolled_val
    # If negated just return the negative value
    elif isinstance(token, Negated):
        return -eval_parsed_expression(token.wrapped)
    elif isinstance(token, SubExpr):
        tokens = token.sub_expr_toks

        # Step one: copy the list
        tokens = list(tokens)

        # Step two: fail if empty
        if not tokens:
            raise ParseErr("Need at least one value")

        # Step three: in cases of <SOME OPERATION> - VAL, we just move the - into the val, as a negated
        def wrap_negatives(a, b, c):
            if isinstance(a, Operation):
                if isinstance(b, Sub):
                    if isinstance(c, Value):
                        return [a, Negated(c)]

        tokens = util.predicate_transform(tokens, wrap_negatives)

        # Step four: since the above should've taken care of any funky op sequences, now there should be a strict
        # operator, value, operator, value alternating pattern
        def validate_alternation(a, b):
            if (isinstance(a, Operation) and isinstance(b, Operation)) or (
                    isinstance(a, Value) and isinstance(b, Value)):
                raise ParseErr("Illegal token sequence {} {}".format(a, b))

        util.predicate_transform(tokens, validate_alternation)

        # Step five: If the leading thing is a negative, just make it a negation instead
        if isinstance(tokens[0], Sub):
            tokens = [Negated(tokens[1])] + tokens[2:]

        # Step six: Now we solve, quite simply! First token guaranteed to be a value
        # We might actually parse as a tree later but for now we basically just flatten as a list.
        cv = eval_parsed_expression(tokens[0])
        for op, val in zip(tokens[1::2], tokens[2::2]):
            if isinstance(op, Add):
                cv = cv + eval_parsed_expression(val)
            elif isinstance(op, Sub):
                cv = cv - eval_parsed_expression(val)
        return cv


def parse_expression(expr: str) -> List[Expression]:
    """Turn a string into expression tokens"""
    # First, pad around each op for ease of parsing
    for op in ["+", "-", "(", ")"]:
        expr = expr.replace(op, " " + op + " ")

    # Split into tokens
    tokens = re.split(r"\s+", expr.strip())

    # Go through and replace tokens with class reprs
    parsed_tokens: List[Expression] = []
    for token in tokens:
        r = re.match(r"(\d+)d(\d+)", token)
        # Is it plus/minus?
        if token == "+":
            parsed_tokens.append(Add(None, None))
        elif token == "-":
            parsed_tokens.append(Sub(None, None))
        # Is it a dice roll?
        elif r:
            # Get the roll count and limit
            rolls = int(r.group(1))
            limit = int(r.group(2))

            # Validate
            if rolls <= 0 or limit <= 0:
                raise ParseErr("Cannot roll less than 1 dice / a less than 1 sided dice")

            # Make the items into sub tokens
            sub_tokens = []
            for _ in range(rolls):
                sub_tokens.append(Dice(limit))
                sub_tokens.append(Add(None, None))

            # Cut off the extra add
            sub_tokens = sub_tokens[:-1]

            # Finally, add the sub expression
            parsed_tokens.append(SubExpr(sub_tokens))
        else:
            # Is it a number?
            try:
                i = int(token)
                parsed_tokens.append(Num(i))
            except (TypeError, ValueError):
                # If we hit this exception, we've hit an unrecognizable token
                raise ParseErr("Unparseable token {}".format(token))

    # Job's done!
    return parsed_tokens


def handle_dice_cmd(cmd: str) -> str:
    try:
        # Parse it!
        parsed = parse_expression(cmd)

        # make it a subexpr then evaluaate
        expr = SubExpr(parsed)
        result = "{} = {}".format(expr, eval_parsed_expression(expr))
        if len(result) > 1000:
            result = "{} = {}".format(str(expr)[:1000], eval_parsed_expression(expr))
        return result
    except ParseErr as e:
        return "Error: {}".format(e.message)


class DiceRoller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, *, dice_expr: str):
        result = handle_dice_cmd(dice_expr)
        await ctx.send(result)
