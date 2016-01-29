<%inherit file="../base.mako"/>

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
      <td>${h.arrow.get(r.updated_at or r.created_at).humanize()}</td>
      <td><a href="${request.route_url('users_show', nickname=r.user.nickname)}">${r.user.nickname}</a></td>
      <td>${r.age.days} d</td>
    </tr>
  %endfor
  </tbody>
</table>
