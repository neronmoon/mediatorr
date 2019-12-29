from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from mediatorr.utils.string import sizeof_fmt, time_fmt
from mediatorr.models.torrent import *
import json
import PTN

TORRENT_STATE_EMOJI = {
    TORRENT_STATE_UNKNOWN: '👽',
    TORRENT_STATE_ERROR: '🚫',
    TORRENT_STATE_PAUSE: '⏸️',
    TORRENT_STATE_CHECKING: '🤔',
    TORRENT_STATE_DOWNLOADING: '🔄',
    TORRENT_STATE_OK: '✅',
}


def detail_view(model):
    row = []
    if model.get('state') == TORRENT_STATE_DOWNLOADING:
        row.append(InlineKeyboardButton('Pause', callback_data=json.dumps({'path': '/pause%s' % model.doc_id})))
    if model.get('state') == TORRENT_STATE_PAUSE:
        row.append(InlineKeyboardButton('Resume', callback_data=json.dumps({'path': '/resume%s' % model.doc_id})))
    row.append(InlineKeyboardButton('Follow', callback_data=json.dumps({'path': '/follow%s' % model.doc_id})))
    markup = InlineKeyboardMarkup()
    markup.row(*row)
    markup.row(InlineKeyboardButton('Delete', callback_data=json.dumps({'path': '/delete%s' % model.doc_id})))
    return {
        'text': status_line(model, details=False),
        'reply_markup': markup
    }


def list_view(models):
    models.sort(key=lambda x: x.get('state'))
    row = []
    if any([x for x in models if x.get('state') == TORRENT_STATE_DOWNLOADING]):
        row.append(InlineKeyboardButton('Pause All', callback_data=json.dumps({'path': '/pauseall'})))

    if any([x for x in models if x.get('state') == TORRENT_STATE_PAUSE]):
        row.append(InlineKeyboardButton('Resume All', callback_data=json.dumps({'path': '/startall'})))

    markup = InlineKeyboardMarkup()
    markup.row(*row)

    return {
        'text': '\n\n'.join((list(map(status_line, models)))),
        'reply_markup': markup
    }


def status_line(model, links=True, details=True, progress=True):
    chunks = [
        TORRENT_STATE_EMOJI[model.get('state')]
    ]
    if progress and model.get('progress') != 1:
        chunks.append("<b>{:.0%}</b>".format(model.get('progress')))
    search_model = model.search_model()
    chunks.append(search_model.get('name') if search_model is not None else model.get('name'))
    if progress and model.get('state') == TORRENT_STATE_DOWNLOADING:
        chunks.append("<b>| %s |</b>" % sizeof_fmt(model.get('speed'), 'B/s'))
        chunks.append(time_fmt(model.get('eta')))
    if links:
        if details:
            chunks.append("\n/details%s " % model.doc_id)
        if model.get('state') in [TORRENT_STATE_DOWNLOADING, TORRENT_STATE_CHECKING]:
            chunks.append("/pause%s " % model.doc_id)
        elif model.get('state') not in [TORRENT_STATE_OK, TORRENT_STATE_ERROR, TORRENT_STATE_UNKNOWN]:
            chunks.append("/resume%s " % model.doc_id)
        chunks.append("/delete%s" % model.doc_id)

    return " ".join(chunks)


def search_line(item):
    info = PTN.parse(item.get('name'))
    badges = []
    if 'year' in info:
        badges.append('[%s]' % info['year'])
    if 'resolution' in info:
        badges.append('[%s]' % info['resolution'])
    if 'orig' in item.get('name').lower():
        badges.append('[original]')
    if ' sub' in item.get('name').lower():
        badges.append('[SUBS]')
    badges.append("[%s]" % sizeof_fmt(item.get('size')))
    badges.append("[Seeds: %s]" % (item.get('seeds') + item.get('leech')))

    badges_string = "" if not badges else " <b>%s</b> " % ("".join(badges))
    return '🍿{badges}\n{name}\n/download{link_id}\n'.format(link_id=item.doc_id, badges=badges_string, **item)
