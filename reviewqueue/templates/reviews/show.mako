<%inherit file="../base.mako"/>

<h1>${review.source_url}</h1>

<h2>Tests</h2>
<table class="table">
  <thead>
    <tr>
      <th>Substrate</th>
      <th>Status</th>
      <th>Results</th>
      <th>Submitted</th>
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
          % if test.url:
            <a href="${test.url}console">${test.url}console</a>
          % endif
        </td>
        <td>${test.updated_at}</td>
      </tr>
      % endfor
    % endif
  </tbody>
</table>

% if request.user and request.user.is_charmer:
<h3>New Test</h3>
<form method="post"
      action="${request.route_url('revision_test', id=review.latest_revision.id)}">
  <select name="substrate">
    % for substrate in substrates:
      <option value="${substrate}">${substrate}</option>
    % endfor
    <option value="all">All</option>
  </select>
  <input type="submit" value="Start Test">
</form>
% endif

<h2>Comments/Votes<h2>
%for comment in review.latest_revision.comments:
  <p>${comment.text}</p>
  <p>${comment.vote}</p>
%endfor
<h3>Add Comment</h3>
<form method="post"
      action="${request.route_url('revision_comment', id=review.latest_revision.id)}">
  <textarea name="comment"></textarea>
  <br>Vote:
  <select name="vote">
    % if request.user and request.user.is_charmer:
      <option value="2">Accept (+2)</option>
    % endif
    <option value="1">Approve (+1)</option>
    <option value="0" selected>Abstain (0)</option>
    <option value="-1">Disapprove (-1)</option>
    % if request.user and request.user.is_charmer:
      <option value="-2">Reject (-2)</option>
    % endif
  </select>
  <br><input type="submit" value="Save Comment">
</form>

<h2>Review Checklist</h2>
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

<h2>Diff</h2>
% for change in review.get_diff(request.registry.settings).get_changes():
  <h3>${change.description}</h3>
  ${change.pygments_diff(context=True) | n}
% endfor
