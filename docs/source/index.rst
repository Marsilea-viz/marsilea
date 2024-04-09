:html_theme.sidebar_secondary.remove:


.. image:: https://raw.githubusercontent.com/Marsilea-viz/marsilea/main/img/banner-blue.jpg
    :alt: Marsilea banner
    :align: center
    :width: 600px

.. raw:: html

        <div id="space" style="text-align: center; margin-top: 20px; margin-bottom: 20px"></div>

Marsilea: Declarative creation of composable visualization
==========================================================


.. grid:: 1 1 2 2



    .. grid-item::

        Marsilea is a Python library for creating composable visualizations in a declarative way.
        It is built on top of Matplotlib and provides a high-level API for you to puzzle different visualizations
        together like logo.

        .. card :: Related Projects
            :shadow: none

            - Easy legend creation: `legendkit <https://github.com/Marsilea-viz/legendkit/>`_ | `Documentation <https://legendkit.rtfd.io/>`_
            - Font management: `mpl-fontkit <https://github.com/Marsilea-viz/mpl-fontkit/>`_

    .. grid-item::

        .. image:: img/code_example.png
            :align: center
            :width: 600px


Installation
------------

Install via pip:

.. code-block:: shell

   $ pip install marsilea


Documentation Sections
----------------------

.. grid:: 2 2 4 4

    .. grid-item-card:: :octicon:`repo;4em;sd-text-primary`
        :shadow: none
        :text-align: center
        :link: tutorial/index.html
        :margin: 1 1 0 0

        **Tutorial**

    .. grid-item-card:: :octicon:`device-camera;4em;sd-text-primary`
        :shadow: none
        :text-align: center
        :link: examples/index.html
        :margin: 1 1 0 0

        **Gallery**

    .. grid-item-card:: :octicon:`archive;4em;sd-text-primary`
        :shadow: none
        :text-align: center
        :link: api/index.html
        :margin: 1 1 0 0

        **API Reference**

    .. grid-item-card:: :octicon:`question;4em;sd-text-primary`
        :shadow: none
        :text-align: center
        :link: how-to.html
        :margin: 1 1 0 0

        **How-To**


.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   Tutorial <tutorial/index>
   Gallery <examples/index>
   API <api/index>
   Installation <installation>
   How-To <how_to/index>
