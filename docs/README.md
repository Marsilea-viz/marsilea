# Marsilea Documentation

The marsilea documentation is written in reStructuredText and built with Sphinx.

## Build

```shell
uv run task doc-build
# or
uv run task doc-clean-build
```

To serve the documentation, use:

```shell
uv run task doc-serve
```

## Writing Style

### Class

A name with a link to the class page.

```text
:class:`MyClass <module.MyClass>`
```

### Function or Method

Function or method name must end with brackets to indicate it can be called, 
and a link to the function or method page.

```text
:func:`myfunc() <module.myfunc>`
:meth:`mymethod() <module.MyClass.mymethod>`
```

### Attribute

Attribute name must prefix with a dot, with a link to the attribute page.

```text
:attr:`.myattr <module.MyClass.myattr>`
```

### Parameter

Parameter should be wrapped in the code directive

```text
:code:`myparam`
```