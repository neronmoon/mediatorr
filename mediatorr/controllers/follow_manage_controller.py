import inject

from mediatorr.controllers.search_torrent_controller import SearchTorrentController
from mediatorr.models.following import FollowSearch

from mediatorr.controllers.controller import Controller
from mediatorr.models.search import SearchQuery
from mediatorr.views.follow import follow_list


class FollowManageController(Controller):
    patterns = [
        r"^/(?P<mode>following$)",
        r'^/(?P<follow_state>(un)?follow)(?P<query_id>\d+)_(?P<mode>follow_list)$',
        r'^/(?P<follow_state>(un)?follow)(?P<query_id>\d+)_(?P<mode>search_list)_(?P<page>.*)$'
    ]
    search_service = inject.attr('search_service')

    def __init__(self, params):
        super().__init__(params)
        self.mode = params.get('mode')

    def handle(self, message, **kwargs):
        if self.mode == 'following':
            follows = FollowSearch.select().where(FollowSearch.chat_id == message.chat.id)
            self.update_message(**follow_list(follows))
            return

        query_model = SearchQuery.get_by_id(self.params.get('query_id'))
        self.__handle_following_callback(query_model, message)
        if self.mode == 'follow_list':
            follows = FollowSearch.select().where(FollowSearch.chat_id == message.chat.id)
            self.update_message(**follow_list(follows))
        elif self.mode == 'search_list':
            search_controller = SearchTorrentController(self.params)
            search_controller.run(kwargs.get('is_callback'), message)

    def __handle_following_callback(self, query_model, message):
        params = {'query_id': query_model.id, 'chat_id': message.chat.id}
        task = FollowSearch.get_or_none(**params)
        should_follow = self.params.get('follow_state') == 'follow'
        if should_follow and task is None:
            FollowSearch(**params).save()
        elif not should_follow and task is not None:
            task.delete_instance()
        self.flash_message(
            text="👍 You're now following `%s` query!" % query_model.query if should_follow else "😴 Unfollowed!",
            chat_id=message.chat.id
        )
