<%inherit file="../base.mako"/>

<% diff_comments = revision.diff_comments %>
<% diff, fetch_error = revision.get_diff(request.registry.settings, prior_revision=diff_revision) %>

% if fetch_error:
  <div class='alert alert-danger'>
    <p>An error occured while fetching the charm source for this review.</p>
    <p><strong>Command:</strong> <code>${fetch_error.cmd}</code></p>
    <p><strong>Error: </strong><code>${str(fetch_error)}</code></p>
    % if fetch_error.hint:
      <p><strong>Possible Solution: </strong>${fetch_error.hint}</p>
    % endif
  </div>
% endif

% if request.user and request.user.is_charmer:
<div class="pull-right">
  <form action="${request.route_url('review_update', id=review.id)}" method="post">
    % if review.status != 'CLOSED':
      % if review.status == 'APPROVED':
      <button type="submit" name="action" class="btn btn-positive"
        value="promulgate" title="Close this review and automatically promulgate the charm">Promulgate</button>
      % endif
      <button type="submit" name="action" class="btn btn-negative"
        value="close" title="Close this review without promulgation">Close</button>
    % else:
      <button type="submit" name="action" class="btn btn-primary"
        value="reopen" title="Reopen this review">Reopen</button>
    % endif
  </form>
</div>
% endif

<h1>
  <img src="${review.icon_url(request.registry.settings)}" class="charm-icon" />
  ${review.source_url}
</h1>

<div class="row">
  <div class="col-md-6">
    <p>
    <strong>Owner:</strong> <a href="${request.route_url('users_show', nickname=review.user.nickname)}">${review.user.nickname}</a><br>
    <strong>Status:</strong> ${review.human_status}<br>
    <strong>Vote:</strong> ${review.human_vote} (+2 needed for approval)<br>
    </p>
  </div>
  <div class="col-md-6">
    <p>
    <strong>CPP?:</strong> ${'Yes' if review.is_cpp else 'No'}<br>
    <strong>OIL?:</strong> ${'Yes' if review.is_oil else 'No'}<br>
    </p>
  </div>
</div>

% if review.description:
<p>${review.description | h.linesplit}</p>
% endif

<hr>

<ul class="nav nav-tabs">
  % for i, rev in enumerate(review.revisions):
  <li role="presentation" class="${'active' if rev == revision else ''}">
    <a href="${request.route_url('reviews_show', id=review.id, _query={'revision':rev.id})}">${rev.shortname}</a>
  </li>
  % endfor
	% if request.user and (request.user == review.user or request.user.is_charmer):
  <li role="presentation">
		<a href="${request.route_url('review_show_import', id=review.id)}" title="Update this review with a new revision">Import a new revision</a>
	</li>
	% endif
</ul>

<h2>Tests</h2>
<table class="table">
  <thead>
    <tr>
      <th>Substrate</th>
      <th>Status</th>
      <th>Results</th>
      <th>Last Updated</th>
    </tr>
  </thead>
  <tbody>
    % if not revision.tests:
    <tr>
      <td colspan="4">No tests have been run.</td>
    </tr>
    % else:
      % for test in revision.tests:
      <tr>
        <td>${test.substrate}</td>
        <td>${test.status}</td>
        <td>
          % if test.results:
            <a href="${request.route_url('revision_tests_show', id=test.id)}">Test Results</a>
          % elif test.url:
            <a href="${test.url}console">${test.url}console</a>
          % endif
        </td>
        <td>${self.human_date(test.updated_at or test.created_at)}</td>
      </tr>
      % endfor
    % endif
  </tbody>
</table>

% if request.user and request.user.is_charmer:
<form method="post"
      action="${request.route_url('revision_test', id=revision.id)}"
      class="form-inline">
  <select name="substrate" class="form-control">
    % for substrate in substrates:
      <option value="${substrate}">${substrate}</option>
    % endfor
    <option value="all">All</option>
  </select>
    <button type="submit" class="btn btn-default">Start Test</button>
</form>
% endif

<hr>

%for comment in revision.comments:
<div class="panel panel-default">
  <div class="panel-heading">
    <div class="pull-right"><strong>Voted:</strong> ${comment.human_vote}</div>
    ${self.user_link(comment.user)} wrote ${self.human_date(comment.created_at)}
  </div>
  <div class="panel-body">
    ${comment.text | h.linesplit}
  </div>
</div>
%endfor

<h3>Add Comment</h3>
% if request.user:
<form method="post"
      action="${request.route_url('revision_comment', id=revision.id)}">
  <div class="form-group">
    <textarea name="comment" class="form-control" rows="5" required></textarea>
  </div>
  <div class="form-inline">
    <div class="form-group">
      % if review.user == request.user:
        <input type="hidden" name="vote" value="0">
        <label for="status">Status</label>
        <select name="status" class="form-control">
          ${self.status_option('NEEDS_FIXING', review)}
          ${self.status_option('NEEDS_REVIEW', review)}
        </select>
      % else:
      <label for="vote">Vote</label>
      <select name="vote" class="form-control">
        % if request.user and request.user.is_charmer:
          <option value="2">Accept (+2)</option>
        % endif
        <option value="1">Approve (+1)</option>
        <option value="0" selected>Abstain (comment only)</option>
        <option value="-1">Disapprove (-1)</option>
        % if request.user and request.user.is_charmer:
          <option value="-2">Reject (-2)</option>
        % endif
      </select>
      % endif
    </div>
    <button type="submit" class="btn btn-default pull-right">Save Comment</button>
  </div>
</form>
% else:
<p><a href="/login/openid?openid_identifier=http://login.ubuntu.com">Login</a> to comment/vote on this review.</p>
% endif

<hr>

<h2>Policy Checklist</h2>
<form id="policyForm">
<table class="table">
  <thead>
    <tr>
      <th>Description</th>
      <th>Unreviewed</th>
      <th>Pass</th>
      <th>Fail</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    % for cat in policy_categories:
      <tr>
        <td colspan="5"><h3>${cat.name}</h3></td>
      </tr>
      % for policy, policy_check in cat.get_review_policies(review):
      <tr class="${'policyStatus{}'.format(policy_check.status) if policy_check else ''}">
        <td>
          ${policy.description | n}
          % if policy.tip:
            <span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>
          % endif
        </td>
        <td><input type="radio" name="policy${policy.id}" value="0"
              data-revision-id="${revision.id}"
              data-policy-id="${policy.id}"
              ${"checked" if not policy_check or policy_check.unreviewed else ""}
              ${'disabled' if (not request.user or request.user == review.user) else ''}></td>
        <td><input type="radio" name="policy${policy.id}" value="1"
              data-revision-id="${revision.id}"
              data-policy-id="${policy.id}"
              ${"checked" if policy_check and policy_check.passing else ""}
              ${'disabled' if (not request.user or request.user == review.user) else ''}></td>
        <td>
          % if policy.required:
            <input type="radio" name="policy${policy.id}" value="2"
              data-revision-id="${revision.id}"
              data-policy-id="${policy.id}"
              ${"checked" if policy_check and policy_check.failing else ""}
              ${'disabled' if (not request.user or request.user == review.user) else ''}></td>
          % endif
        </td>
        <td class="small" id="policy-${policy.id}-user">
          <% title = '{}, {}'.format(policy_check.revision.shortname, h.arrow.get(policy_check.updated_at or policy_check.created_at).humanize()) if policy_check else '' %>
          <span title="${title}">
            ${policy_check.user.nickname if policy_check else ''}
          </span>
        </td>
      </tr>
      % if policy.tip:
      <tr style="display: none">
        <td colspan="5" class="bg-warning">${policy.tip | n}</td>
      </tr>
      % endif
      % endfor
    % endfor
  </tbody>
</table>
</form>

<hr>

% if diff:
  <% changes = diff.get_changes() %>

  % if revision.prior:
  <div class="pull-right">
    % if not diff_revision:
      All changes | <a href="${request.route_url('reviews_show', id=review.id, _query={'revision':revision.id, 'diff_revision':revision.prior.id})}">Changes since last revision</a>
    % else:
      <a href="${request.route_url('reviews_show', id=review.id, _query={'revision':revision.id})}">All changes</a> | Changes since last revision
    % endif
  </div>
  % endif

  <h2>Source Diff</h2>
  <div class="row">
    <div class="col-md-6">
      <div class="panel panel-default">
        <a name="file-index"></a>
        <div class="panel-heading">
          <h3 class="panel-title">Files changed <span class="badge">${len(changes)}</span></h3>
        </div>
        <div class="panel-body">
          <ul class="list-unstyled">
          % for change in changes:
            <li><a href="#${id(change)}">${change.description}</a></li>
          % endfor
          </ul>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="panel panel-default">
        <div class="panel-heading">
          <h3 class="panel-title">Inline diff comments <span class="badge">${len(diff_comments)}</span></h3>
        </div>
        <div class="panel-body">
          % if not diff_comments:
            <p>No comments yet.</p>
          % else:
            <ul class="list-unstyled">
            % for comment in diff_comments:
              <li><a href="#${id(comment)}" class="truncate">${comment.text}</a></li>
            % endfor
            </ul>
          % endif
        </div>
      </div>
    </div>
  </div>

  % for change in changes:
    <%
      change_diff_comments = {}
      for d in diff_comments:
          if d.filename == change.description:
              change_diff_comments.setdefault(d.line_start, []).append(d)

      diff = change.pygments_diff(change_diff_comments, context=True)
    %>
    % if diff:
    <div>
      <a href="#file-index" class="pull-right">Back to file index</a>
      <h4><a name="${id(change)}"></a><a href="#${id(change)}">${change.description}</a></h4>
      ${diff | n}
    </div>
    % endif
  % endfor
% endif

<div id="revision-id" style="display:none">${revision.id}</div>
<div id="user-id" style="display:none">${request.user.id if request.user else ''}</div>
