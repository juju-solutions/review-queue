<%inherit file="../base.mako"/>

<h1>Request a Review</h1>

<p>Before submitting an item for review, make sure that you have:</p>
<ul>
  <li>Reviewed <a href="https://jujucharms.com/docs/stable/authors-charm-policy">Charm store policy</a></li>
  <li>Uploaded and published your charm to the Charm store, e.g.:
    <div>
      <code>$ cd ~/charms/meteor</code><br>
      <code>$ charm push --publish . cs:~tvansteenburgh/meteor</code>
    </div>
  </li>
  <li>Set everyone=read pemissions on the charm, e.g.:
    <div>
      <code>$ charm change-perm cs:~tvansteenburgh/meteor --add-read=everyone</code>
    </div>
  </li>
</ul>

<form action="/reviews/create" method="post">
  <div class="form-group">
    <label for="source_url">Charm store url</label>
    <input type="text" class="form-control" id="source_url"
           name="source_url" placeholder="e.g. ~tvansteenburgh/meteor" required>
  </div>
  <div class="form-group">
    <label for="description">Description of changes (optional)</label>
    <textarea class="form-control" id="description" name="description"
      rows="5" placeholder=""></textarea>
  </div>
  <button type="submit" class="btn btn-default">Submit</button>
</form>
