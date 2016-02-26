<%inherit file="../base.mako"/>

<h1>${review.source_url}</h1>
<p>
  <strong>Status:</strong> ${review.human_status}<br>
  <strong>Vote:</strong> ${review.human_vote} (+2 needed for approval)
</p>
% if review.description:
<p>${review.description}</p>
% endif

<hr>

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
    % if not review.latest_revision.tests:
    <tr>
      <td colspan="4">No tests have been run.</td>
    </tr>
    % else:
      % for test in review.latest_revision.tests:
      <tr>
        <td>${test.substrate}</td>
        <td>${test.status}</td>
        <td>
          % if test.results:
            <a href="${request.route_url('revision_tests_show', id=test.id)}">Test Results</a>
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
      action="${request.route_url('revision_test', id=review.latest_revision.id)}"
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

%for comment in review.latest_revision.comments:
<div class="panel panel-default">
  <div class="panel-heading">
    <div class="pull-right"><strong>Voted:</strong> ${comment.human_vote}</div>
    ${self.user_link(comment.user)} wrote ${self.human_date(comment.created_at)}
  </div>
  <div class="panel-body">
    ${comment.text}
  </div>
</div>
%endfor

<h3>Add Comment</h3>
% if request.user:
<form method="post"
      action="${request.route_url('revision_comment', id=review.latest_revision.id)}">
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

<h2>Reviewer's Checklist</h2>
<form id="policyForm">
<table class="table">
  <thead>
    <tr>
      <th>Description</th>
      <th>Unreviewed</th>
      <th>Pass</th>
      <th>Fail</th>
    </tr>
  </thead>
  <tbody>
    % for policy in policy_checklist:
    <% policy_check = review.latest_revision.get_policy_check_for(policy.id) %>
    <tr class="${'policyStatus{}'.format(policy_check.status) if policy_check else ''}">
      <td>${policy.description}</td>
      <td><input type="radio" name="policy${policy.id}" value="0"
            data-revision-id="${review.latest_revision.id}"
            data-policy-id="${policy.id}"
            ${"checked" if not policy_check or policy_check.unreviewed else ""}></td>
      <td><input type="radio" name="policy${policy.id}" value="1"
            data-revision-id="${review.latest_revision.id}"
            data-policy-id="${policy.id}"
            ${"checked" if policy_check and policy_check.passing else ""}></td>
      <td><input type="radio" name="policy${policy.id}" value="2"
            data-revision-id="${review.latest_revision.id}"
            data-policy-id="${policy.id}"
            ${"checked" if policy_check and policy_check.failing else ""}></td>
    </tr>
    % endfor
  </tbody>
</table>
</form>

<% diff_comments = review.latest_revision.diff_comments %>
% for change in review.get_diff(request.registry.settings).get_changes():
  <%
    change_diff_comments = {}
    for d in diff_comments:
        if d.filename == change.description:
            change_diff_comments.setdefault(d.line_start, []).append(d)

    diff = change.pygments_diff(change_diff_comments, context=True)
  %>
  % if diff:
  <h3>${change.description}</h3>
  ${diff | n}
  % endif
% endfor

<div id="revision-id">${review.latest_revision.id}</div>
