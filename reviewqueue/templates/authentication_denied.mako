<%inherit file="base.mako"/>

% if reason == 'Missing Email':
<h1>In order to log in you must share your email address.</h1>
<img src="${request.static_url('reviewqueue:static/images/ubuntu_login_example.png')}"
     style="border: solid 1px #eee">
% else:
<h1>Authentication failed, please try again.</h1>
% endif
