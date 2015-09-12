<!DOCTYPE html>

<html>
  <head>
    <title>Review Queue</title>
    <link href='http://fonts.googleapis.com/css?family=Ubuntu:300,400,700' rel='stylesheet' type='text/css'>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="/static/css/app.css">
  </head>
  <body>
    <nav class="navbar navbar-default navbar-static-top">
      <div class="container">
        <div class="navbar-header">
          <a class="navbar-brand" href="/">Review Queue</a>
        </div>

        <ul class="nav navbar-nav">
        %if request.user:
          <li><a href="${request.route_url('reviews_new')}">Request Review</a></li>
        %endif
        </ul>

        <div class="navbar-text navbar-right">
        %if request.user:
          <a href="${request.route_url('users_show', nickname=request.user.nickname)}" class="navbar-link">${request.user.fullname}</a> |
          <a href="${request.route_url('logout')}">Logout</a>
        %else:
          <a href="/login/openid?openid_identifier=http://login.ubuntu.com">Login</a>
        %endif
        </div>
      </div>
    </nav>

    <div class="container">
      ${next.body()}
    </div>

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>
  </body>
</html>
