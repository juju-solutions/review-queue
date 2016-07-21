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
    </tr>
  %endfor
  </tbody>
</table>
