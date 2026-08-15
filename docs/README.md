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

## llms.txt

`source/_extra/llms.txt` is copied verbatim into each version's output by `html_extra_path`.
It is hand-written: when the API or the gallery changes, update it in the same PR.

Assistants look for it at the domain root, <https://marsilea.readthedocs.io/llms.txt>. Read
the Docs serves that natively — no redirect needed — but only from the project's **default
version**, which is `stable`, which tracks the latest tag. So a change to `llms.txt` does not
reach the canonical URL until it lands in a release; until then it is only visible at
`/en/latest/llms.txt`. Check with:

    curl -sI https://marsilea.readthedocs.io/llms.txt | grep x-rtd-path

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