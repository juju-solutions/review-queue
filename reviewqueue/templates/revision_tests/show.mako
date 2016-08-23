<%inherit file="../base.mako"/>

<table class="table test-results">
  <thead>
    <tr>
      <th>Suite</th>
      <th>Test</th>
      <th>Return Code</th>
      <th>Duration</th>
      <th></th>
    </tr>
  <tbody>
  % for test in (revision_test.results or {}).get('tests', []):
    <tr>
      <td>${test['suite']}</td>
      <td>${test['test']}</td>
      <td>${test['returncode']}</td>
      <td>${test['duration']}</td>
      <td><a href="#" class="test-detail-toggle">Detail</a></td>
    </tr>
    <tr class="test-detail">
      <td colspan="5"><pre>${test['output']}</pre></td>
    </tr>
  % endfor
  </tbody>
</table>
