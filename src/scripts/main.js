import $ from 'jquery'
import _uniq from 'lodash/uniq'
import {crc32} from 'js-crc'
import 'lazysizes'
import 'select2'

function getKeywords () {
  return _uniq($('.thumb .keyword').toArray().map((x) => x.innerHTML)).sort()
}

let allKeywords = []

function indexThumbnail (el) {
  const $thumb = $(el)
  // TODO remove old keywords, maybe just set the class
  $('.keyword', el).each((idx, keyword) => {
    $thumb.addClass(`keyword-${crc32(keyword.innerHTML)}`)
  })
}

function indexKeywords () {
  $('.thumb').toArray().forEach(indexThumbnail)
}

function updateKeywords () {
  allKeywords = getKeywords()

  const $ul = $('<ul/>').on('click', 'li', function () {
    const $li = $(this)
    $li.siblings('.active').removeClass('active')
    if ($li.hasClass('active')) {
      $li.removeClass('active')
      $('.thumb.thumb-hide').removeClass('thumb-hide')
    } else {
      $li.addClass('active')
      $(`.thumb.keyword-${$(this).attr('data-crc')}`).removeClass('thumb-hide')
      $(`.thumb:not(.keyword-${$(this).attr('data-crc')})`).addClass('thumb-hide')
    }
  })
  allKeywords.forEach((x) => $(`<li class="keyword" data-crc=${crc32(x)}>${x}</li>`).appendTo($ul))
  if (allKeywords.length) {
    $('.nav-keywords').empty().append($ul)
  }
}

// FIXME this causes the browser to freeze because there are so many elements
$('form.thumb').one('click', (evt) => {
  const $elem = $(evt.currentTarget)
  $elem.find('select').select2({
    data: allKeywords,
    tags: true
  })
  // User intended to edit keywords, so focus() on it
  if (evt.target.tagName === 'SELECT') {
    $elem.find('input.select2-search__field').focus()
  }
})

$('form').on('submit', function (evt) {
  evt.preventDefault()

  const $form = $(this)
  $.post($form.attr('action'), $form.serialize())
  .done(function (data) {
    const $button = $form.find('button')
    $button.text('saved!').addClass('success')
    setTimeout(() => {
      $button.text('save').removeClass('success')
    }, 2000)

    // Update 'src' if user renamed file
    $form.find('input[name=src]').val(data.src)

    // Update keyword datastore
    updateKeywords()
  })
  .fail(function (xhr, textStatus, message) {
    window.alert(message)
  })
})

indexKeywords()
updateKeywords()
