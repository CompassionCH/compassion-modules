import html
import json
import logging
import re
import unicodedata

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# "% set NAME=EXPR" is a non-standard shorthand that was never converted to a
# real QWeb <t t-set> directive. QWeb only interprets t-* attributes on
# elements, so these lines were rendered verbatim as literal text in every
# sent thank you letter, and the variables they were meant to define stayed
# unset (leaving dependent sentences blank).
PRAGMA_SET_RE = re.compile(
    r"^(?P<indent>\s*)%\s*set\s+(?P<name>[^\s=]+)\s*=\s*(?P<expr>.*)$"
)

# Single stray leftover with no matching "% if" anywhere in the template.
STRAY_PRAGMA_RE = re.compile(r"^\s*%\s*endif\s*$")

# Matches a variable name already converted to a real <t t-set> tag - needed
# so this migration stays idempotent/safe to re-run on a database where an
# earlier version of it already converted the pragma line but kept an
# invalid (non-ASCII) varname.
TSET_TAG_NAME_RE = re.compile(r'<t\s+t-set="(?P<name>[^"]+)"')

# QWeb's <t t-set> only accepts ASCII alphanumerics/underscore in varnames;
# some variable names use ligatures (e.g. "cœur") that aren't covered by
# plain accent-stripping.
_LIGATURES = {"œ": "oe", "Œ": "Oe", "æ": "ae", "Æ": "Ae"}


def _sanitize_varname(name):
    for src, dst in _LIGATURES.items():
        name = name.replace(src, dst)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^0-9A-Za-z_]", "_", name)


# fr_CH accesses products[0].thanks_name (a Char field, False when unset)
# directly and unguarded, unlike de_DE/it_IT which already define a safe
# "thanks_name" variable ("products[0].thanks_name if ... else ''"). This
# crashes with "'bool' object is not subscriptable"/AttributeError for any
# product without a thanks_name (e.g. "undesignated donation") - previously
# masked because the surrounding "% set" line never actually executed.
_FR_UNSAFE_THANKS_NAME_TERNARY = (
    "(products[0].thanks_name if products[0].thanks_name[:1] in "
    "(&#x27;.&#x27;,&#x27;!&#x27;,&#x27;?&#x27;) else &#x27; &#x27;"
    "+products[0].thanks_name)"
)
_FR_SAFE_THANKS_NAME_TERNARY = (
    "(thanks_name if thanks_name[:1] in "
    "(&#x27;.&#x27;,&#x27;!&#x27;,&#x27;?&#x27;) else &#x27; &#x27;+thanks_name)"
)
_FR_UNSAFE_LINE_THANKS_NAME = "line.product_id.thanks_name.replace("
_FR_SAFE_LINE_THANKS_NAME = "(line.product_id.thanks_name or &#x27;&#x27;).replace("
_FR_PRODUCTS_TSET = (
    '<t t-set="products" t-value="invoice_lines.mapped(&#x27;product_id&#x27;)"/>'
)


# Shared by fr_CH and de_DE, both inside a previously-dead "% set" line:
# default_code is a Char field, False for any product without one, and
# .startswith() raises AttributeError on a bool.
_UNSAFE_DEFAULT_CODE_STARTSWITH = "products[0].default_code.startswith("
_SAFE_DEFAULT_CODE_STARTSWITH = "(products[0].default_code or &#x27;&#x27;).startswith("


def _fix_unguarded_thanks_name(body):
    if _FR_UNSAFE_THANKS_NAME_TERNARY not in body:
        return body
    body = body.replace(_FR_UNSAFE_THANKS_NAME_TERNARY, _FR_SAFE_THANKS_NAME_TERNARY)
    body = body.replace(_FR_UNSAFE_LINE_THANKS_NAME, _FR_SAFE_LINE_THANKS_NAME)
    body = body.replace(
        _FR_PRODUCTS_TSET,
        _FR_PRODUCTS_TSET
        + '\n    <t t-set="thanks_name" t-value="products[0].thanks_name if '
        'products[0].thanks_name else &#x27;&#x27;"/>',
    )
    return body


def _fix_body(body):
    if not body:
        return body
    body = body.replace("&amp;gt;", "&gt;").replace("&amp;lt;", "&lt;")
    body = _fix_unguarded_thanks_name(body)
    body = body.replace(_UNSAFE_DEFAULT_CODE_STARTSWITH, _SAFE_DEFAULT_CODE_STARTSWITH)

    # Rename any variable whose name QWeb would reject, everywhere it's used
    # (not just where it's declared) - existing t-out/t-if/t-value
    # expressions already reference the original name. Checks both raw
    # "% set" pragma lines and already-converted <t t-set> tags, so this
    # stays safe to re-run regardless of which state the database is in.
    invalid_names = set()
    for line in body.split("\n"):
        match = PRAGMA_SET_RE.match(line)
        if match:
            invalid_names.add(match["name"])
    invalid_names.update(m["name"] for m in TSET_TAG_NAME_RE.finditer(body))
    for name in invalid_names:
        safe_name = _sanitize_varname(name)
        if safe_name != name:
            body = re.sub(rf"\b{re.escape(name)}\b", safe_name, body)

    lines = []
    for line in body.split("\n"):
        if STRAY_PRAGMA_RE.match(line):
            continue
        match = PRAGMA_SET_RE.match(line)
        if match:
            expr = html.escape(match["expr"].strip(), quote=True)
            line = f'{match["indent"]}<t t-set="{match["name"]}" t-value="{expr}"/>'
        lines.append(line)
    return "\n".join(lines)


@openupgrade.migrate()
def migrate(env, version):
    template = env.ref("thankyou_letters.thankyou_letter_template")
    env.cr.execute("SELECT body_html FROM mail_template WHERE id = %s", (template.id,))
    (body_html,) = env.cr.fetchone()
    if not body_html:
        return

    fixed = {lang: _fix_body(body) for lang, body in body_html.items()}
    if fixed == body_html:
        _logger.info("thankyou_letter_template: nothing to fix")
        return

    env.cr.execute(
        "UPDATE mail_template SET body_html = %s WHERE id = %s",
        (json.dumps(fixed), template.id),
    )
    _logger.info(
        "thankyou_letter_template: fixed raw pragma lines / double-escaped "
        "entities for languages: %s",
        ", ".join(lang for lang in fixed if fixed[lang] != body_html.get(lang)),
    )
