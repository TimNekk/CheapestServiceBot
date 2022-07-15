import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InputFile, MediaGroup, InputMedia, InputMediaPhoto
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, BotKicked, UserDeactivated, BadRequest, MessageToEditNotFound, MessageCantBeEdited, \
    MessageNotModified


@dataclass
class User:
    id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    _banned: bool
    paid: int
    join_datetime: datetime

    def __post_init__(self):
        self._banned = self._banned == 1
        self.join_datetime = datetime.strptime(self.join_datetime, '%Y-%m-%d %H:%M:%S')

    async def _check_ban(self):
        from loader import dp

        try:
            await dp.bot.send_chat_action(self.id, 'typing')
        except (BotBlocked, ChatNotFound):
            self.ban()
        except (UserDeactivated, BotKicked):
            self.ban()
            self.delete()

    @property
    async def link(self):
        from loader import dp

        user = await dp.bot.get_chat(self.id)
        if user.username:
            return f"@{user.username}"
        elif user.full_name:
            return f'<a href="{(await dp.bot.get_chat(self.id)).user_url}">{user.full_name}</a>'
        else:
            return ''

    def ban(self) -> None:
        self._banned = True
        self._update('ban', 1)

    def unban(self) -> None:
        self._banned = False
        self._update('ban', 0)

    @property
    async def banned(self) -> bool:
        if not self._banned:
            await self._check_ban()
        return self._banned

    # Adding

    def add_paid(self, amount: int) -> None:
        self.paid += amount
        self._update('paid', self.paid)

    # Sending

    async def send_message(self, text: str,
                           reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
                           reply_to_message_id: Union[None, int, str] = None,
                           disable_web_page_preview: Optional[int] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.send_message(chat_id=self.id,
                                                 text=text,
                                                 reply_to_message_id=reply_to_message_id,
                                                 reply_markup=reply_markup,
                                                 allow_sending_without_reply=True,
                                                 disable_web_page_preview=disable_web_page_preview)
            except BadRequest as err:
                logging.error(err)

    async def send_image(self, image: Union[InputFile, str],
                         caption: Optional[str] = None,
                         reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
                         reply_to_message_id: Optional[int] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.send_photo(chat_id=self.id,
                                               photo=image,
                                               caption=caption,
                                               reply_to_message_id=reply_to_message_id,
                                               reply_markup=reply_markup,
                                               allow_sending_without_reply=True)
            except BadRequest as err:
                logging.error(err)

    async def send_video(self, video: Union[InputFile, str],
                         caption: Optional[str] = None,
                         reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
                         reply_to_message_id: Optional[int] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.send_video(chat_id=self.id,
                                               video=video,
                                               caption=caption,
                                               reply_to_message_id=reply_to_message_id,
                                               reply_markup=reply_markup,
                                               allow_sending_without_reply=True)
            except BadRequest as err:
                logging.error(err)

    async def send_media_group(self, media: Union[MediaGroup, list],
                               reply_to_message_id: Optional[int] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.send_media_group(chat_id=self.id,
                                                     media=media,
                                                     reply_to_message_id=reply_to_message_id,
                                                     allow_sending_without_reply=True)
            except BadRequest as err:
                logging.error(err)

    async def send_chat_action(self, action: str):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.send_chat_action(chat_id=self.id,
                                                     action=action)
            except BadRequest as err:
                logging.error(err)

    async def edit_message_text(self, message_id: Union[str, int],
                                text: str,
                                reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
                                disable_web_page_preview: Optional[int] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.edit_message_text(chat_id=self.id,
                                                      message_id=message_id,
                                                      text=text,
                                                      reply_markup=reply_markup,
                                                      disable_web_page_preview=disable_web_page_preview)
            except (MessageToEditNotFound, MessageCantBeEdited):
                return await self.send_message(text=text,
                                               reply_markup=reply_markup,
                                               disable_web_page_preview=disable_web_page_preview)
            except MessageNotModified:
                pass
            except BadRequest as err:
                logging.error(err)

    async def edit_message_caption(self, message_id: Union[str, int],
                                   caption: str,
                                   reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.edit_message_caption(chat_id=self.id,
                                                         message_id=message_id,
                                                         caption=caption,
                                                         reply_markup=reply_markup)
            except (MessageToEditNotFound, MessageCantBeEdited):
                return await self.send_message(text=caption,
                                               reply_markup=reply_markup)
            except MessageNotModified:
                pass
            except BadRequest as err:
                logging.error(err)

    async def edit_message_media(self, message_id: Union[str, int],
                                 media: Union[InputMedia, InputMediaPhoto],
                                 reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.edit_message_media(media=media,
                                                       chat_id=self.id,
                                                       message_id=message_id,
                                                       reply_markup=reply_markup)
            except (MessageToEditNotFound, MessageCantBeEdited):
                return await self.send_image(image=media.media,
                                             reply_markup=reply_markup)
            except MessageNotModified:
                pass
            except BadRequest as err:
                logging.error(err)

    async def edit_message_reply_markup(self, message_id: Union[str, int],
                                        reply_markup: Union[None, InlineKeyboardMarkup, ReplyKeyboardMarkup] = None):
        from loader import dp

        if not await self.banned:
            try:
                return await dp.bot.edit_message_reply_markup(chat_id=self.id,
                                                              message_id=message_id,
                                                              reply_markup=reply_markup)
            except (MessageToEditNotFound, MessageCantBeEdited, MessageNotModified):
                pass
            except BadRequest as err:
                logging.error(err)

    def delete(self) -> None:
        from loader import db

        sql = "DELETE FROM Users WHERE id = ?"
        db.execute(sql, parameters=(self.id,), commit=True)

    def _update(self, parameter, value) -> None:
        from loader import db

        sql = f"UPDATE Users SET {parameter} = ? WHERE id = ?"
        db.execute(sql, parameters=(value, self.id), commit=True)
