:html_theme.sidebar_secondary.remove:

.. meta::
   :description: Use Marsilea from AI coding assistants: install the official agentic
       skill, or point any assistant at the machine-readable llms.txt.

Use Marsilea with AI assistants
===============================

Marsilea ships two things for AI coding assistants: an official skill and an ``llms.txt`` that any assistant
can read.

Agentic skill
-----------------

Run these inside Claude Code:

.. code-block:: shell

   /plugin marketplace add Marsilea-viz/marsilea-skill
   /plugin install marsilea@marsilea-marketplace

The skill then activates on its own whenever you ask for a composable visualization,
a heatmap with annotations, an oncoprint, an UpSet plot. It will then write Marsilea code
against the current API instead of guessing.

Marsilea itself still has to be installed in the Python environment the assistant runs
code in:

.. code-block:: shell

   pip install marsilea

The skill lives in its own repository,
`Marsilea-viz/marsilea-skill <https://github.com/Marsilea-viz/marsilea-skill>`_; open an
issue there for skill-specific problems.

Any other assistant: llms.txt
-----------------------------

`llms.txt <https://llmstxt.org>`_ is a plain-text summary of a project written for
language models: what the library is, the core API, and a link per topic. Marsilea's
``llms.txt`` lives at

    https://marsilea.readthedocs.io/llms.txt

Paste that URL into an assistant that can fetch pages, or paste the file's contents into
the context window of one that cannot. It is short enough to include wholesale and covers
the canvases, the plotters, and one linked example per plot type.

Getting good results
--------------------

- Name the plot type you want ("oncoprint", "UpSet plot", "annotated heatmap"). Each one
  has a gallery example with full source, and assistants that fetch pages will find it.
- Say which side each piece belongs on. Marsilea's model is a main plot plus
  ``add_top`` / ``add_bottom`` / ``add_left`` / ``add_right``, so phrasing the request that
  way maps straight onto the API.
- If an assistant produces code for an older API, point it at
  the :doc:`API reference <api/index>` or the ``llms.txt`` above.
