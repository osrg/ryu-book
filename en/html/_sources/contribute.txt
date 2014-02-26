.. _ch_contribute:

Contribution
============

One of the appeals of open source software is that you can participate in the development process yourself. This section introduces how to participate in the development of Ryu.

Development structure
---------------------

Development of Ryu has been conducted around a mailing list. Let's begin by to joining the mailing list.

https://lists.sourceforge.net/lists/listinfo/ryu-devel

Information exchange on the mailing list is primarily done in English. When you have questions such as how to use, or if you encounter behavior that seems like a bug, do not hesitate to send mail. Because using open source software itself is an important contribution to the project.

Development Environment
-----------------------

This section describes the necessary environment and points to consider during Ryu development.

Python
^^^^^^

Ryu supports Python 2.6 and later. Therefore, do not use syntax only available in Python 2.7.

Python 3.0 or later are not supported at the moment. However, it's best to keep in mind to write source code that avoids future changes as much as possible.

Coding Style
^^^^^^^^^^^^

Ryu source code is in compliance with the PEP8 coding style. When sending a patch, which will be described later, please make sure in advance that the content is in compliance with PEP8.

http://www.python.org/dev/peps/pep-0008/

To check whether source code is compliant with PEP8, a checker is available along with the script introduced in the test section.

https://pypi.python.org/pypi/pep8

Test
^^^^

Ryu has some automated testing, but the simplest and most frequently used one is a unit test that is completed only by Ryu. When sending a patch, which will be described later, please make sure in advance that the execution of unit tests do not fail due to changes made. As for newly added source code, it is desirable to describe unit tests as much as possible.

.. rst-class:: console

::

   $ cd ryu/
   $ ./run_tests.sh

Sending a Patch
---------------

When you want to change the source code repository due to adding features or bug fixes, create a patch of the changed contents and sent it to the mailing list. It is desirable to discuss major changes on the mailing list in advance.

.. NOTE::
   A repository of Ryu source code exists on GitHub, but please note that this is not a development process using a pull request.

For the format of a patch you're going to send, the style used in the development of the Linux kernel is expected. In this section we will show you an example of sending a patch of the same style to the mailing list, but please refer to related documents for more information.

http://lxr.linux.no/linux/Documentation/SubmittingPatches

The following is the procedure.

1 Check out the source code

 First, check out the Ryu source code.
 You may also create a working repository for yourself by forking the source code on GitHub, but the example uses the exact original for the sake of simplicity.

   ``$ git clone https://github.com/osrg/ryu.git``
   ``$ cd ryu/``

2 Make changes to the source code

 Make the necessary changes to the Ryu source code. 
 Let's commit the changes at the break of work.

   ``$ git commit -a``

3 Creating a patch

 Create a patch of the difference between the changes. 
 Please do not forget to include a Signed-off-by: line in the patch. 
 This signature will be the declaration that for the patch you submitted there are problems with the open-source software license.

   ``$ git format-patch origin -s``

4 Sending the patch

 After confirming that the content of the completed patch is correct, send it to the mailing list. 
 You can send directly by a mailer, but you can also handle interactively by using git-send-email(1).

   ``$ git send-email 0001-sample.patch``

5 Wait for a response

 Wait for a response to the patch.
 It may be taken as it is, but if issues are pointed out you'll need to correct the contents and send it again.
