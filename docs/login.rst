
Login
=====

Here is an example of how you can login in a more advanced way, the login is a bit complicated since
people use tidalapi in lots of different ways.

See :class:`tidalapi.session` for additional information about the available fields and functions

Customizable login
-------------------------

This will use a desktop notification to show the link used for logging in, you can also open the browser directly,
display the code and tell the user to visit link.tidal.com and enter it, write it to a file, or send an email.

See :class:`tidalapi.session.LinkLogin` for the fields you can use to print the link

.. testsetup::

    import tests.conftest
    import requests
    import sys
    session = tests.conftest.login(requests.Session())
    printer = lambda x: print(x, file=sys.stderr)

.. testcode::

    from plyer import notification

    login, future = session.login_oauth()

    notification.notify("Open the URL to log in", login.verification_uri_complete)

    future.result()
    print(session.check_login())

.. testoutput::
    :hide:

    True

Simple login
------------
This will print the link, and then wait for the login future to complete, but it's not very flexible

.. testcode::

    # The function is print by default, but you can use anything, here we do it to avoid the print being swallowed
    session.login_oauth_simple(function=printer)
    print(session.check_login())

.. testoutput::
    :hide:

    True

Storing login credentials
-------------------------

In order to store the login details, you need to store these variables in a secure place

.. testcode::

    token_type = session.token_type
    access_token = session.access_token
    refresh_token = session.refresh_token # Not needed if you don't care about refreshing
    expiry_time = session.expiry_time


Loading login credentials
-------------------------

Using the variables from the above snippet, we can login using stored credentials.
This could for example be used to login on your computer, and then load the credentials in the cloud.

.. testcode::

    print(session.load_oauth_session(token_type, access_token, refresh_token, expiry_time))

.. testoutput::
    :hide:

    True
