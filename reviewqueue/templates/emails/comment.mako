<% from reviewqueue import helpers as h %>

${comment.user.fullname} said:

<blockquote>${comment.text | h.linesplit}</blockquote>

Current Vote: ${comment.revision.review.vote}<br>
Current Staus: ${comment.revision.review.status}<br>

<p>
Go to Review: ${request.registry.settings['base_url']}/reviews/${comment.revision.review.id}
</p>
