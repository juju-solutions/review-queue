<%inherit file="../base.mako"/>

% if request.user and request.user.is_charmer:
<div class="pull-right">
  <form action="${request.route_url('review_update', id=review.id)}" method="post">
    <button type="submit" name="action" class="btn btn-default"
      value="close" title="Close this review without promulgation">Close</button>
    % if review.status == 'APPROVED':
    <button type="submit" name="action" class="btn btn-default"
      value="promulgate" title="Close this review and automatically promulgate the charm">Promulgate</button>
    % endif
  </form>
</div>
% endif

<h1>${review.source_url}</h1>
<p>
  <strong>Status:</strong> ${review.human_status}<br>
  <strong>Vote:</strong> ${review.human_vote} (+2 needed for approval)
</p>
% if review.description:
<p>${review.description}</p>
% endif

<hr>

<ul class="nav nav-tabs">
  % for i, rev in enumerate(review.revisions):
  <li role="presentation">
    <a href="${request.route_url('reviews_show', id=review.id, _query={'revision':rev.id})}">
      % if i == 0:
        <span title="${rev.shortname}">Latest revision</span>
      % else:
        ${rev.shortname}
      % endif
    </a>
  </li>
  % endfor
	% if request.user and (request.user == review.user or request.user.is_charmer):
  <li role="presentation" class="active">
		<a href="" title="Update this review with a new revision">Import a new revision</a>
	</li>
	% endif
</ul>

<h2>Add a new revision to this review</h2>
  <form action="${request.route_url('review_new_import', id=review.id)}" method="post">
  %if not new_revisions:
    <p>No new revisions to import.</p>
  %else:
    <div class="alert alert-info" role="alert">
      <strong>Note:</strong>
      Importing a revision will reset the current vote, reset the status to Needs Review,
      and kick off a new set of tests against the new revision.
    </div>
    <select name="revision">
      %for rev in new_revisions:
        <option>${rev}</option>
      %endfor
    </select>
    <button type="submit" class="btn btn-default">Import</button>
  %endif
</form>
