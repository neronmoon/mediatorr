from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from mediatorr.utils.string import sizeof_fmt, time_fmt
from mediatorr.models.torrent import *
import json

TORRENT_STATE_EMOJI = {
    TORRENT_STATE_UNKNOWN: '👽',
    TORRENT_STATE_ERROR: '🚫',
    TORRENT_STATE_PAUSE: '⏸️',
    TORRENT_STATE_CHECKING: '🤔',
    TORRENT_STATE_DOWNLOADING: '🔄',
    TORRENT_STATE_OK: '✅',
}


def detail_view(torrent_dto):
    row = []
    model_id = torrent_dto.get('search_id')
    if torrent_dto.get('state') == TORRENT_STATE_DOWNLOADING:
        row.append(InlineKeyboardButton('Pause', callback_data=json.dumps({'path': '/pause%s' % model_id})))
    if torrent_dto.get('state') == TORRENT_STATE_PAUSE:
        row.append(InlineKeyboardButton('Resume', callback_data=json.dumps({'path': '/resume%s' % model_id})))
    markup = InlineKeyboardMarkup()
    markup.row(*row)
    markup.row(InlineKeyboardButton('Delete', callback_data=json.dumps({'path': '/delete%s' % model_id})))
    return {
        'text': status_line(torrent_dto, links=False, details=False),
        'reply_markup': markup
    }


def list_view(torrent_dto):
    torrent_dto.sort(key=lambda x: x.get('state'))
    row = []
    if any([x for x in torrent_dto if x.get('state') == TORRENT_STATE_DOWNLOADING]):
        row.append(InlineKeyboardButton('Pause All', callback_data=json.dumps({'path': '/pauseall'})))

    if any([x for x in torrent_dto if x.get('state') == TORRENT_STATE_PAUSE]):
        row.append(InlineKeyboardButton('Resume All', callback_data=json.dumps({'path': '/startall'})))

    markup = InlineKeyboardMarkup()
    markup.row(*row)

    return {
        'text': '\n\n'.join(list(map(status_line, torrent_dto))),
        'reply_markup': markup
    }


def status_line(torrent_dto, links=True, details=True, progress=True):
    model_id = torrent_dto.get('search_id')
    chunks = [
        TORRENT_STATE_EMOJI[torrent_dto.get('state')]
    ]
    if progress and torrent_dto.get('progress') != 1:
        chunks.append("<b>{:.0%}</b>".format(torrent_dto.get('progress')))
    search_model = torrent_dto.search_model()
    chunks.append(search_model.title if search_model is not None else torrent_dto.get('title'))
    if progress and torrent_dto.get('state') == TORRENT_STATE_DOWNLOADING:
        chunks.append("<b>| %s |</b>" % sizeof_fmt(torrent_dto.get('speed'), 'B/s'))
        chunks.append(time_fmt(torrent_dto.get('eta')))
    if links and model_id:
        if details:
            chunks.append("\n/details%s " % model_id)
        if torrent_dto.get('state') in [TORRENT_STATE_DOWNLOADING, TORRENT_STATE_CHECKING]:
            chunks.append("/pause%s " % model_id)
        elif torrent_dto.get('state') not in [TORRENT_STATE_OK, TORRENT_STATE_ERROR, TORRENT_STATE_UNKNOWN]:
            chunks.append("/resume%s " % model_id)
        chunks.append("/delete%s" % model_id)

    return " ".join(chunks)
