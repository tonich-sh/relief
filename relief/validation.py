# coding: utf-8
"""
    relief.validation
    ~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from relief import Unspecified, NotUnserializable


class Validator(object):

    @property
    def valid(self):
        return True

    @property
    def invalid(self):
        return False

    def validate(self, element, context):
        return self.invalid

    def note_error(self, element, error, context, substitutions=None):
        if substitutions is None:
            substitutions = {}
        element.errors.append(error.format(**substitutions))

    def is_unusable(self, element):
        return (
            element.value is Unspecified or
            element.value is NotUnserializable
        )

    def __call__(self, element, context):
        result = self.validate(element, context)
        if result:
            print('validate: {}[{}] ({}) by {} with {}'.format(element.__class__.__name__, context.get('name', 'unnamed'), element.raw_value, self.__class__.__name__, result))
        else:
            print('validate: {}[{}] ({}) by {} with {}'.format(element.__class__.__name__, context.get('name', 'unnamed'), element.raw_value, self.__class__.__name__, element.errors))
        return result


class Present(Validator):
    """
    Validator that fails with :attr:`message` if the value is unspecified.
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u"May not be blank."

    def validate(self, element, context):
        if element.value is Unspecified:
            self.note_error(element, self.message, context)
            return self.invalid
        return self.valid


class Converted(Validator):
    """
    Validator that fails with :attr:`message` if the value is not
    unserializable.
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u"Not a valid value."

    def validate(self, element, context):
        if self.is_unusable(element):
            self.note_error(element, self.message, context)
            return self.invalid
        return self.valid


class IsTrue(Validator):
    """
    Validator that fails with :attr:`message` if the value is false-ish.
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u"Must be true."

    def validate(self, element, context):
        if self.is_unusable(element) or not element.value:
            self.note_error(element, self.message, context)
            return self.invalid
        return self.valid


class IsFalse(Validator):
    """
    Validator that fails with :attr:`message` if the value is true-ish.
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u"Must be false."

    def validate(self, element, context):
        if self.is_unusable(element) or element.value:
            self.note_error(element, self.message, context)
            return self.invalid
        return self.valid


class ShorterThan(Validator):
    """
    Validator that fails with :attr:`message` if the length of the value is
    equal to or longer than the given `upperbound`.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{upperbound}`` in
    #: the message is substituted with the given `upperbound`.
    message = u"Must be shorter than {upperbound}."

    def __init__(self, upperbound):
        self.upperbound = upperbound

    def validate(self, element, context):
        if self.is_unusable(element) or len(element.value) >= self.upperbound:
            self.note_error(
                element,
                self.message,
                context,
                substitutions={"upperbound": self.upperbound}
            )
            return self.invalid
        return self.valid


class LongerThan(Validator):
    """
    Validator that fails with :attr:`message` if the length of the value is
    equal to or shorter than the given `lowerbound`.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{lowerbound}`` in
    #: the message is substituted with the given `lowerbound`.
    message = u"Must be longer than {lowerbound}."

    def __init__(self, lowerbound):
        self.lowerbound = lowerbound

    def validate(self, element, context):
        if self.is_unusable(element) or len(element.value) <= self.lowerbound:
            self.note_error(
                element,
                self.message,
                context,
                substitutions={"lowerbound": self.lowerbound}
            )
            return self.invalid
        return self.valid


class LengthWithinRange(Validator):
    """
    Validator that fails with :attr:`message` if the length of the value is
    less than or equal to `start` or greater than or equal to `end`.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{start}`` and
    #: ``{end}`` is substituted with the given `start` and `end`.
    message = u"Must be longer than {start} and shorter than {end}."

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, element, context):
        if (not self.is_unusable(element) and
            self.start < len(element.value) < self.end
           ):
            return self.valid
        self.note_error(
            element,
            self.message,
            context,
            substitutions={"start": self.start, "end": self.end}
        )
        return self.invalid


class ContainedIn(Validator):
    """
    A validator that fails with ``"Not a valid value."`` if the value is not
    contained in `options`.
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u"Not a valid value."

    def __init__(self, options):
        self.options = options

    def validate(self, element, context):
        if element.value not in self.options:
            self.note_error(element, u"Not a valid value.", context)
            return self.invalid
        return self.valid


class LessThan(Validator):
    """
    Validator that fails with :attr:`message` if the value is greater than or
    equal to `upperbound`.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{upperbound}`` is
    #: substituted with the given `upperbound`.
    message = u"Must be less than {upperbound}."

    def __init__(self, upperbound):
        self.upperbound = upperbound

    def validate(self, element, context):
        if self.is_unusable(element) or element.value >= self.upperbound:
            self.note_error(
                element,
                self.message,
                context,
                substitutions={"upperbound": self.upperbound}
            )
            return self.invalid
        return self.valid


class GreaterThan(Validator):
    """
    Validator that fails with :attr:`message` if the value is less than or
    equal to `lowerbound`.
    """
    #: Message that is stored in the :attr:`Element.errors`. ``{lowerbound}``
    #: is substituted with the given `lowerbound`.
    message = u"Must be greater than {lowerbound}."

    def __init__(self, lowerbound):
        self.lowerbound = lowerbound

    def validate(self, element, context):
        if self.is_unusable(element) or element.value <= self.lowerbound:
            self.note_error(
                element,
                self.message,
                context,
                substitutions={"lowerbound": self.lowerbound}
            )
            return self.invalid
        return self.valid


class WithinRange(Validator):
    """
    Validator that fails with :attr:`message` if the value is less than or
    equal to `start` or greater than or equal to `end.`
    """
    #: Message that is stored in :attr:`Element.errors`. ``{start}`` and
    #: ``{end}`` are substituted with the given `start` and `end`.
    message = u"Must be greater than {start} and shorter than {end}."

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def validate(self, element, context):
        if not self.is_unusable(element) and self.start < element.value < self.end:
            return self.valid
        self.note_error(
            element,
            self.message,
            context,
            substitutions={"start": self.start, "end": self.end}
        )
        return self.invalid


class ItemsEqual(Validator):
    """
    Validator that fails with :attr:`message` if two items in the value are
    unequal.

    The items are defined with the tuples `a` and `b` each of which consist of
    two elements ``(label, key)``. The `key` is used to determine the item to
    compare and the `label` is used for substitution in the message.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{a}`` and ``{b}``
    #: are substituted with the labels in the given `a` and `b`.
    message = u"{a} and {b} must be equal."

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def validate(self, element, context):
        if (not self.is_unusable(element) and
            element.value[self.a[1]] == element.value[self.b[1]]
           ):
            return self.valid
        self.note_error(
            element,
            self.message,
            context,
            substitutions={"a": self.a[0], "b": self.b[0]}
        )
        return self.invalid


class AttributesEqual(Validator):
    """
    Validator that fails with :attr:`message` if two attributes of the value
    are unequal.

    Similar to :class:`ItemsEqual` the attributes are defined with the tuples
    `a` and `b` each of which consists of two element in the form ``(label,
    attribute_name)``. `attribute_name` is used to determine the attributes to
    compare and the `label` is used for substitution in the message.
    """
    #: Message that is stored in :attr:`Element.errors`. ``{a}`` and ``{b}``
    #: are substituted with the labels in the given `a` and `b`.
    message = u"{a} and {b} must be equal."

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def validate(self, element, context):
        if (not self.is_unusable(element) and
            getattr(element, self.a[1]).value == getattr(element, self.b[1]).value
           ):
            return self.valid
        self.note_error(
            element,
            self.message,
            context,
            substitutions={"a": self.a[0], "b": self.b[0]}
        )
        return self.invalid


class ProbablyAnEmailAddress(Validator):
    """
    A validator that fails with :attr:`message`, if the value of the validated
    e-mail is not a valid e-mail address.

    While this validator works on valid e-mail addresses it is not expected to
    pick up all bad e-mail addresses. The reason for this is that parsing
    e-mail addresses is very complicated, costly, probably would wrongly
    recognize some valid e-mail addresses as invalid and cannot determine if
    someone is reachable with this address.

    If you want to truly validate e-mail addresses you need to send an e-mail
    and wait for a response.
    """
    #: Message that is stored in the :attr:`Element.errors`.
    message = u"Must be a valid e-mail address."

    def validate(self, element, context):
        if not self.is_unusable(element) and u"@" in element.value:
            host = element.value.split(u"@", 1)[1]
            if u"." in host:
                parts = host.split(u".")
                if len(parts) >= 2:
                    return self.valid
        self.note_error(
            element,
            self.message,
            context
        )
        return self.invalid


class MatchesRegex(Validator):
    """
    Validator that fails with :attr:`message` if the value does not match the
    given `regex`.

    .. versionadded:: 2.1.0
    """
    #: The default regular expression used.
    regex = u''

    #: Message that is stored in :attr:`Element.errors`.
    message = u'Must be a valid value.'

    def __init__(self, regex=None):
        if regex is None:
            regex = self.regex
        self.regex = re.compile(regex)

    def validate(self, element, context):
        if not self.is_unusable(element) and self.regex.match(element.value):
            return self.valid
        self.note_error(element, self.message, context)
        return self.invalid


class IsURL(Validator):
    """
    Validator that fails with :attr:`message` if the value is not an absolute
    URL.

    .. versionadded:: 2.1.0
    """
    #: Message that is stored in :attr:`Element.errors`.
    message = u'Must be a URL.'

    def validate(self, element, context):
        if not self.is_unusable(element):
            parsed = urlparse(element.value)
            if parsed.scheme and parsed.netloc:
                return self.valid
        self.note_error(element, self.message, context)
        return self.invalid
