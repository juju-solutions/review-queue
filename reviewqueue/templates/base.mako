<!DOCTYPE html>

<html>
  <head>
    <title>Review Queue</title>
    <link href='http://fonts.googleapis.com/css?family=Ubuntu:300,400,700' rel='stylesheet' type='text/css'>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="${request.static_url('reviewqueue:static/css/pygments.formatters.HtmlFormatter.css')}">
    <link rel="stylesheet" href="${request.static_url('reviewqueue:static/css/app.css')}">
  </head>
  <body>
    <nav class="navbar navbar-default navbar-static-top">
      <div class="container">
        <div class="navbar-header">
          <a class="navbar-brand" href="/">Review Queue</a>
        </div>

        <ul class="nav navbar-nav">
        %if request.user:
          <li><a href="${request.route_url('reviews_new')}">Request a Review</a></li>
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

    <footer class="footer">
      <div class="container">
        <p class="text-muted">
          <a href="://github.com/tvansteenburgh/review-queue">github repo</a> |
          <a href="://github.com/tvansteenburgh/review-queue/issues">report a bug</a> |
          <a href="://github.com/tvansteenburgh/review-queue/issues">request a feature</a>
        </p>
      </div>
    </footer>

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>
    <script src="${request.static_url('reviewqueue:static/javascript/app.js')}"></script>
  </body>
</html>

<%def name="human_date(date)">
  <span title="${date}">${h.arrow.get(date).humanize()}</span>
</%def>

<%def name="status_option(status, review)">
  <option value="${status}"
    ${"selected" if review.status == status else ""}>
    ${"Leave as " if review.status == status else "Update to "}${h.human_status(status)}
  </option>
</%def>

<%def name="user_link(user)">
  <a href="https://launchpad.net/~${user.nickname}">${user.nickname}</a>
</%def>
