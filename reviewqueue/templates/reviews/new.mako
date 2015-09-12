<%inherit file="../base.mako"/>

<h1>Create New Review</h1>

<form action="/reviews/create" method="post">
  <div class="form-group">
    <label for="source_url">Source URL</label>
    <input type="text" class="form-control" id="source_url"
           name="source_url" placeholder="Source URL">
  </div>
</form>
