<%inherit file="../base.mako"/>

<h1>Request a Review</h1>

<form action="/reviews/create" method="post">
  <div class="form-group">
    <label for="source_url">Source URL</label>
    <input type="text" class="form-control" id="source_url"
           name="source_url" placeholder="Source URL" required>
  </div>
  <div class="form-group">
    <label for="description">Description</label>
    <textarea class="form-control" id="description" name="description"
      rows="5" placeholder="Optional description of changes"></textarea>
  </div>
  <button type="submit" class="btn btn-default">Submit</button>
</form>
