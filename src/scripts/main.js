import $ from 'jquery'
import 'select2'
import 'lazysizes'

// FIXME this causes the browser to freeze because there are so many elements
$('form.thumb').one('click', (evt) => {
  const $elem = $(evt.currentTarget)
  $elem.find('select').select2({
    tags: true
  })
  // User intended to edit keywords
  if (evt.target.tagName === 'SELECT') {
    $elem.find('input.select2-search__field').focus()
  }
})

$('form').on('submit', function (evt) {
  evt.preventDefault()

  const $form = $(this)
  console.log($form.attr('action'), $form.serialize())
  $.post($form.attr('action'), $form.serialize())
  .done(function (data) {
    const $button = $form.find('button')
    $button.text('saved!').addClass('success')
    setTimeout(() => {
      $button.text('save').removeClass('success')
    }, 2000)
  })
  .fail(function (xhr, textStatus, message) {
    window.alert(message)
  })
})
