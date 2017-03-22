<%inherit file="../base.mako"/>

<h1>Request a Review</h1>

<p>Before submitting an item for review, make sure that you:</p>
<ul>
  <li>Reviewed <a href="https://jujucharms.com/docs/stable/authors-charm-policy">Charm store policy</a></li>
  <li>Uploaded and published your charm to the Charm store, e.g.:
    <div>
      <code>$ cd ~/charms/meteor</code><br>
      <code>$ charm push . cs:~tvansteenburgh/meteor</code><br>
      <code>$ charm release cs:~tvansteenburgh/meteor-0</code>
    </div>
  </li>
  <li>Set everyone=read pemissions on the charm, e.g.:
    <div>
      <code>$ charm grant cs:~tvansteenburgh/meteor everyone</code>
    </div>
  </li>
  <li>If your charm uses terms, release all terms using the <code>charm release-term</code>
    command (<a href="https://jujucharms.com/docs/2.0/developer-terms#releasing-terms">docs</a>).
  </li>
  <li>Are the owner of the charm, or a member of the team that owns the charm</li>
</ul>

<p>You may submit a charm url with or without a revision number. If a
revision number is included and the charm is not yet promulgated, the
revision must be the latest in the stable channel.<p>

<p>If a revision is not specified, the latest revision in the stable
channel (for a non-promulgated charm) or the edge channel (for
a promulgated charm) will be used.<p>

%if validation_result and 'error' in validation_result:
<div class='alert alert-danger'>
  %if 'NotFound' == validation_result['error']:
    Couldn't find ${validation_result['source_url']} in the Charm Store.
    Have you granted read permissions (see above)?
  %elif 'NotOwner' == validation_result['error']:
    Sorry, to request a review for this charm, you must be the owner of
    the charm, or a member of the team that owns the charm.
  %elif 'NotLatestRevision' == validation_result['error']:
    A review of a non-promulgated charm must be against the latest revision
    in the stable channel. Try removing the revision from the url.
  %endif
</div>
%endif

<form action="/reviews/create" method="post">
  <div class="form-group">
    <label for="source_url">Charm store url</label>
    <input type="text" class="form-control" id="source_url"
           name="source_url"
           value="${request.params.get('source_url') or ''}"
           placeholder="e.g. ~tvansteenburgh/meteor or ~tvansteenburgh/meteor-1" required>
  </div>
  <div class="form-group">
    <label for="description">Description of changes (optional)</label>
    <textarea class="form-control" id="description" name="description"
      rows="5" placeholder="">${request.params.get('description') or ''}</textarea>
  </div>
  <div class="checkbox">
    <label>
      <input type="checkbox" name="cpp"
        ${'checked' if request.params.get('cpp') else ''}> CPP member?
    </label>
  </div>
  <div class="checkbox">
    <label>
      <input type="checkbox" name="oil"
        ${'checked' if request.params.get('oil') else ''}> OIL member?
    </label>
  </div>
  <button type="submit" class="btn btn-default">Submit</button>
</form>
