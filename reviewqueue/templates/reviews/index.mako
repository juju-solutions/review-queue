<%inherit file="../base.mako"/>

<div class="pull-right btn-launch btn-group">
  %if request.user:
    <a class="btn btn-primary" href="${request.route_url('reviews_new')}">Request a Review</a>
  %endif
</div>
<h1>Reviews</h1>
<table class="table">
  <thead>
    <tr>
      <th>Source</th>
      <th>Status</th>
      <th>Updated</th>
      <th>Owner</th>
      <th>Age</th>
      <th>Progress</th>
    </tr>
  </thead>
  <tbody>
  %for r in reviews:
    <tr>
      <td><a href="${request.route_url('reviews_show', id=r.id)}">${r.source_url}</a></td>
      <td>${r.human_status}</td>
      <td>${self.human_date(r.updated_at or r.created_at)}</td>
      <td><a href="${request.route_url('users_show', nickname=r.user.nickname)}">${r.user.nickname}</a></td>
      <td>${r.age.days} d</td>
      <th>${progress(r.get_progress())}</th>
    </tr>
  %endfor
  </tbody>
</table>

<%def name="progress(d)">
  <%
  from math import floor
  pass_count = d['passing']
  fail_count = d['failing']
  total_count = d['total']
  pass_percent = (pass_count * 1.0 / total_count) * 100
  fail_percent = (fail_count * 1.0 / total_count) * 100
  %>
	<div class="progress" title="${total_count} total policy checks">
		<div class="progress-bar progress-bar-success"
      style="width: ${pass_percent}%"
      title="${pass_count} passing (${int(floor(pass_percent))}%)">
		</div>
		<div class="progress-bar progress-bar-danger"
      style="width: ${fail_percent}%"
      title="${fail_count} failing (${int(floor(fail_percent))}%)">
		</div>
	</div>
</%def>
