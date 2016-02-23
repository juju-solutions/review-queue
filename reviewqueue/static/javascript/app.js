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
      }
    });
  });

  $('table.highlighttable tr').on('mouseenter', function() {
    var self = $(this);
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
});
