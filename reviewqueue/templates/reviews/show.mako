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
<h2>New Test</h2>
<form method="post"
      action="${request.route_url('test_revision', id=review.latest_revision.id)}">
  <select name="substrate">
    % for substrate in substrates:
      <option value="${substrate}">${substrate}</option>
    % endfor
    <option value="all">All</option>
  </select>
  <input type="submit" value="Start Test">
</form>
% endif

<h2>Diff</h2>
% for change in review.get_diff(request.registry.settings).get_changes():
  <h3>${change.description}</h3>
  ${change.html_diff(context=True) | n}
% endfor

