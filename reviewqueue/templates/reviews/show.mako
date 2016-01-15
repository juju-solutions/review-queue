<%inherit file="../base.mako"/>

<h1>Review ${review.id}</h1>
<p>${review.source_url}</p>

% for change in review.get_diff(request.registry.settings).get_changes():
  <h3>${change.description}</h3>
  ${change.html_diff(context=True) | n}
% endfor
