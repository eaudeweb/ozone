Introduction
============

Veyon is an application that lets you monitor and control a group of computers (e.g. classrooms) on a central computer (e.g. an instructor's computer) and use various features and modes.



.. tabs::

   .. tab:: Mac OS

      If you are having trouble on OS X Mavericks
      (or possibly other versions of OS X) with building ``lxml``,
      you probably might need to use Homebrew_ to ``brew install libxml2``,
      and invoke the install with::

          CFLAGS=-I/usr/local/opt/libxml2/include/libxml2 \
          LDFLAGS=-L/usr/local/opt/libxml2/lib \
          pip install -r requirements.txt

   .. tab:: Ubuntu

      Install::

         sudo apt-get install build-essential
         sudo apt-get install python-dev python-pip python-setuptools
         sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

      If you don't have redis installed yet, you can do it with::

         sudo apt-get install redis-server

   .. tab:: CentOS/RHEL 7

      Install::
      
         sudo yum install python-devel python-pip libxml2-devel libxslt-devel

   .. tab:: Other OS

      On other operating systems no further dependencies are required,
      or you need to find the proper equivalent libraries.




Topics, Sidebars, and Rubrics
-----------------------------

.. sidebar:: Sidebar Title
   :subtitle: Optional Subtitle

   This is a sidebar.  It is for text outside the flow of the main
   text.

   .. rubric:: This is a rubric inside a sidebar

   Sidebars often appears beside the main text with a border and
   background color.

.. topic:: Topic Title

   This is a topic.

.. rubric:: This is a rubric

