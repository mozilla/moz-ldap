MozLDAP
=======

This app aims to wrap the Mozilla LDAP so you can ask simple questions
about users in LDAP by a straight forwards RESTful API.


License
-------
MPL2


Running tests
-------------

You need to force a new DB every time since we're using sqlite's
`:memory:`.

    FORCE_DB=1 python manage.py test
