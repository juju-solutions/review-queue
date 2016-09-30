$(function() {
  /*
   * Do ajax form submit when Policy items are checked
   */
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
   * Show next/prev links when hovering over diff comment
   */
  $('table.highlighttable').on('mouseenter', '.diff-comment', function() {
    var self = $(this);
    var prev_link = self.find('.prev-diff-comment');
    var next_link = self.find('.next-diff-comment');

    var all_comments = $('.diff-comment');
    var curr_index = all_comments.index(self);

    if (curr_index > 0) {
      prev_link.show()
    }

    if (curr_index + 1 < all_comments.length) {
      next_link.show()
    }
  });

  /*
   * Hide next/prev links when done hovering over diff comment
   */
  $('table.highlighttable').on('mouseleave', '.diff-comment', function() {
    var self = $(this);
    var prev_link = self.find('.prev-diff-comment');
    var next_link = self.find('.next-diff-comment');

    prev_link.hide()
    next_link.hide()
  });

  /*
   * Scroll to next diff comment
   */
  $('table.highlighttable').on('click', '.next-diff-comment', function(event) {
    event.preventDefault();

    var self = $(this);

    var all_comments = $('.diff-comment');
    var curr_index = all_comments.index(self.closest('.diff-comment'));
    var next_comment = all_comments.eq(curr_index + 1);

    if (next_comment.length) {
      $(document).scrollTop(next_comment.offset().top);
    }
  });

  /*
   * Scroll to prev diff comment
   */
  $('table.highlighttable').on('click', '.prev-diff-comment', function(event) {
    event.preventDefault();

    var self = $(this);

    var all_comments = $('.diff-comment');
    var curr_index = all_comments.index(self.closest('.diff-comment'));
    var prev_comment = all_comments.eq(curr_index - 1);

    if (prev_comment.length) {
      $(document).scrollTop(prev_comment.offset().top);
    }
  });

  /*
   * Show "add diff comment" button when hovering over a diff row
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

  /*
   * Remove "add diff comment" button when mouse leaves row
   */
  $('table.highlighttable tr').on('mouseleave', function() {
    var addDiffCommentBtn = $(this).find('.btn.add-diff-comment');
    addDiffCommentBtn.remove();
  });

  $('td.linenos .btn.add-diff-comment').on('mouseover', function(event) {
    $(this).remove();
  });

  /*
   * Insert/show new diff comment form
   */
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

  /*
   * Do ajax form submit for new diff comment
   */
  $('table.highlighttable').on('submit', '#diffCommentForm', function(event) {
    event.preventDefault();

    var form = $(this);
    var comment = form.find('textarea').val();
    var line_start = form.closest('tr').prev().find('td.linenos pre').text();
    var filename = form.closest('table').data('filename');
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

  /*
   * Remove row with diff comment form if Cancel clicked
   */
  $('table.highlighttable').on('click', '.btn.diff-comment-cancel', function(event) {
    $(this).closest('tr').remove();
  });

  /*
   * Show/hide test details
   */
  $('.test-detail-toggle').on('click', function(event) {
    $(this).closest('tr').next().toggle();
  });

  /*
   * Show/hide extra Policy detail
   */
  $('.glyphicon-info-sign').on('click', function(event) {
    $(this).closest('tr').next().toggle();
  });
});
