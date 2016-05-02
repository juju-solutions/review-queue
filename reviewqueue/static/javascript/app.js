$(function() {
  $('#policyForm input[type=radio]').on('change', function() {
    var self = $(this);

    var radio_name = self.attr('name');
    var revision_id = self.data('revision-id');
    var policy_id = self.data('policy-id');
    var radio_value = $('#policyForm input[name=' + radio_name +']:checked').val();

    var parent = self.closest('tr');
    parent.removeClass('policyStatus0')
      .removeClass('policyStatus1')
      .removeClass('policyStatus2')
      .addClass('policyStatus' + radio_value);

    $.post("/revisions/" + revision_id + "/policy", {
      policy_id: policy_id,
      status: radio_value
    }).done(function(data) {
      if(data.error) {
      } else {
        html = '<span title="' + data.revision + ', ' + data.timestamp + '">' + data.user + '</span>';
        $('#policy-' + policy_id + '-user').html(html);
      }
    });
  });

  /*
   * Showe "add diff comment" button when hovering over a diff row
   */
  $('table.highlighttable tr').on('mouseenter', function() {
    var self = $(this);

    // abort if not logged in
    if ($('#user-id').text().length === 0) {
      return;
    }

    // abort if we're already showing a comment box for this row
    if (self.next().find('#diffCommentForm').length) {
      return;
    }

    var td = self.find('td.linenos');

    var btn_html =
      '<button type="button" class="btn btn-primary btn-xs add-diff-comment">' +
      '  <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>' +
      '</button>';
    btn = $(btn_html);
    td.append(btn);
  });

  $('table.highlighttable tr').on('mouseleave', function() {
    var addDiffCommentBtn = $(this).find('.btn.add-diff-comment');
    addDiffCommentBtn.remove();
  });

  $('td.linenos .btn.add-diff-comment').on('mouseover', function(event) {
    $(this).remove();
  });

  $('td.linenos').on('click', '.btn.add-diff-comment', function(event) {
    var tr = $(this).closest('tr');
    $(this).remove();
    var newRow =
      `<tr><td colspan="2" class="diff-comment">
        <form id="diffCommentForm">
          <div class="form-group">
            <textarea autofocus name="comment" class="form-control" rows="5" required></textarea>
          </div>
          <div class="form-inline">
            <button type="submit" class="btn btn-primary">Save</button>
            <button class="btn btn-default diff-comment-cancel">Cancel</button>
          </div>
        </form>
      </td></tr>`;
    tr.after(newRow);
    tr.next().find('textarea').focus();
  });

  $('table.highlighttable').on('submit', '#diffCommentForm', function(event) {
    event.preventDefault();

    var form = $(this);
    var comment = form.find('textarea').val();
    var line_start = form.closest('tr').prev().find('td.linenos pre').text();
    var filename = form.closest('table').prev('h3').text();
    var revision_id = $('#revision-id').text();

    $.post("/revisions/" + revision_id + "/diff_comment", {
      comment: comment,
      line_start: line_start,
      filename: filename
    }).done(function(data) {
      if(data.error) {
      } else {
        form.closest('tr').replaceWith(data.html);
      }
    });
  });

  $('table.highlighttable').on('click', '.btn.diff-comment-cancel', function(event) {
    $(this).closest('tr').remove();
  });

  $('.test-detail-toggle').on('click', function(event) {
    $(this).closest('tr').next().toggle();
  });

  $('.glyphicon-info-sign').on('click', function(event) {
    $(this).closest('tr').next().toggle();
  });
});
