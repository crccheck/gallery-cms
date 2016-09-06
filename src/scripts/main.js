import $ from 'jquery'
import 'select2'

// FIXME this causes the browser to freeze because there are so many elements
$('form.thumb').one('click', (evt) => {
  console.log(evt)
  const $elem = $(evt.currentTarget)
  $elem.find('select').select2({
    tags: true
  })
  // User intended to edit keywords
  if (evt.target.tagName === 'SELECT') {
    $elem.find('input.select2-search__field').focus()
  }
})
